import os
import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from llm_factory import get_llm

def unescape_json_string(s: str) -> str:
    """Helper to unescape escaped JSON string content recovered via regex."""
    replacements = [
        ('\\\\', '\\'),
        ('\\"', '"'),
        ('\\n', '\n'),
        ('\\r', '\r'),
        ('\\t', '\t'),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s

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
        # Sort chunks strictly by relevance score descending
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

    # Fallback if raw context string was provided without structured chunks
    raw_context = state.get("context", "")
    if not raw_context:
        return "Rely on standard Node.js/Express and React production patterns."

    max_chars = max_tokens * 4
    if len(raw_context) <= max_chars:
        return raw_context
    return raw_context[:max_chars] + "\n...[Context budgeted to token ceiling]"

def coder_node(state):
    current_attempt = state.get("attempt", 0) + 1
    print(f"--- CODER AGENT (FULL-STACK, ATTEMPT {current_attempt}) ---")
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
    
    system_prompt = f"""You are the Principal Full-Stack Engineer Agent.
Your job is to generate BOTH the complete Backend code and the complete Frontend code for the web application based on the architectural plan and API specification.

Key Technical Context:
{context}

REQUIRED FILE STRUCTURE (Output a single, strictly valid JSON object where keys are file paths and values are complete code strings. Keep implementations compact, elegant, and concise so the JSON closes cleanly):

1. BACKEND FILES:
   - `/server.js`: Complete Node.js / Express.js server.
     * MUST require 'express' and 'cors', and use `app.use(cors())` and `app.use(express.json())`.
     * MUST define in-memory storage array/object initialized with 3-5 rich, domain-specific seed items.
     * MUST implement all REST endpoints from the API specification (GET all, GET by id, POST create, PUT/PATCH update, DELETE).
     * MUST include `GET /api/health` returning `{{ status: "ok", uptime: process.uptime() }}`.
     * MUST start the server: `const PORT = process.env.PORT || 5000; app.listen(PORT, () => console.log('Server running on port ' + PORT));`.
   - `/server/package.json`: Valid JSON package descriptor with "dependencies": {{ "express": "^4.19.2", "cors": "^2.8.5" }} and "scripts": {{ "start": "node server.js" }}.

2. FRONTEND SERVICES:
   - `/services/api.js`: The central API client module used by React components.
     * Export an `api` object or async helper functions for every endpoint (e.g. `getItems()`, `createItem()`, `updateItem()`, `deleteItem()`).
     * CRITICAL DUAL-MODE LOGIC: Maintain a top-level in-memory mock store initialized with the domain seed items (e.g. `let mockItems = [...seedData];`). In every async function, attempt `fetch('http://localhost:5000' + endpoint)`. If fetch fails (or `!res.ok`), catch the error and ALWAYS RETURN the mock data (e.g. `return [...mockItems];`). NEVER return undefined from any API function!
     * This guarantees the frontend is 100% interactive inside the live Sandpack browser preview, while simultaneously providing true production backend connectivity!

3. FRONTEND UI (SANDPACK COMPATIBLE):
   - `/App.js`: Complete, rich React application component.
     * MUST be named `/App.js` (not .jsx or .tsx).
     * MUST import `./styles.css` and `./services/api.js`.
     * CRITICAL REACT IMMUNITY RULES:
       - ALWAYS initialize collection state with an empty array: `const [items, setItems] = useState([]);` (NEVER `useState()`, `useState(null)`, or `useState(undefined)`).
       - ALWAYS render collections defensively: `(items || []).map(...)` and `(items || []).filter(...)`.
       - ALWAYS format numbers defensively: `(Number(item.amount) || 0).toFixed(2)` so null, undefined, or string values never crash.
     * Build a rich interactive UI with search/filter, item creation/editing forms, data cards/tables, and action buttons.
     * Display live feedback: badge showing "Backend API Connected" or "Preview Store Active", loading spinners, and alerts.
   - `/styles.css`: Modern CSS styling with smooth transitions, modern colors, card styles, and button effects.
   - `/package.json`: Client package.json specifying dependencies: {{ "dependencies": {{ "lucide-react": "latest" }} }}.

4. DOCUMENTATION:
   - `/README.md`: Quickstart instructions on running backend (`cd server && npm install && npm start`) and frontend (`npm install && npm start`).

RULES:
- Output strictly valid, parsable JSON ONLY.
- Keys MUST be file paths starting with `/`.
- DO NOT wrap the output in markdown code blocks like ```json ... ```. Output raw JSON starting with `{{` and ending with `}}`.
- Do NOT generate HTML files or Vite config files."""

    prompt = f"""Plan & Requirements:\n{plan}\n\nTarget API Specification:\n{api_spec_str}\n\nPrevious Reviewer Errors (Fix all of these):\n{formatted_errors}\n\nGenerate the complete Full-Stack JSON file structure now:"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ]

    response = llm.invoke(messages)
    raw_content = response.content
    if isinstance(raw_content, list):
        raw_content = "\n".join([c if isinstance(c, str) else c.get("text", str(c)) for c in raw_content])
    content = str(raw_content).strip()

    # If content is empty or lacks JSON brackets, check reasoning_content (common for reasoning models)
    if (not content or '{' not in content) and hasattr(response, 'additional_kwargs'):
        reasoning = response.additional_kwargs.get('reasoning_content', '')
        if '{' in reasoning:
            print("Coder Agent: Extracted file structure from model reasoning channel.", flush=True)
            content = reasoning

    # Robust JSON extraction
    # Strip any markdown code fences if present
    content = re.sub(r"^```(?:json)?\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    start_idx = content.find('{')
    end_idx = content.rfind('}')

    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        content = content[start_idx:end_idx+1]

    files = {}
    code_status = ""
    try:
        files = json.loads(content, strict=False)
        code_status = f"Successfully generated {len(files)} full-stack files."
    except json.JSONDecodeError as e:
        print(f"JSON decode failed on primary attempt: {e}")
        # Try to fix common JSON issues like trailing commas or unescaped control characters
        cleaned = re.sub(r',\s*([\]}])', r'\1', content)
        try:
            files = json.loads(cleaned, strict=False)
            code_status = f"Successfully generated {len(files)} files after JSON sanitization."
        except Exception as e2:
            print(f"JSON decode failed after sanitization: {e2}")
            # Resilient Fallback: Regex extraction for file mapping
            pattern = r'"((?:/)?[a-zA-Z0-9_\-\./]+)":\s*"([\s\S]*?)(?="\s*,\s*"(?:/)?[a-zA-Z0-9_\-\./]+"\s*:|"\s*\})'
            matches = re.findall(pattern, content)
            if matches:
                for fpath, fbody in matches:
                    unescaped = unescape_json_string(fbody)
                    norm_key = fpath if fpath.startswith('/') else f"/{fpath}"
                    files[norm_key] = unescaped
                code_status = f"Successfully extracted {len(files)} files via pattern matcher."
                print(f"Resilient Pattern Matcher recovered {len(files)} files.")
            else:
                code_status = f"Failed to parse JSON: {e2}"
                files = {}

    # Normalize file path keys
    normalized_files = {}
    for path, code_content in files.items():
        norm_path = path if path.startswith('/') else f"/{path}"
        normalized_files[norm_path] = code_content
    files = normalized_files

    # Separate into frontend_files and backend_files
    backend_files = {}
    frontend_files = {}

    for norm_path, code_content in files.items():
        lower = norm_path.lower()
        if lower.startswith('/server') or 'server.js' in lower:
            backend_files[norm_path] = code_content
        elif lower == '/readme.md':
            # Include in both or root
            backend_files[norm_path] = code_content
            frontend_files[norm_path] = code_content
        else:
            frontend_files[norm_path] = code_content

    print(f"Coder Agent generated {len(backend_files)} backend files and {len(frontend_files)} frontend files (attempt {current_attempt}).")

    return {
        "code": code_status,
        "files": files,
        "backend_files": backend_files,
        "frontend_files": frontend_files,
        "attempt": current_attempt
    }
