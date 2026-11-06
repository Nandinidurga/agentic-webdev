"""
validators.py - Comprehensive AST and static validation suite for full-stack applications.

Enforces 4 core rules:
1. syntax: JS syntax check via `node --check` (for server.js) and esbuild (for App.js/api.js).
   Returns explicit "validator-unavailable" warning when esbuild is unreachable.
2. route-contract: Verifies all api_spec endpoints and client URLs map to server.js routes.
   Resolves Express router mounting (app.use('/prefix', router)), route chaining (app.route().get().post()),
   ${BASE}/api template URLs, and treats trailing ${...} as optional parameters.
3. import-allowlist: Restricts packages to approved whitelist and validates multi-line lucide-react icon imports.
   Returns explicit "validator-unavailable" warning when lucide-react exports cannot be resolved.
4. package-json: Strict json.loads parsing for package descriptors without blind quote replacement.

Structured error format:
{"file": str, "line": int, "rule": str, "message": str}
"""

import os
import re
import json
import tempfile
import subprocess
from typing import Dict, List, Any, Optional, Set, Tuple

# Type definition for structured errors
StructuredError = Dict[str, Any]

# Cache for lucide-react exports: None indicates uninitialized or unavailable
_LUCIDE_EXPORTS_CACHE: Optional[Set[str]] = None
_LUCIDE_RESOLVED: Optional[bool] = None


def remove_js_comments(code: str) -> str:
    """
    Replaces comments with spaces and newlines so that character offsets
    and line numbers are preserved. Preserves single, double, and template string literals.
    """
    def replacer(match):
        s = match.group(0)
        if s.startswith('/') and len(s) > 1 and (s[1] == '/' or s[1] == '*'):
            return ''.join('\n' if c == '\n' else ' ' for c in s)
        return s

    pattern = re.compile(
        r'//.*?$|/\*[\s\S]*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"|`(?:\\.|[^\\`])*`',
        re.DOTALL | re.MULTILINE
    )
    return re.sub(pattern, replacer, code)


def get_installed_lucide_exports() -> Optional[Set[str]]:
    """
    Introspects the locally installed lucide-react package exports using Node.js.
    Returns the set of exported icon and component names if resolved,
    or None if lucide-react cannot be resolved.
    """
    global _LUCIDE_EXPORTS_CACHE, _LUCIDE_RESOLVED
    if _LUCIDE_RESOLVED is True and _LUCIDE_EXPORTS_CACHE is not None:
        return _LUCIDE_EXPORTS_CACHE
    if _LUCIDE_RESOLVED is False:
        return None

    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/node_modules/lucide-react")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "node_modules/lucide-react")),
        "lucide-react"
    ]

    for mod_path in possible_paths:
        try:
            clean_path = mod_path.replace("\\", "/")
            cmd = ["node", "-e", f"try {{ const l = require('{clean_path}'); console.log(JSON.stringify(Object.keys(l))); }} catch(e) {{ console.log('[]'); }}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                exports_list = json.loads(res.stdout.strip())
                if exports_list and len(exports_list) > 10:
                    _LUCIDE_EXPORTS_CACHE = set(exports_list)
                    _LUCIDE_RESOLVED = True
                    return _LUCIDE_EXPORTS_CACHE
        except Exception:
            continue

    _LUCIDE_RESOLVED = False
    return None


def normalize_route_path(path: str) -> str:
    """
    Normalizes REST route paths by:
    - Stripping query strings: /api/items?limit=10 -> /api/items
    - Replacing parameterized segments (:id, :itemId, :userId) with a canonical ':id'
    - Stripping trailing slashes
    """
    if not path:
        return "/"
    
    # Strip query parameters
    path = path.split("?")[0].strip()
    
    # Replace URL parameter tokens like :itemId, :id, :todoId, :userId with :id
    normalized = re.sub(r':[a-zA-Z0-9_]+', ':id', path)
    
    # Normalize multiple slashes and strip trailing slashes
    normalized = re.sub(r'/+', '/', normalized)
    if len(normalized) > 1 and normalized.endswith('/'):
        normalized = normalized[:-1]
        
    return normalized if normalized.startswith('/') else f"/{normalized}"


def extract_server_routes(server_code: str) -> Tuple[Set[Tuple[str, str]], Set[str]]:
    """
    Extracts all routes from Express.js server code, supporting:
    (a) Direct calls: app.get('/path', ...), router.post('/path', ...)
    (b) Route chaining: app.route('/path').get(...).post(...)
        or router.route('/path').get(...).delete(...)
    (c) Express router mounting: app.use('/prefix', router)
        and router.use('/prefix', subRouter)
    Returns:
        (server_routes, server_paths)
        server_routes: Set of (METHOD, normalized_path)
        server_paths: Set of normalized_path
    """
    clean_code = remove_js_comments(server_code)
    
    server_routes: Set[Tuple[str, str]] = set()
    server_paths: Set[str] = set()

    # Dictionary mapping identifier -> list of (method, raw_path)
    object_routes: Dict[str, List[Tuple[str, str]]] = {}
    
    # List of (parent_ident, mount_prefix, child_ident)
    mounts: List[Tuple[str, str, str]] = []

    # 1. Parse router mounts: app.use('/api', router) or parent.use('/prefix', child)
    mount_with_prefix = re.compile(
        r'\b([a-zA-Z0-9_$]+)\.use\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*([a-zA-Z0-9_$]+)\b'
    )
    for m in mount_with_prefix.finditer(clean_code):
        parent, prefix, child = m.group(1), m.group(2).strip(), m.group(3)
        mounts.append((parent, prefix, child))

    # Mount without explicit prefix: app.use(router)
    mount_without_prefix = re.compile(
        r'\b([a-zA-Z0-9_$]+)\.use\s*\(\s*([a-zA-Z0-9_$]+)\s*\)'
    )
    for m in mount_without_prefix.finditer(clean_code):
        parent, child = m.group(1), m.group(2)
        if child not in {"express", "cors"}:
            mounts.append((parent, "", child))

    # 2. Parse direct route calls: ident.(get|post|put|patch|delete)('path', ...)
    direct_route_pattern = re.compile(
        r'\b([a-zA-Z0-9_$]+)\.(get|post|put|patch|delete)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE
    )
    for m in direct_route_pattern.finditer(clean_code):
        ident = m.group(1)
        method = m.group(2).upper()
        path = m.group(3)
        if ident not in object_routes:
            object_routes[ident] = []
        object_routes[ident].append((method, path))

    # 3. Parse route chains: ident.route('/path').get(...).post(...)
    route_chain_pattern = re.compile(
        r'\b([a-zA-Z0-9_$]+)\.route\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*\)',
        re.IGNORECASE
    )
    for m in route_chain_pattern.finditer(clean_code):
        ident = m.group(1)
        path = m.group(2)
        if ident not in object_routes:
            object_routes[ident] = []
        
        # Look ahead for chained method calls until semicolon or next statement
        tail = clean_code[m.end():]
        end_idx = len(tail)
        semicolon_idx = tail.find(';')
        if semicolon_idx != -1:
            end_idx = semicolon_idx
        
        decl_match = re.search(r'\b(?:const|let|var|function|app\.|module\.exports)\b', tail[:end_idx])
        if decl_match:
            end_idx = decl_match.start()
        
        chain_segment = tail[:end_idx]
        method_pattern = re.compile(r'\.\s*(get|post|put|patch|delete)\s*\(', re.IGNORECASE)
        for mm in method_pattern.finditer(chain_segment):
            method = mm.group(1).upper()
            object_routes[ident].append((method, path))

    # 4. Resolve mount prefixes
    prefixes: Dict[str, List[str]] = {"app": [""]}
    
    # Propagate prefixes across mounts (support nested routers)
    for _ in range(5):
        updated = False
        for parent, mount_prefix, child in mounts:
            if parent in prefixes:
                for parent_prefix in prefixes[parent]:
                    combined = f"{parent_prefix}/{mount_prefix}".replace("//", "/") if parent_prefix else mount_prefix
                    norm_combined = normalize_route_path(combined)
                    if child not in prefixes:
                        prefixes[child] = []
                    if norm_combined not in prefixes[child]:
                        prefixes[child].append(norm_combined)
                        updated = True
        if not updated:
            break

    # 5. Build final server_routes and server_paths
    for ident, routes in object_routes.items():
        if ident in prefixes:
            for pfx in prefixes[ident]:
                for method, raw_path in routes:
                    full_path = f"{pfx}/{raw_path}".replace("//", "/") if pfx else raw_path
                    norm = normalize_route_path(full_path)
                    server_routes.add((method, norm))
                    server_paths.add(norm)
        else:
            # Fallback for router instances whose mounting was not explicit
            for method, raw_path in routes:
                norm = normalize_route_path(raw_path)
                server_routes.add((method, norm))
                server_paths.add(norm)

    return server_routes, server_paths


def validate_syntax(files: Dict[str, str]) -> List[StructuredError]:
    """
    JS syntax checker:
    - For server.js: executes `node --check`
    - For App.js, api.js, and other frontend JS/JSX files: executes esbuild via backend/check_syntax.js
    Returns explicit 'validator-unavailable' warning when esbuild cannot be resolved.
    """
    errors: List[StructuredError] = []
    checker_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "check_syntax.js"))

    for file_path, code in files.items():
        if not isinstance(code, str) or not code.strip():
            continue

        lower = file_path.lower()
        if not lower.endswith(('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')):
            continue

        # 1. Server-side check using `node --check`
        if lower.endswith('server.js') or lower.startswith('/server/') or lower.startswith('server/'):
            with tempfile.NamedTemporaryFile(suffix=".js", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp_path = tmp.name
                tmp.write(code)

            try:
                proc = subprocess.run(
                    ["node", "--check", tmp_path],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if proc.returncode != 0:
                    stderr = proc.stderr
                    line_no = 1
                    line_match = re.search(r':(\d+)\r?\n', stderr)
                    if line_match:
                        try:
                            line_no = int(line_match.group(1))
                        except ValueError:
                            line_no = 1

                    msg = "Node.js syntax error in server code."
                    for line in stderr.splitlines():
                        if "SyntaxError:" in line or "Error:" in line:
                            msg = line.strip()
                            break

                    errors.append({
                        "file": file_path,
                        "line": line_no,
                        "rule": "syntax",
                        "message": msg
                    })
            except Exception as ex:
                errors.append({
                    "file": file_path,
                    "line": 1,
                    "rule": "syntax",
                    "message": f"Execution failure during syntax check: {str(ex)}"
                })
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

        # 2. Frontend check using esbuild (App.js, api.js, components, etc.)
        else:
            with tempfile.NamedTemporaryFile(suffix=".jsx" if "app" in lower or ".jsx" in lower else ".js", delete=False, mode="w", encoding="utf-8") as tmp:
                tmp_path = tmp.name
                tmp.write(code)

            try:
                loader = "jsx" if ("app" in lower or ".jsx" in lower or ".tsx" in lower) else "js"
                proc = subprocess.run(
                    ["node", checker_script, tmp_path, loader],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    result = json.loads(proc.stdout.strip())
                    if result.get("unavailable") or result.get("warning") == "esbuild unavailable":
                        errors.append({
                            "file": file_path,
                            "line": 1,
                            "rule": "validator-unavailable",
                            "message": "esbuild could not be resolved for frontend syntax validation."
                        })
                    elif not result.get("valid", True):
                        for err in result.get("errors", []):
                            errors.append({
                                "file": file_path,
                                "line": err.get("line", 1),
                                "rule": "syntax",
                                "message": f"Syntax error: {err.get('message', 'Syntax error')}"
                            })
                else:
                    stderr = proc.stderr if proc else ""
                    if "Cannot find module" in stderr or "esbuild" in stderr:
                        errors.append({
                            "file": file_path,
                            "line": 1,
                            "rule": "validator-unavailable",
                            "message": "esbuild could not be resolved for frontend syntax validation."
                        })
                    else:
                        errors.append({
                            "file": file_path,
                            "line": 1,
                            "rule": "syntax",
                            "message": f"Syntax validation failed: {stderr.strip() or 'Execution error'}"
                        })
            except Exception as ex:
                errors.append({
                    "file": file_path,
                    "line": 1,
                    "rule": "syntax",
                    "message": f"Syntax validation failed: {str(ex)}"
                })
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

    return errors


def validate_route_contract(files: Dict[str, str], api_spec: Optional[List[Dict[str, Any]]] = None) -> List[StructuredError]:
    """
    Route contract check:
    - Extracts server routes with full router mounting (app.use) and route chaining (app.route).
    - Compares against api_spec; missing endpoints are errors.
    - Resolves client URLs in services/api.js:
      * Resolves ${BASE}/api, ${API_URL}/api template strings.
      * Treats trailing ${...} as optional parameter (matches /path/:id OR /path).
    """
    errors: List[StructuredError] = []

    # Locate server.js
    server_path = None
    server_code = None
    for path, code in files.items():
        if path.lower().endswith("server.js"):
            server_path = path
            server_code = code
            break

    if not server_code:
        errors.append({
            "file": "/server.js",
            "line": 1,
            "rule": "route-contract",
            "message": "Missing `/server.js`. The application must include an Express.js backend server."
        })
        return errors

    # Extract all route registrations from server.js
    server_routes, server_paths = extract_server_routes(server_code)

    # 1. Compare against api_spec
    if api_spec and isinstance(api_spec, list):
        for endpoint in api_spec:
            if not isinstance(endpoint, dict):
                continue
            expected_method = str(endpoint.get("method", "GET")).upper()
            raw_path = endpoint.get("path", "")
            if not raw_path:
                continue
            norm_path = normalize_route_path(raw_path)

            if (expected_method, norm_path) not in server_routes:
                errors.append({
                    "file": server_path or "/server.js",
                    "line": 1,
                    "rule": "route-contract",
                    "message": f"Missing required API route in server.js: {expected_method} {raw_path}"
                })

    # 2. Verify every URL in services/api.js maps to an existing route in server.js
    api_client_path = None
    api_client_code = None
    for path, code in files.items():
        if "api.js" in path.lower() and not path.lower().endswith("server.js"):
            api_client_path = path
            api_client_code = code
            break

    if api_client_code:
        clean_api_code = remove_js_comments(api_client_code)

        template_pattern = re.compile(r'`([^`]+)`')
        quoted_pattern = re.compile(r'[\'"]([^\'"]+)[\'"]')

        extracted_calls = []

        # Find template literals with line numbers
        for m in template_pattern.finditer(clean_api_code):
            content = m.group(1)
            line_no = api_client_code[:m.start()].count('\n') + 1
            if "/api" in content:
                extracted_calls.append((content, line_no, True))

        # Find quoted literals with line numbers
        for m in quoted_pattern.finditer(clean_api_code):
            content = m.group(1)
            line_no = api_client_code[:m.start()].count('\n') + 1
            if "/api" in content:
                extracted_calls.append((content, line_no, False))

        for raw_url, line_no, is_template in extracted_calls:
            api_idx = raw_url.find('/api')
            if api_idx == -1:
                continue
            path_part = raw_url[api_idx:]
            
            # Strip query string
            path_part = path_part.split('?')[0].strip()

            candidate_paths: Set[str] = set()

            if is_template:
                # Check for trailing ${...} parameter
                trailing_param = re.search(r'/\$\{[^}]+\}\s*$', path_part)
                if trailing_param:
                    # Treat trailing ${...} as an optional parameter:
                    # Candidate 1: parameterized route -> /path/:id
                    p_with_id = path_part[:trailing_param.start()] + '/:id'
                    candidate_paths.add(normalize_route_path(p_with_id))
                    # Candidate 2: base route without param -> /path
                    p_without_id = path_part[:trailing_param.start()]
                    candidate_paths.add(normalize_route_path(p_without_id))
                else:
                    # Replace intermediate ${...} with :id
                    normalized = re.sub(r'\$\{[^}]+\}', ':id', path_part)
                    candidate_paths.add(normalize_route_path(normalized))
            else:
                normalized = re.sub(r'/[0-9]+', '/:id', path_part)
                candidate_paths.add(normalize_route_path(normalized))

            # Verify if ANY candidate path maps to an existing server route
            if not any(cand in server_paths for cand in candidate_paths):
                errors.append({
                    "file": api_client_path,
                    "line": line_no,
                    "rule": "route-contract",
                    "message": f"Client calls endpoint '{raw_url}' which is not implemented in server.js"
                })

    return errors


def validate_import_allowlist(files: Dict[str, str]) -> List[StructuredError]:
    """
    Import allowlist validator:
    - Frontend allowed packages: react, react-dom, react-dom/client, lucide-react.
      * All named icon imports from lucide-react (including multi-line imports) are checked.
      * When lucide-react cannot be resolved, returns explicit 'validator-unavailable' warning
        instead of emitting false errors.
    - Backend allowed packages: express, cors, standard Node.js built-ins.
    - Local relative imports (starting with ./ or ../) are allowed.
    Unknown imports are structured errors.
    """
    errors: List[StructuredError] = []
    lucide_exports = get_installed_lucide_exports()

    allowed_frontend_packages = {"react", "react-dom", "react-dom/client", "lucide-react"}
    allowed_backend_packages = {
        "express", "cors", "path", "fs", "http", "https", "crypto",
        "os", "url", "events", "util", "stream", "process", "dotenv", "buffer"
    }

    # Multi-line aware ES import pattern
    import_stmt_pattern = re.compile(
        r'(?m)^\s*import\s+(?:([\w*\s{},]+?)\s+from\s+)?[\'"]([^\'"]+)[\'"]',
        re.DOTALL
    )
    require_pattern = re.compile(
        r'\brequire\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
    )

    for file_path, code in files.items():
        if not isinstance(code, str) or not code.strip():
            continue

        lower = file_path.lower()
        if not lower.endswith(('.js', '.jsx', '.ts', '.tsx')):
            continue

        is_backend = lower.endswith('server.js') or '/server/' in lower or lower.startswith('server/')
        allowed_pkgs = allowed_backend_packages if is_backend else allowed_frontend_packages

        clean_code = remove_js_comments(code)

        # 1. Check ES imports (multi-line aware)
        for match in import_stmt_pattern.finditer(clean_code):
            clause = match.group(1) or ""
            pkg = match.group(2).strip()
            line_no = code[:match.start()].count('\n') + 1

            # Local relative imports are allowed
            if pkg.startswith('.') or pkg.startswith('/'):
                continue

            # Top-level package name
            base_pkg = pkg.split('/')[0] if not pkg.startswith('@') else '/'.join(pkg.split('/')[:2])
            
            if pkg not in allowed_pkgs and base_pkg not in allowed_pkgs:
                errors.append({
                    "file": file_path,
                    "line": line_no,
                    "rule": "import-allowlist",
                    "message": f"Import of unapproved package '{pkg}' is not permitted."
                })
                continue

            # For lucide-react: validate every named icon export
            if pkg == "lucide-react":
                if lucide_exports is None:
                    # Explicit unavailable warning instead of false errors
                    errors.append({
                        "file": file_path,
                        "line": line_no,
                        "rule": "validator-unavailable",
                        "message": "lucide-react could not be resolved to validate icon exports."
                    })
                elif "{" in clause:
                    named_block = clause[clause.find("{") + 1 : clause.rfind("}")]
                    raw_items = [item.strip() for item in named_block.split(",") if item.strip()]
                    for item in raw_items:
                        parts = re.split(r'\s+as\s+', item)
                        icon_name = parts[0].strip()
                        icon_idx = match.start(1) + clause.find(item)
                        icon_line = code[:icon_idx].count('\n') + 1
                        if icon_name and icon_name not in lucide_exports:
                            errors.append({
                                "file": file_path,
                                "line": icon_line,
                                "rule": "import-allowlist",
                                "message": f"Icon '{icon_name}' is not exported by lucide-react."
                            })

        # 2. Check CommonJS require calls
        for match in require_pattern.finditer(clean_code):
            pkg = match.group(1).strip()
            line_no = code[:match.start()].count('\n') + 1

            if pkg.startswith('.') or pkg.startswith('/'):
                continue

            base_pkg = pkg.split('/')[0] if not pkg.startswith('@') else '/'.join(pkg.split('/')[:2])
            if pkg not in allowed_pkgs and base_pkg not in allowed_pkgs:
                errors.append({
                    "file": file_path,
                    "line": line_no,
                    "rule": "import-allowlist",
                    "message": f"Require of unapproved package '{pkg}' is not permitted."
                })

    return errors


def validate_package_json(files: Dict[str, str]) -> List[StructuredError]:
    """
    package.json validation:
    - Parses all package.json files strictly with json.loads.
    - If invalid, records structured error with exact line (no blind quote replacement).
    """
    errors: List[StructuredError] = []

    for file_path, code in files.items():
        if not file_path.lower().endswith("package.json"):
            continue

        if not isinstance(code, str) or not code.strip():
            errors.append({
                "file": file_path,
                "line": 1,
                "rule": "package-json",
                "message": f"Package descriptor `{file_path}` is empty."
            })
            continue

        try:
            parsed = json.loads(code)
            if not isinstance(parsed, dict):
                errors.append({
                    "file": file_path,
                    "line": 1,
                    "rule": "package-json",
                    "message": f"`{file_path}` root must be a valid JSON object."
                })
        except json.JSONDecodeError as exc:
            errors.append({
                "file": file_path,
                "line": exc.lineno,
                "rule": "package-json",
                "message": f"Invalid JSON syntax in `{file_path}`: {exc.msg} (line {exc.lineno}, col {exc.colno})"
            })

    return errors


def validate_all(files: Dict[str, str], api_spec: Optional[List[Dict[str, Any]]] = None) -> List[StructuredError]:
    """
    Runs all static validation rules and aggregates structured errors.
    """
    all_errors: List[StructuredError] = []
    
    # 1. Package descriptor check
    all_errors.extend(validate_package_json(files))
    
    # 2. Import allowlist
    all_errors.extend(validate_import_allowlist(files))
    
    # 3. Route contract
    all_errors.extend(validate_route_contract(files, api_spec))
    
    # 4. JS syntax check
    all_errors.extend(validate_syntax(files))
    
    return all_errors
