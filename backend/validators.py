"""
validators.py - Comprehensive AST and static validation suite for full-stack applications.

Enforces 4 core rules:
1. syntax: JS syntax check via `node --check` (for server.js) and esbuild (for App.js/api.js).
2. route-contract: Verifies all api_spec endpoints and client URLs map to server.js routes.
3. import-allowlist: Restricts packages to approved whitelist and validates lucide-react icon exports.
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

# Cache for lucide-react exports to avoid re-invoking node on every validation call
_LUCIDE_EXPORTS_CACHE: Optional[Set[str]] = None

def get_installed_lucide_exports() -> Set[str]:
    """
    Introspects the locally installed lucide-react package exports using Node.js.
    Caches the resulting set of exported icon and component names.
    """
    global _LUCIDE_EXPORTS_CACHE
    if _LUCIDE_EXPORTS_CACHE is not None:
        return _LUCIDE_EXPORTS_CACHE

    possible_paths = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/node_modules/lucide-react")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "node_modules/lucide-react")),
        "lucide-react"
    ]

    for mod_path in possible_paths:
        try:
            # Escape backslashes for node -e on Windows
            clean_path = mod_path.replace("\\", "/")
            cmd = ["node", "-e", f"try {{ const l = require('{clean_path}'); console.log(JSON.stringify(Object.keys(l))); }} catch(e) {{ console.log('[]'); }}"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout.strip():
                exports_list = json.loads(res.stdout.strip())
                if exports_list:
                    _LUCIDE_EXPORTS_CACHE = set(exports_list)
                    return _LUCIDE_EXPORTS_CACHE
        except Exception:
            continue

    # Fallback to standard common icon names if node cannot resolve
    _LUCIDE_EXPORTS_CACHE = {
        "Plus", "Trash2", "Trash", "Edit", "Edit2", "Edit3", "Check", "CheckCircle",
        "X", "XCircle", "AlertCircle", "AlertTriangle", "Search", "Filter", "Download",
        "Upload", "Eye", "EyeOff", "Menu", "Settings", "User", "Users", "Mail", "Phone",
        "Calendar", "Clock", "ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown", "ChevronRight",
        "ChevronLeft", "ChevronUp", "ChevronDown", "ExternalLink", "Share", "Copy", "File",
        "Folder", "Home", "Database", "Server", "Cpu", "Activity", "BarChart", "BarChart2",
        "PieChart", "TrendingUp", "TrendingDown", "RefreshCw", "RotateCw", "Loader", "Loader2",
        "Info", "HelpCircle", "Lock", "Unlock", "Shield", "Zap", "Star", "Heart", "Smile"
    }
    return _LUCIDE_EXPORTS_CACHE


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


def validate_syntax(files: Dict[str, str]) -> List[StructuredError]:
    """
    JS syntax checker:
    - For server.js: executes `node --check`
    - For App.js, api.js, and other frontend JS/JSX files: executes esbuild via backend/check_syntax.js
    Returns structured errors with exact file and line numbers.
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
                    # Parse line number from node error output (e.g., C:\path\tmp.js:12 or :12)
                    line_no = 1
                    line_match = re.search(r':(\d+)\r?\n', stderr)
                    if line_match:
                        try:
                            line_no = int(line_match.group(1))
                        except ValueError:
                            line_no = 1

                    # Parse message
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
                    if not result.get("valid", True):
                        for err in result.get("errors", []):
                            errors.append({
                                "file": file_path,
                                "line": err.get("line", 1),
                                "rule": "syntax",
                                "message": f"Syntax error: {err.get('message', 'Syntax error')}"
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
    - Parses app.get/post/put/patch/delete(...) calls from server.js.
    - Normalizes path (:id) and compares against api_spec; MISSING routes are errors.
    - Verifies every URL called in services/api.js maps to an existing server.js route.
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
    # Matches: app.get('/api/items', ...), router.post("/api/items/:id", ...)
    route_pattern = re.compile(
        r'\b(?:app|router)\.(get|post|put|patch|delete)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]',
        re.IGNORECASE
    )

    server_routes: Set[Tuple[str, str]] = set()  # (METHOD, normalized_path)
    server_paths: Set[str] = set()               # normalized_path

    for match in route_pattern.finditer(server_code):
        method = match.group(1).upper()
        raw_path = match.group(2)
        norm_path = normalize_route_path(raw_path)
        server_routes.add((method, norm_path))
        server_paths.add(norm_path)

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
        # Match URL patterns in fetch or axios calls:
        # e.g., fetch('http://localhost:5000/api/items') or fetch(`/api/items/${id}`) or fetch('/api/items/' + id)
        url_patterns = [
            # Template literals with ${...}
            r'`(?:https?://[^/`]+)?(/api/[^`]*)`',
            # Single/double quoted strings
            r'[\'"](?:https?://[^/\'"]+)?(/api/[^\'"]*)[\'"]'
        ]

        lines = api_client_code.splitlines()
        for idx, line in enumerate(lines, start=1):
            for pat in url_patterns:
                for match in re.finditer(pat, line):
                    raw_url = match.group(1)
                    # Normalize dynamic segments like ${id} or ${item.id} to :id
                    normalized_url = re.sub(r'\$\{[^}]+\}', ':id', raw_url)
                    # Normalize concatenated string tail like ' + id' or '/123'
                    normalized_url = re.sub(r'/[0-9]+', '/:id', normalized_url)
                    normalized_path = normalize_route_path(normalized_url)

                    # Check if normalized_path maps to any known server route path
                    if normalized_path not in server_paths:
                        errors.append({
                            "file": api_client_path,
                            "line": idx,
                            "rule": "route-contract",
                            "message": f"Client calls endpoint '{raw_url}' which is not implemented in server.js"
                        })

    return errors


def validate_import_allowlist(files: Dict[str, str]) -> List[StructuredError]:
    """
    Import allowlist validator:
    - Frontend allowed packages: react, react-dom, react-dom/client, lucide-react.
      * All named icon imports from lucide-react are checked against installed exports.
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

    # Regexes for ES imports and CommonJS requires
    import_stmt_pattern = re.compile(
        r'^\s*import\s+(?:([\w*\s{},]+)\s+from\s+)?[\'"]([^\'"]+)[\'"]',
        re.MULTILINE
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

        lines = code.splitlines()
        for line_idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            # Ignore comment lines
            if stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*'):
                continue

            # 1. Check ES imports
            for match in import_stmt_pattern.finditer(line):
                clause = match.group(1) or ""
                pkg = match.group(2).strip()

                # Local relative imports are allowed
                if pkg.startswith('.') or pkg.startswith('/'):
                    continue

                # Top-level package name
                base_pkg = pkg.split('/')[0] if not pkg.startswith('@') else '/'.join(pkg.split('/')[:2])
                
                if pkg not in allowed_pkgs and base_pkg not in allowed_pkgs:
                    errors.append({
                        "file": file_path,
                        "line": line_idx,
                        "rule": "import-allowlist",
                        "message": f"Import of unapproved package '{pkg}' is not permitted."
                    })
                    continue

                # For lucide-react: validate every named icon export
                if pkg == "lucide-react" and "{" in clause:
                    named_block = clause[clause.find("{") + 1 : clause.rfind("}")]
                    raw_items = [item.strip() for item in named_block.split(",") if item.strip()]
                    for item in raw_items:
                        # Clean alias e.g. "Trash2 as DeleteIcon" -> "Trash2"
                        parts = re.split(r'\s+as\s+', item)
                        icon_name = parts[0].strip()
                        if icon_name and icon_name not in lucide_exports:
                            errors.append({
                                "file": file_path,
                                "line": line_idx,
                                "rule": "import-allowlist",
                                "message": f"Icon '{icon_name}' is not exported by lucide-react."
                            })

            # 2. Check CommonJS require calls
            for match in require_pattern.finditer(line):
                pkg = match.group(1).strip()
                if pkg.startswith('.') or pkg.startswith('/'):
                    continue

                base_pkg = pkg.split('/')[0] if not pkg.startswith('@') else '/'.join(pkg.split('/')[:2])
                if pkg not in allowed_pkgs and base_pkg not in allowed_pkgs:
                    errors.append({
                        "file": file_path,
                        "line": line_idx,
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
    Runs all 4 static validation rules and aggregates structured errors.
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
