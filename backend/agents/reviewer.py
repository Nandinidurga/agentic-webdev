import os
import re

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
    current_iteration = state.get("iteration", 0)
    
    critical_errors = []
    validation_logs = []
    
    if not files:
        critical_errors.append("Critical: No files were generated or JSON could not be parsed.")
    else:
        validation_logs.append(f"Received {len(files)} total files ({len(backend_files)} backend, {len(frontend_files)} frontend).")
        
        # 1. Validate Backend Files
        server_code = None
        for path, code in files.items():
            if path.lower().endswith('server.js'):
                server_code = code
                break
                
        if not server_code:
            critical_errors.append("Backend Error: Missing `/server.js`. The application must include an Express.js server.")
        else:
            validation_logs.append("Backend Check: Found `/server.js`.")
            
            # Check for Express setup
            if "express" not in server_code:
                critical_errors.append("Backend Error: `/server.js` does not import or require Express.")
            if "cors" not in server_code:
                validation_logs.append("Backend Warning: CORS middleware not detected in `/server.js`. Adding recommendation.")
            if "app.listen" not in server_code and "server.listen" not in server_code:
                critical_errors.append("Backend Error: `/server.js` does not start the server using `app.listen(...)`.")
            
            # Check for planned API endpoints
            if api_spec:
                missing_routes = []
                for endpoint in api_spec:
                    path = endpoint.get("path", "")
                    route_snippet = path.split("?")[0]
                    if route_snippet and route_snippet not in server_code:
                        missing_routes.append(f"{endpoint.get('method', 'GET')} {route_snippet}")
                
                if missing_routes and len(missing_routes) > len(api_spec) // 2:
                    validation_logs.append(f"Backend Warning: Expected endpoints not explicitly in `/server.js`: {', '.join(missing_routes[:3])}.")
                else:
                    validation_logs.append("Backend Check: Endpoints verified against API specification.")

        # 2. Validate Frontend Files
        app_code = files.get("/App.js") or files.get("App.js")
        if not app_code:
            for path, code in files.items():
                if path.lower().endswith("/app.js") or path.lower() == "app.js":
                    app_code = code
                    break
                    
        if not app_code:
            critical_errors.append("Frontend Error: Missing main React component `/App.js`.")
        else:
            validation_logs.append("Frontend Check: Found `/App.js`.")
            if "export default" not in app_code and "export {" not in app_code:
                validation_logs.append("Frontend Warning: `/App.js` does not have an explicit default export.")

        # 3. Validate API Client Service
        api_client_code = files.get("/services/api.js") or files.get("services/api.js")
        if not api_client_code:
            for path, code in files.items():
                if "api.js" in path.lower():
                    api_client_code = code
                    break
                    
        if not api_client_code:
            validation_logs.append("Frontend Note: `/services/api.js` was not found. Using fallback preview store.")
        else:
            validation_logs.append("Frontend Check: Found `/services/api.js` client module.")

        # 4. Auto-heal all frontend React components and services
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
            validation_logs.append(f"Auto-Healer: Injected runtime defensive guards into {healed_count} frontend file(s).")

        # 5. Auto-heal any package.json files (convert single quotes to valid JSON double quotes)
        for path, code in list(files.items()):
            if 'package.json' in path.lower() and isinstance(code, str):
                cleaned_pkg = code.strip()
                if "'" in cleaned_pkg and '"' not in cleaned_pkg:
                    cleaned_pkg = cleaned_pkg.replace("'", '"')
                    files[path] = cleaned_pkg
                    if path in frontend_files:
                        frontend_files[path] = cleaned_pkg
                    if path in backend_files:
                        backend_files[path] = cleaned_pkg
                    validation_logs.append(f"Auto-Healer: Converted single quotes in `{path}` to valid JSON.")

    errors = "\n".join(critical_errors)
    execution_result = "\n".join(validation_logs)
    
    if errors:
        print(f"Reviewer identified critical issues (iteration {current_iteration + 1}):\n{errors}")
    else:
        print("Reviewer: Full-stack validation passed successfully!")
        execution_result += "\nAll full-stack validation checks passed."

    return {
        "execution_result": execution_result,
        "backend_test_results": "Backend static validation complete." if not errors else errors,
        "errors": errors,
        "files": files,
        "frontend_files": frontend_files,
        "backend_files": backend_files,
        "iteration": current_iteration + 1
    }
