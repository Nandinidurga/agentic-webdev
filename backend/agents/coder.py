"""
coder.py - Parallel full-stack code generator with delimited block parsing.

Architecture:
- Delimited block emission (=== FILE: /path === ... === END FILE ===).
- Concurrent parallel LLM execution for Backend and Frontend pipelines.
- Passes previous files into coder on retry and requests ONLY files named in errors.
- Routes/server errors -> backend; all remaining errors -> frontend.
- Dedicated error stream per side (each side only receives its own errors).
- ThreadPoolExecutor with shared timeout and cancellation token (Event) so 504 stops work immediately.
- Per-attempt execution timeout bounded by GENERATION_TIMEOUT (default: 180s).
- Targeted single-file re-request on parse failure for missing required files.
- Token-budgeted context packing prioritizing highest-scoring RAG chunks.
"""

import os
import json
import re
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional, Set
from langchain_core.messages import SystemMessage, HumanMessage
from llm_factory import get_llm
from file_parser import parse_delimited_files


REQUIRED_BACKEND_FILES = ["/server.js", "/server/package.json"]
REQUIRED_FRONTEND_FILES = ["/App.js", "/services/api.js", "/package.json", "/styles.css"]


def estimate_tokens(text: str) -> int:
    """Fast conservative heuristic: ~4 characters per token."""
    return max(1, len(text) // 4)


def build_budgeted_context(state: dict, max_tokens: int) -> str:
    """
    Budgets technical context by tokens and prioritizes the highest-scoring chunks.
    Replaces blind character truncation with score-ranked packing.
    """
    rag_chunks = state.get("rag_chunks", [])
    if rag_chunks and isinstance(rag_chunks, list):
        sorted_chunks = sorted(rag_chunks, key=lambda c: c.get("score", 0.0), reverse=True)
        packed_snippets = []
        allocated_tokens = 0

        for chunk in sorted_chunks:
            domain = str(chunk.get("domain", "doc")).upper()
            source = str(chunk.get("source", "reference"))
            score = chunk.get("score", 0.0)
            content = str(chunk.get("content", "")).strip()

            snippet = f"[{domain} - {source} (relevance: {score})]:\n{content}"
            chunk_tokens = estimate_tokens(snippet)

            if allocated_tokens + chunk_tokens <= max_tokens:
                packed_snippets.append(snippet)
                allocated_tokens += chunk_tokens
            else:
                remaining_tokens = max_tokens - allocated_tokens
                if remaining_tokens > 40:
                    truncated_content = content[: remaining_tokens * 4]
                    packed_snippets.append(f"[{domain} - {source} (relevance: {score})]:\n{truncated_content}...")
                    allocated_tokens += remaining_tokens
                break

        if packed_snippets:
            return "\n\n---\n\n".join(packed_snippets)

    raw_context = state.get("context", "")
    if not raw_context:
        return "Rely on standard Node.js/Express and React production patterns."

    max_chars = max_tokens * 4
    if len(raw_context) <= max_chars:
        return raw_context
    return raw_context[:max_chars] + "\n...[Context budgeted to token ceiling]"


def extract_content(response) -> str:
    """Extracts raw text from LangChain message or reasoning channel."""
    raw = response.content
    if isinstance(raw, list):
        raw = "\n".join([c if isinstance(c, str) else c.get("text", str(c)) for c in raw])
    text = str(raw).strip()
    if (not text or "=== FILE:" not in text) and hasattr(response, 'additional_kwargs'):
        reasoning = response.additional_kwargs.get('reasoning_content', '')
        if "=== FILE:" in reasoning:
            return reasoning.strip()
    return text


def is_backend_error(err: Any) -> bool:
    """
    Categorizes errors:
    Route contract and server errors -> backend.
    All remaining errors -> frontend.
    """
    if isinstance(err, dict):
        file = str(err.get("file", "")).lower()
        rule = str(err.get("rule", "")).lower()
        msg = str(err.get("message", "")).lower()

        if rule == "route-contract":
            return True
        if "/server" in file or file.endswith("server.js") or "server" in file:
            return True
        if "server" in msg or "route" in msg or "endpoint" in msg:
            return True
        return False

    err_str = str(err).lower()
    return "route" in err_str or "server" in err_str or "backend" in err_str


def extract_files_from_errors(errors: List[Any], default_files: List[str]) -> List[str]:
    """Extracts specific file paths explicitly named in structured errors."""
    named_files: Set[str] = set()
    for err in errors:
        if isinstance(err, dict):
            f = str(err.get("file", "")).strip()
            if f and f != "general":
                norm = f if f.startswith("/") else f"/{f}"
                named_files.add(norm)
            elif err.get("rule") == "route-contract":
                named_files.add("/server.js")
    if not named_files:
        return list(default_files)
    return sorted(list(named_files))


def format_structured_errors(errors: List[Any]) -> str:
    """Formats structured error objects for LLM prompt injection."""
    if not errors:
        return "None"
    lines = []
    for err in errors:
        if isinstance(err, dict):
            lines.append(f"- [{err.get('file', 'general')}:{err.get('line', 1)}] ({err.get('rule', 'error')}) {err.get('message', '')}")
        else:
            lines.append(f"- {err}")
    return "\n".join(lines)


def generate_backend(
    plan: str,
    context: str,
    api_spec_str: str,
    formatted_errors: str,
    llm,
    requested_files: Optional[List[str]] = None,
    previous_files: Optional[Dict[str, str]] = None,
    cancel_event: Optional[Any] = None
) -> str:
    """Generates Node.js/Express backend files in delimited format."""
    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Backend generation aborted: shared cancel flag active.")

    if requested_files and previous_files:
        files_str = ", ".join(requested_files)
        prev_blocks = []
        for f in requested_files:
            if f in previous_files:
                prev_blocks.append(f"=== CURRENT FILE: {f} ===\n{previous_files[f]}\n=== END CURRENT FILE ===")
        prev_context = "\n\n".join(prev_blocks) if prev_blocks else "No previous file content available."

        system_prompt = f"""You are the Lead Backend Engineer Agent.
Your task is to update specific backend files to resolve reviewer errors while keeping all existing functionality.

Key Technical Context:
{context}

PREVIOUS CODE TO UPDATE:
{prev_context}

CRITICAL RULES:
1. Emit ONLY the requested files: {files_str}.
2. Fix all reported backend errors.
3. Emit each file inside delimited blocks without markdown commentary:
=== FILE: /path ===
<complete fixed code>
=== END FILE ==="""

        prompt = f"""Target API Specification:\n{api_spec_str}\n\nReviewer Errors to Resolve (Backend Only):\n{formatted_errors}\n\nRequested Files to Update: {files_str}\n\nEmit ONLY the requested files now in delimited blocks:"""
    else:
        system_prompt = f"""You are the Lead Backend Engineer Agent.
Generate the complete Node.js / Express.js Backend for the web application based on the architectural plan and API specification.

Key Technical Context:
{context}

REQUIRED BACKEND FILES:
1. `/server.js`: Complete Node.js / Express.js server.
   * MUST require 'express' and 'cors', and use `app.use(cors())` and `app.use(express.json())`.
   * MUST define in-memory storage array/object initialized with 3-5 rich, domain-specific seed items.
   * MUST implement all REST endpoints from the API specification (GET all, GET by id, POST create, PUT/PATCH update, DELETE).
   * MUST include `GET /api/health` returning `{{ status: "ok", uptime: process.uptime() }}`.
   * MUST start the server: `const PORT = process.env.PORT || 5000; app.listen(PORT, () => console.log('Server running on port ' + PORT));`.
2. `/server/package.json`: Valid JSON package descriptor with "dependencies": {{ "express": "^4.19.2", "cors": "^2.8.5" }} and "scripts": {{ "start": "node server.js" }}.
3. `/README.md`: Quickstart instructions on running backend (`cd server && npm install && npm start`).

CRITICAL FORMAT RULES:
Emit each file inside delimited blocks without markdown commentary:
=== FILE: /server.js ===
<complete unescaped server code>
=== END FILE ===

=== FILE: /server/package.json ===
<valid package.json with double quotes>
=== END FILE ===

=== FILE: /README.md ===
<readme documentation>
=== END FILE ==="""

        prompt = f"""Plan & Requirements:\n{plan}\n\nTarget API Specification:\n{api_spec_str}\n\nPrevious Reviewer Errors to Resolve:\n{formatted_errors}\n\nEmit all backend files now in delimited blocks:"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]

    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Backend generation aborted before LLM invoke: shared cancel flag active.")

    resp = llm.invoke(messages)

    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Backend generation aborted after LLM invoke: shared cancel flag active.")

    return extract_content(resp)


def generate_frontend(
    plan: str,
    context: str,
    api_spec_str: str,
    formatted_errors: str,
    llm,
    requested_files: Optional[List[str]] = None,
    previous_files: Optional[Dict[str, str]] = None,
    cancel_event: Optional[Any] = None
) -> str:
    """Generates React client files in delimited format."""
    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Frontend generation aborted: shared cancel flag active.")

    if requested_files and previous_files:
        files_str = ", ".join(requested_files)
        prev_blocks = []
        for f in requested_files:
            if f in previous_files:
                prev_blocks.append(f"=== CURRENT FILE: {f} ===\n{previous_files[f]}\n=== END CURRENT FILE ===")
        prev_context = "\n\n".join(prev_blocks) if prev_blocks else "No previous file content available."

        system_prompt = f"""You are the Lead Frontend Engineer Agent.
Your task is to update specific frontend files to resolve reviewer errors while keeping all existing functionality.

Key Technical Context:
{context}

PREVIOUS CODE TO UPDATE:
{prev_context}

CRITICAL RULES:
1. Emit ONLY the requested files: {files_str}.
2. Fix all reported frontend errors.
3. Emit each file inside delimited blocks without markdown commentary:
=== FILE: /path ===
<complete fixed code>
=== END FILE ==="""

        prompt = f"""Target API Specification:\n{api_spec_str}\n\nReviewer Errors to Resolve (Frontend Only):\n{formatted_errors}\n\nRequested Files to Update: {files_str}\n\nEmit ONLY the requested files now in delimited blocks:"""
    else:
        system_prompt = f"""You are the Lead Frontend Engineer Agent.
Generate the complete React Frontend UI for the web application based on the architectural plan and API specification.

Key Technical Context:
{context}

REQUIRED FRONTEND FILES:
1. `/services/api.js`: The central API client module.
   * Export an `api` object or async helper functions for every endpoint.
   * Maintain an in-memory mock store with seed items. Attempt `fetch('http://localhost:5000' + endpoint)`. If fetch fails, catch the error and ALWAYS return mock data. NEVER return undefined!
2. `/App.js`: Complete React application component.
   * MUST be named `/App.js`. MUST import `./styles.css` and `./services/api.js`.
   * Initialize collections defensively: `const [items, setItems] = useState([]);`.
   * Defensive rendering: `(items || []).map(...)`. Format numbers safely: `(Number(item.amount) || 0).toFixed(2)`.
   * Rich interactive UI with filters, search, creation forms, data cards, and live API status badge.
3. `/styles.css`: Modern styling with smooth transitions, cards, and buttons.
4. `/package.json`: Client package.json specifying dependencies: {{ "dependencies": {{ "lucide-react": "latest" }} }}.

CRITICAL FORMAT RULES:
Emit each file inside delimited blocks without markdown commentary:
=== FILE: /services/api.js ===
<complete unescaped api client code>
=== END FILE ===

=== FILE: /App.js ===
<complete unescaped React App code>
=== END FILE ===

=== FILE: /styles.css ===
<complete styles>
=== END FILE ===

=== FILE: /package.json ===
<valid package.json with double quotes>
=== END FILE ==="""

        prompt = f"""Plan & Requirements:\n{plan}\n\nTarget API Specification:\n{api_spec_str}\n\nPrevious Reviewer Errors to Resolve:\n{formatted_errors}\n\nEmit all frontend files now in delimited blocks:"""

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=prompt)]

    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Frontend generation aborted before LLM invoke: shared cancel flag active.")

    resp = llm.invoke(messages)

    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Frontend generation aborted after LLM invoke: shared cancel flag active.")

    return extract_content(resp)


def re_request_single_file(
    missing_file: str,
    role_type: str,
    plan: str,
    api_spec_str: str,
    llm,
    cancel_event: Optional[Any] = None
) -> Optional[str]:
    """Targeted re-request when a single required file failed to parse or was omitted."""
    if cancel_event and cancel_event.is_set():
        return None

    print(f"Coder Agent: Re-requesting missing required file '{missing_file}' ({role_type})...", flush=True)
    prompt = f"""You are the {role_type} Engineer Agent.
The required file '{missing_file}' was omitted or failed to parse in your previous output.
Generate ONLY the file '{missing_file}' right now in the exact delimited format:

=== FILE: {missing_file} ===
<complete unescaped code>
=== END FILE ===

Plan Reference:
{plan[:1000]}
API Spec Reference:
{api_spec_str}
"""
    try:
        if cancel_event and cancel_event.is_set():
            return None
        resp = llm.invoke([HumanMessage(content=prompt)])
        if cancel_event and cancel_event.is_set():
            return None
        parsed = parse_delimited_files(extract_content(resp))
        norm_key = missing_file if missing_file.startswith('/') else f"/{missing_file}"
        if norm_key in parsed:
            return parsed[norm_key]
        for k, v in parsed.items():
            if k.lower().endswith(missing_file.lower().lstrip('/')):
                return v
    except Exception as err:
        print(f"Failed to recover file {missing_file}: {err}", flush=True)
    return None


def coder_node(state: Dict[str, Any]) -> Dict[str, Any]:
    cancel_event = state.get("cancel_event")
    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Coder execution aborted: shared cancel flag is active.")

    current_attempt = state.get("attempt", 0) + 1
    attempt_timeout = float(os.getenv("GENERATION_TIMEOUT", "180"))
    print(f"--- CODER AGENT (PARALLEL DUAL GENERATION, ATTEMPT {current_attempt}, TIMEOUT {attempt_timeout}s) ---", flush=True)
    plan = state.get("plan", "")[:1800]

    max_context_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", "2500"))
    context = build_budgeted_context(state, max_tokens=max_context_tokens)

    raw_errors = state.get("errors", [])
    api_spec = state.get("api_spec", [])
    api_spec_str = json.dumps(api_spec, indent=2) if api_spec else "Derive REST endpoints based on plan."

    # Previous files from prior attempts
    prev_files = dict(state.get("files") or {})
    prev_backend_files = dict(state.get("backend_files") or {})
    prev_frontend_files = dict(state.get("frontend_files") or {})

    if not prev_backend_files and prev_files:
        prev_backend_files = {k: v for k, v in prev_files.items() if "server" in k or k == "/server.js"}
    if not prev_frontend_files and prev_files:
        prev_frontend_files = {k: v for k, v in prev_files.items() if "server" not in k and k != "/server.js"}

    is_retry = bool(prev_files) and bool(raw_errors) and current_attempt > 1
    llm = get_llm()

    if is_retry:
        backend_errors = [e for e in raw_errors if is_backend_error(e)]
        frontend_errors = [e for e in raw_errors if not is_backend_error(e)]

        backend_req_files = extract_files_from_errors(backend_errors, REQUIRED_BACKEND_FILES) if backend_errors else []
        frontend_req_files = extract_files_from_errors(frontend_errors, REQUIRED_FRONTEND_FILES) if frontend_errors else []

        run_backend = bool(backend_req_files)
        run_frontend = bool(frontend_req_files)

        fmt_backend_errors = format_structured_errors(backend_errors)
        fmt_frontend_errors = format_structured_errors(frontend_errors)
    else:
        run_backend = True
        run_frontend = True
        backend_req_files = list(REQUIRED_BACKEND_FILES)
        frontend_req_files = list(REQUIRED_FRONTEND_FILES)
        fmt_backend_errors = "None"
        fmt_frontend_errors = "None"

    backend_output = ""
    frontend_output = ""

    executor = ThreadPoolExecutor(max_workers=2)
    futures = {}
    try:
        if run_backend:
            print(f"Coder: Launching Backend thread (requesting: {backend_req_files})...", flush=True)
            futures["backend"] = executor.submit(
                generate_backend,
                plan,
                context,
                api_spec_str,
                fmt_backend_errors,
                llm,
                backend_req_files if is_retry else None,
                prev_backend_files if is_retry else None,
                cancel_event
            )
        if run_frontend:
            print(f"Coder: Launching Frontend thread (requesting: {frontend_req_files})...", flush=True)
            futures["frontend"] = executor.submit(
                generate_frontend,
                plan,
                context,
                api_spec_str,
                fmt_frontend_errors,
                llm,
                frontend_req_files if is_retry else None,
                prev_frontend_files if is_retry else None,
                cancel_event
            )

        if futures:
            done, not_done = concurrent.futures.wait(
                futures.values(),
                timeout=attempt_timeout,
                return_when=concurrent.futures.ALL_COMPLETED
            )

            if not_done or (cancel_event and cancel_event.is_set()):
                if cancel_event:
                    cancel_event.set()
                for f in not_done:
                    f.cancel()
                raise TimeoutError(f"Coder attempt {current_attempt} timed out after {attempt_timeout}s per-attempt budget.")

            if "backend" in futures:
                backend_output = futures["backend"].result()
            if "frontend" in futures:
                frontend_output = futures["frontend"].result()
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

    new_backend_files = parse_delimited_files(backend_output) if backend_output else {}
    new_frontend_files = parse_delimited_files(frontend_output) if frontend_output else {}

    # Targeted re-request for any missing requested files
    target_backend_req = backend_req_files if is_retry else REQUIRED_BACKEND_FILES
    for req_file in target_backend_req:
        if req_file not in new_backend_files and req_file not in prev_backend_files:
            if cancel_event and cancel_event.is_set():
                break
            recovered = re_request_single_file(req_file, "Backend", plan, api_spec_str, llm, cancel_event=cancel_event)
            if recovered:
                new_backend_files[req_file] = recovered

    target_frontend_req = frontend_req_files if is_retry else REQUIRED_FRONTEND_FILES
    for req_file in target_frontend_req:
        if req_file not in new_frontend_files and req_file not in prev_frontend_files:
            if cancel_event and cancel_event.is_set():
                break
            recovered = re_request_single_file(req_file, "Frontend", plan, api_spec_str, llm, cancel_event=cancel_event)
            if recovered:
                new_frontend_files[req_file] = recovered

    # Merge with previous files: preserve unmodified files intact
    final_backend_files = dict(prev_backend_files)
    final_backend_files.update(new_backend_files)

    final_frontend_files = dict(prev_frontend_files)
    final_frontend_files.update(new_frontend_files)

    merged_files = dict(prev_files)
    merged_files.update(final_backend_files)
    merged_files.update(final_frontend_files)

    print(
        f"Coder Agent produced {len(new_backend_files)} new backend, {len(new_frontend_files)} new frontend "
        f"({len(merged_files)} total active files) on attempt {current_attempt}.",
        flush=True
    )

    return {
        "code": f"Generated {len(merged_files)} files via parallel delimited blocks.",
        "files": merged_files,
        "backend_files": final_backend_files,
        "frontend_files": final_frontend_files,
        "attempt": current_attempt,
        "cancel_event": cancel_event
    }
