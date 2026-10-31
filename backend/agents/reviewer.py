import os
import re
from typing import Dict, List, Any
import sys

# Ensure backend root is in Python path for local module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validators import validate_all, StructuredError

def heal_frontend_code(code: str) -> str:
    """
    Defensively heals React code to guarantee live Sandpack preview stability:
    - Replaces uninitialized useState() with useState([])
    - Wraps bare array methods (.map, .filter, .reduce) with (var || [])
    - Wraps .toFixed() with (Number(var) || 0).toFixed()
    """
    if not code or not isinstance(code, str):
        return code

    # 1. Uninitialized useState() or useState(undefined)
    code = re.sub(r'useState\s*\(\s*\)', 'useState([])', code)
    code = re.sub(r'useState\s*\(\s*undefined\s*\)', 'useState([])', code)

    # 2. Defensive array methods: map, filter, reduce, forEach, some, every, slice
    array_pattern = r'(?<![\)\w\?\]])\b([a-zA-Z_$][a-zA-Z0-9_$]*(?:\.[a-zA-Z_$][a-zA-Z0-9_$]*)*)\.(map|filter|reduce|forEach|some|every|slice)\('
    def array_repl(match):
        var_chain = match.group(1)
        method = match.group(2)
        base = var_chain.split('.')[0]
        if base in ['Array', 'React', 'Promise', 'Object']:
            return match.group(0)
        return f"({var_chain} || []).{method}("
    code = re.sub(array_pattern, array_repl, code)

    # 3. Defensive number formatting: amount.toFixed(2) -> (Number(amount) || 0).toFixed(2)
    fixed_pattern = r'(?<![\.\)\]\w])\b([a-zA-Z_$][a-zA-Z0-9_$\.]*)\.toFixed\('
    def fixed_repl(match):
        expr = match.group(1)
        return f"(Number({expr}) || 0).toFixed("
    code = re.sub(fixed_pattern, fixed_repl, code)

    return code

def reviewer_node(state):
    print("--- REVIEWER AGENT (FULL-STACK VALIDATION) ---")
    files = dict(state.get("files", {}))
    backend_files = dict(state.get("backend_files", {}))
    frontend_files = dict(state.get("frontend_files", {}))
    api_spec = state.get("api_spec", [])
    current_attempt = state.get("attempt", 0)
    
    structured_errors: List[StructuredError] = []
    validation_logs: List[str] = []
    
    if not files:
        structured_errors.append({
            "file": "general",
            "line": 1,
            "rule": "syntax",
            "message": "Critical: No files were generated or JSON could not be parsed."
        })
    else:
        validation_logs.append(f"Received {len(files)} total files ({len(backend_files)} backend, {len(frontend_files)} frontend).")
        
        # 1. Structural requirements: Backend Server
        server_code = None
        for path, code in files.items():
            if path.lower().endswith('server.js'):
                server_code = code
                break
                
        if not server_code:
            structured_errors.append({
                "file": "/server.js",
                "line": 1,
                "rule": "route-contract",
                "message": "Backend Error: Missing `/server.js`. The application must include an Express.js server."
            })
        else:
            validation_logs.append("Backend Check: Found `/server.js`.")
            if "express" not in server_code:
                structured_errors.append({
                    "file": "/server.js",
                    "line": 1,
                    "rule": "route-contract",
                    "message": "Backend Error: `/server.js` does not import or require Express."
                })
            if "app.listen" not in server_code and "server.listen" not in server_code:
                structured_errors.append({
                    "file": "/server.js",
                    "line": 1,
                    "rule": "route-contract",
                    "message": "Backend Error: `/server.js` does not start the server using `app.listen(...)`."
                })

        # 2. Structural requirements: Frontend Main Component
        app_code = files.get("/App.js") or files.get("App.js")
        if not app_code:
            for path, code in files.items():
                if path.lower().endswith("/app.js") or path.lower() == "app.js":
                    app_code = code
                    break
                    
        if not app_code:
            structured_errors.append({
                "file": "/App.js",
                "line": 1,
                "rule": "syntax",
                "message": "Frontend Error: Missing main React component `/App.js`."
            })
        else:
            validation_logs.append("Frontend Check: Found `/App.js`.")

        # 3. Optional regex auto-heal for React components (behind HEAL_REGEX=1, default off)
        heal_regex_enabled = os.getenv("HEAL_REGEX", "0").strip().lower() in ("1", "true")
        if heal_regex_enabled:
            healed_count = 0
            for path, code in list(files.items()):
                lower = path.lower()
                if not lower.startswith('/server') and 'server.js' not in lower:
                    if lower.endswith(('.js', '.jsx', '.tsx', '.ts')):
                        healed = heal_frontend_code(code)
                        if healed != code:
                            files[path] = healed
                            if path in frontend_files:
                                frontend_files[path] = healed
                            healed_count += 1
                            
            if healed_count > 0:
                validation_logs.append(f"Auto-Healer: Injected runtime defensive guards into {healed_count} frontend file(s) via HEAL_REGEX.")

        # 4. Run full AST & static validators suite
        # Rules: syntax (node --check / esbuild), route-contract, import-allowlist, package-json (strict json.loads)
        static_errors = validate_all(files, api_spec)
        structured_errors.extend(static_errors)

    execution_result = "\n".join(validation_logs)
    
    if structured_errors:
        err_summary = "\n".join([f"[{e['file']}:{e['line']}] ({e['rule']}) {e['message']}" for e in structured_errors])
        print(f"Reviewer identified {len(structured_errors)} issues (attempt {current_attempt}):\n{err_summary}")
    else:
        print("Reviewer: Full-stack validation passed successfully!")
        execution_result += "\nAll full-stack validation checks passed."

    return {
        "execution_result": execution_result,
        "backend_test_results": "Backend static validation complete." if not structured_errors else "\n".join(
            [f"[{e['file']}:{e['line']}] {e['message']}" for e in structured_errors]
        ),
        "errors": structured_errors,
        "files": files,
        "frontend_files": frontend_files,
        "backend_files": backend_files,
        "attempt": current_attempt
    }
