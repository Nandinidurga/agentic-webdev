import os
import sys

# Ensure backend root is in Python path for local module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from validators import StructuredError, validate_all


def reviewer_node(state):
    print("--- REVIEWER AGENT (FULL-STACK VALIDATION) ---")
    cancel_event = state.get("cancel_event")
    if cancel_event and cancel_event.is_set():
        raise TimeoutError("Reviewer execution aborted: shared cancel flag active.")

    files = dict(state.get("files", {}))
    backend_files = dict(state.get("backend_files", {}))
    frontend_files = dict(state.get("frontend_files", {}))
    api_spec = state.get("api_spec", [])
    current_attempt = state.get("attempt", 0)
    
    structured_errors: list[StructuredError] = []
    validation_logs: list[str] = []
    
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
            validation_logs.append("Backend Check: Found /server.js.")
            if "cors" not in server_code.lower():
                structured_errors.append({
                    "file": "/server.js",
                    "line": 1,
                    "rule": "route-contract",
                    "message": "Backend Warning: CORS middleware is recommended to avoid browser network errors."
                })
        
        # 2. Structural requirements: Frontend Entrypoint
        app_code = None
        for path, code in files.items():
            if path.lower().endswith('app.js') or path.lower().endswith('app.tsx') or path.lower().endswith('app.jsx'):
                app_code = code
                break
        
        if not app_code:
            structured_errors.append({
                "file": "/App.js",
                "line": 1,
                "rule": "syntax",
                "message": "Frontend Error: Missing primary React component (/App.js)."
            })
        else:
            validation_logs.append("Frontend Check: Found React entry component.")

        # 3. Run full AST & static validators suite
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
        "attempt": current_attempt,
        "cancel_event": cancel_event
    }
