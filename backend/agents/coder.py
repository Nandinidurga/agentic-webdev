"""
coder.py - Parallel full-stack code generator with delimited block parsing.

Architecture:
- Delimited block emission (=== FILE: /path === ... === END FILE ===).
- Concurrent parallel LLM execution for Backend and Frontend pipelines.
- Targeted single-file re-request on parse failure for missing required files.
- Token-budgeted context packing prioritizing highest-scoring RAG chunks.
- Zero JSON escaping or regex heuristic salvaging.
"""

import os
import json
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
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


def generate_backend(plan: str, context: str, api_spec_str: str, formatted_errors: str, llm) -> str:
    """Generates Node.js/Express backend files in delimited format."""
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
    resp = llm.invoke(messages)
    return extract_content(resp)


def generate_frontend(plan: str, context: str, api_spec_str: str, formatted_errors: str, llm) -> str:
    """Generates React client files in delimited format."""
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
    resp = llm.invoke(messages)
    return extract_content(resp)


def re_request_single_file(missing_file: str, role_type: str, plan: str, api_spec_str: str, llm) -> Optional[str]:
    """Targeted re-request when a single required file failed to parse or was omitted."""
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
        resp = llm.invoke([HumanMessage(content=prompt)])
        parsed = parse_delimited_files(extract_content(resp))
        # Check both direct key and normalized key
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
    current_attempt = state.get("attempt", 0) + 1
    print(f"--- CODER AGENT (PARALLEL DUAL GENERATION, ATTEMPT {current_attempt}) ---", flush=True)
    plan = state.get("plan", "")[:1800]

    # Token-budgeted context prioritizing highest-scoring chunks
    max_context_tokens = int(os.getenv("MAX_CONTEXT_TOKENS", "2500"))
    context = build_budgeted_context(state, max_tokens=max_context_tokens)

    raw_errors = state.get("errors", [])
    api_spec = state.get("api_spec", [])

    # Format only structured reviewer errors cleanly for targeted correction
    if isinstance(raw_errors, list) and raw_errors:
        formatted_errors = "\n".join([
            f"- [{err.get('file', 'general')}:{err.get('line', 1)}] ({err.get('rule', 'error')}) {err.get('message', '')}"
            if isinstance(err, dict) else f"- {err}"
            for err in raw_errors
        ])
    elif isinstance(raw_errors, str) and raw_errors.strip():
        formatted_errors = raw_errors.strip()
    else:
        formatted_errors = "None"

    llm = get_llm()
    api_spec_str = json.dumps(api_spec, indent=2) if api_spec else "Derive REST endpoints based on plan."

    # Execute Backend and Frontend code generation concurrently in parallel worker threads
    print("Coder Agent: Launching parallel Backend & Frontend generation calls...", flush=True)
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_backend = executor.submit(
            generate_backend, plan, context, api_spec_str, formatted_errors, llm
        )
        future_frontend = executor.submit(
            generate_frontend, plan, context, api_spec_str, formatted_errors, llm
        )
        backend_output = future_backend.result()
        frontend_output = future_frontend.result()

    # Parse delimited files
    backend_files = parse_delimited_files(backend_output)
    frontend_files = parse_delimited_files(frontend_output)

    # Targeted re-request for any missing required backend files
    for req_file in REQUIRED_BACKEND_FILES:
        if req_file not in backend_files:
            recovered = re_request_single_file(req_file, "Backend", plan, api_spec_str, llm)
            if recovered:
                backend_files[req_file] = recovered

    # Targeted re-request for any missing required frontend files
    for req_file in REQUIRED_FRONTEND_FILES:
        if req_file not in frontend_files:
            recovered = re_request_single_file(req_file, "Frontend", plan, api_spec_str, llm)
            if recovered:
                frontend_files[req_file] = recovered

    # Merge into unified files map
    merged_files = dict(backend_files)
    merged_files.update(frontend_files)

    print(f"Coder Agent successfully produced {len(backend_files)} backend files and {len(frontend_files)} frontend files ({len(merged_files)} total) on attempt {current_attempt}.", flush=True)

    return {
        "code": f"Generated {len(merged_files)} files via parallel delimited blocks.",
        "files": merged_files,
        "backend_files": backend_files,
        "frontend_files": frontend_files,
        "attempt": current_attempt
    }
