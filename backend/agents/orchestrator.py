import json
import re
from langchain_core.messages import SystemMessage, HumanMessage
from llm_factory import get_llm

def orchestrator_node(state):
    print("--- ORCHESTRATOR AGENT ---")
    prompt = state.get("prompt", "")
    
    llm = get_llm()
    
    system_prompt = """You are the Lead Architect & Orchestrator Agent for a Full-Stack AI Web Developer.
Your task is to analyze the user's prompt and formulate a comprehensive technical plan for building BOTH the Frontend and the Backend.

You must design:
1. BACKEND ARCHITECTURE (Node.js + Express.js):
   - Server entry point: `server.js` running on port 5000 with CORS and express.json().
   - In-memory / JSON store with realistic seed data matching the domain.
   - RESTful API endpoints covering full CRUD operations (e.g. GET /api/items, POST /api/items, PUT /api/items/:id, DELETE /api/items/:id, plus GET /api/health).
   - Input validation, clear error responses, and proper HTTP status codes.

2. FRONTEND ARCHITECTURE (React + Tailwind CSS):
   - Interactive UI components (main App.js, modular components, responsive layout).
   - API client module (`services/api.js`) to consume backend endpoints with fallback data for preview.
   - State management, loading states, and optimistic or reactive UI updates.

3. STRUCTURED API CONTRACT:
   At the very end of your response, you MUST provide a JSON block with the exact list of API endpoints for the backend in this format:
   ```json:api_spec
   [
     {
       "method": "GET",
       "path": "/api/items",
       "description": "Retrieve all items",
       "sampleResponse": [{"id": 1, "name": "Sample"}]
     },
     {
       "method": "POST",
       "path": "/api/items",
       "description": "Create a new item",
       "sampleRequest": {"name": "New Item"},
       "sampleResponse": {"id": 2, "name": "New Item"}
     }
   ]
   ```

Output a clear, professional Markdown document containing the complete full-stack plan, followed by the ```json:api_spec block."""
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"User Prompt: {prompt}")
    ]
    
    response = llm.invoke(messages)
    content = response.content
    if isinstance(content, list):
        content = "\n".join([c if isinstance(c, str) else c.get("text", str(c)) for c in content])
    content = str(content)
    
    # Extract api_spec
    api_spec = []
    try:
        spec_match = re.search(r"```(?:json:api_spec|json)?\s*(\[[\s\S]*?\])\s*```", content)
        if spec_match:
            api_spec = json.loads(spec_match.group(1))
        else:
            # Look for any JSON array containing "path" or "method"
            json_arrays = re.findall(r"(\[\s*\{[\s\S]*?\}\s*\])", content)
            for raw_arr in json_arrays:
                try:
                    parsed = json.loads(raw_arr)
                    if isinstance(parsed, list) and len(parsed) > 0 and ("path" in parsed[0] or "method" in parsed[0]):
                        api_spec = parsed
                        break
                except Exception:
                    continue
    except Exception as e:
        print(f"Orchestrator warning: JSON parse error: {e}")

    # If still empty, automatically extract endpoints mentioned in text with regex
    if not api_spec:
        found_routes = re.findall(r"\b(GET|POST|PUT|DELETE|PATCH)\s+([/a-zA-Z0-9_:\-]+)", content)
        if found_routes:
            seen = set()
            for method, path in found_routes:
                if path.startswith("/api") and (method, path) not in seen:
                    seen.add((method, path))
                    api_spec.append({
                        "method": method,
                        "path": path,
                        "description": f"{method} {path} endpoint"
                    })

    if not api_spec:
        api_spec = [
            {"method": "GET", "path": "/api/health", "description": "Backend healthcheck", "sampleResponse": {"status": "ok"}},
            {"method": "GET", "path": "/api/items", "description": "Retrieve items", "sampleResponse": []},
            {"method": "POST", "path": "/api/items", "description": "Create item", "sampleResponse": {"success": True}}
        ]

        
    print(f"Orchestrator identified {len(api_spec)} API endpoints.")
    
    return {
        "plan": content,
        "api_spec": api_spec,
        "iteration": state.get("iteration", 0) + 1
    }

