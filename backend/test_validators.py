"""
test_validators.py - Comprehensive pytest suite for AST & static validators.

Covers:
1. JS Syntax Check: node --check (server.js), esbuild (App.js/api.js) with file + line.
2. Route Contract: app.METHOD route parsing, :id parameter normalization, api_spec matching, and services/api.js URL mapping.
3. Import Allowlist: react, react-dom, lucide-react (introspecting installed exports), express, cors.
4. package.json: Strict json.loads parsing (no blind single-quote replacement).
5. Reviewer Node: Structured errors output schema [{file, line, rule, message}].
6. Regression tests for audit corruptions:
   - await outside async / illegal await vs valid async/await
   - .data.map and defensive array chaining
   - string .slice (preserving string slicing from array healer corruption)
   - comments (inline // and multi-line /* */ with quotes and braces)
"""

import os
import sys
import pytest

# Ensure backend root is on Python sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators import (
    validate_syntax,
    validate_route_contract,
    validate_import_allowlist,
    validate_package_json,
    validate_all,
    normalize_route_path,
    get_installed_lucide_exports
)
from agents.reviewer import reviewer_node


# ==============================================================================
# 1. JS SYNTAX CHECK TESTS (node --check & esbuild)
# ==============================================================================

def test_syntax_valid_server_js():
    files = {
        "/server.js": "const express = require('express');\nconst app = express();\napp.listen(5000);\n"
    }
    errors = validate_syntax(files)
    assert errors == []


def test_syntax_invalid_server_js():
    # server.js with broken syntax
    files = {
        "/server.js": "const express = require('express');\nconst app = ;\napp.listen(5000);"
    }
    errors = validate_syntax(files)
    assert len(errors) == 1
    err = errors[0]
    assert err["file"] == "/server.js"
    assert err["rule"] == "syntax"
    assert err["line"] == 2
    assert "SyntaxError" in err["message"] or "Unexpected token" in err["message"]


def test_syntax_valid_app_js_esbuild():
    files = {
        "/App.js": (
            "import React, { useState } from 'react';\n"
            "export default function App() {\n"
            "  const [count, setCount] = useState(0);\n"
            "  return <div className=\"p-4\"><button onClick={() => setCount(c => c + 1)}>Count: {count}</button></div>;\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert errors == []


def test_syntax_invalid_app_js_esbuild():
    # JSX with mismatched closing tags
    files = {
        "/App.js": (
            "import React from 'react';\n"
            "export default function App() {\n"
            "  return <div><span>Mismatched</div>;\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert len(errors) >= 1
    assert any(e["file"] == "/App.js" and e["rule"] == "syntax" for e in errors)
    first = errors[0]
    assert first["line"] == 3


def test_syntax_valid_api_js_esbuild():
    files = {
        "/services/api.js": (
            "export async function fetchItems() {\n"
            "  const res = await fetch('http://localhost:5000/api/items');\n"
            "  return res.json();\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert errors == []


# ==============================================================================
# 2. AUDIT CORRUPTION REGRESSION TESTS
# ==============================================================================

def test_regression_illegal_await_syntax():
    """Regression: top-level or synchronous function with invalid await is caught."""
    files = {
        "/App.js": (
            "function syncFunction() {\n"
            "  const res = await fetch('/api/data');\n"
            "  return res;\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert len(errors) >= 1
    assert any("await" in e["message"].lower() for e in errors)


def test_regression_valid_await_inside_async():
    """Regression: valid async/await expressions are preserved and pass syntax checking."""
    files = {
        "/services/api.js": (
            "export const getTodos = async () => {\n"
            "  try {\n"
            "    const response = await fetch('/api/todos');\n"
            "    if (!response.ok) throw new Error('Network error');\n"
            "    return await response.json();\n"
            "  } catch (err) {\n"
            "    return [];\n"
            "  }\n"
            "};\n"
        )
    }
    errors = validate_syntax(files)
    assert errors == []


def test_regression_data_map_syntax():
    """Regression: (res.data || []).map(...) and chained array calls pass without syntax corruption."""
    files = {
        "/App.js": (
            "import React from 'react';\n"
            "export default function App({ result }) {\n"
            "  const list = (result?.data || []).map((item, idx) => (\n"
            "    <li key={idx}>{item.title}</li>\n"
            "  ));\n"
            "  return <ul>{list}</ul>;\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert errors == []


def test_regression_string_slice_integrity():
    """Regression: string .slice() calls (e.g. auth header token stripping) must NOT be mangled or corrupted."""
    files = {
        "/server.js": (
            "const express = require('express');\n"
            "const app = express();\n"
            "app.use((req, res, next) => {\n"
            "  const header = req.headers['authorization'] || '';\n"
            "  const token = header.startsWith('Bearer ') ? header.slice(7) : '';\n"
            "  const prefix = 'sample_string'.slice(0, 6);\n"
            "  req.token = token;\n"
            "  req.prefix = prefix;\n"
            "  next();\n"
            "});\n"
            "app.listen(5000);\n"
        )
    }
    errors = validate_syntax(files)
    assert errors == []


def test_regression_complex_comments():
    """Regression: single-line and multi-line comments containing quotes, brackets, and code snippets pass cleanly."""
    files = {
        "/App.js": (
            "import React from 'react';\n"
            "// Single line comment: Don't break on quotes or { brackets }\n"
            "/*\n"
            " * Multi-line JSDoc comment\n"
            " * const broken = 'test';\n"
            " * <div>nested JSX comment</div>\n"
            " */\n"
            "export default function App() {\n"
            "  return <div>Comments safe</div>;\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert errors == []


def test_regression_unclosed_block_comment_detected():
    """Regression: unclosed block comment is identified as syntax error with exact line."""
    files = {
        "/App.js": (
            "import React from 'react';\n"
            "/* unclosed comment start\n"
            "export default function App() {\n"
            "  return <div>Test</div>;\n"
            "}\n"
        )
    }
    errors = validate_syntax(files)
    assert len(errors) >= 1
    assert any(e["rule"] == "syntax" for e in errors)


# ==============================================================================
# 3. ROUTE CONTRACT CHECK TESTS
# ==============================================================================

def test_route_contract_all_routes_matched():
    server_code = (
        "const express = require('express');\n"
        "const app = express();\n"
        "app.get('/api/items', (req, res) => res.json([]));\n"
        "app.post('/api/items', (req, res) => res.json({}));\n"
        "app.delete('/api/items/:id', (req, res) => res.json({ success: true }));\n"
        "app.listen(5000);\n"
    )
    api_spec = [
        {"method": "GET", "path": "/api/items"},
        {"method": "POST", "path": "/api/items"},
        {"method": "DELETE", "path": "/api/items/:id"}
    ]
    files = {
        "/server.js": server_code,
        "/services/api.js": "export const getItems = () => fetch('/api/items');"
    }
    errors = validate_route_contract(files, api_spec)
    assert errors == []


def test_route_contract_missing_api_spec_route():
    server_code = (
        "const express = require('express');\n"
        "const app = express();\n"
        "app.get('/api/items', (req, res) => res.json([]));\n"
        "app.listen(5000);\n"
    )
    api_spec = [
        {"method": "GET", "path": "/api/items"},
        {"method": "DELETE", "path": "/api/items/:id"}
    ]
    files = {"/server.js": server_code}
    errors = validate_route_contract(files, api_spec)
    assert len(errors) == 1
    err = errors[0]
    assert err["rule"] == "route-contract"
    assert "DELETE /api/items/:id" in err["message"]


def test_route_contract_param_normalization():
    # Server uses :todoId, spec uses :id
    server_code = (
        "const express = require('express');\n"
        "const app = express();\n"
        "app.put('/api/todos/:todoId', (req, res) => res.json({}));\n"
        "app.listen(5000);\n"
    )
    api_spec = [{"method": "PUT", "path": "/api/todos/:id"}]
    files = {"/server.js": server_code}
    errors = validate_route_contract(files, api_spec)
    assert errors == []


def test_route_contract_unmapped_client_url():
    server_code = (
        "const express = require('express');\n"
        "const app = express();\n"
        "app.get('/api/items', (req, res) => res.json([]));\n"
        "app.listen(5000);\n"
    )
    api_client_code = (
        "export const getItems = () => fetch('/api/items');\n"
        "export const getSecret = () => fetch('http://localhost:5000/api/unmapped-endpoint');\n"
    )
    files = {
        "/server.js": server_code,
        "/services/api.js": api_client_code
    }
    errors = validate_route_contract(files, [])
    assert len(errors) == 1
    err = errors[0]
    assert err["file"] == "/services/api.js"
    assert err["line"] == 2
    assert err["rule"] == "route-contract"
    assert "/api/unmapped-endpoint" in err["message"]


# ==============================================================================
# 4. IMPORT ALLOWLIST TESTS
# ==============================================================================

def test_import_allowlist_valid_frontend():
    files = {
        "/App.js": (
            "import React, { useState, useEffect } from 'react';\n"
            "import { createRoot } from 'react-dom/client';\n"
            "import { Plus, Trash2, Search, Check } from 'lucide-react';\n"
            "import './styles.css';\n"
            "import api from './services/api';\n"
        )
    }
    errors = validate_import_allowlist(files)
    assert errors == []


def test_import_allowlist_unapproved_frontend_package():
    files = {
        "/App.js": (
            "import React from 'react';\n"
            "import axios from 'axios';\n"
            "import _ from 'lodash';\n"
        )
    }
    errors = validate_import_allowlist(files)
    assert len(errors) == 2
    pkgs = [e["message"] for e in errors]
    assert any("axios" in p for p in pkgs)
    assert any("lodash" in p for p in pkgs)
    assert all(e["rule"] == "import-allowlist" for e in errors)


def test_import_allowlist_invalid_lucide_icon():
    files = {
        "/App.js": (
            "import React from 'react';\n"
            "import { Plus, TotallyFakeIconThatDoesNotExistXYZ } from 'lucide-react';\n"
        )
    }
    errors = validate_import_allowlist(files)
    assert len(errors) == 1
    err = errors[0]
    assert err["rule"] == "import-allowlist"
    assert "TotallyFakeIconThatDoesNotExistXYZ" in err["message"]


def test_import_allowlist_backend_allowed_and_unapproved():
    files = {
        "/server.js": (
            "const express = require('express');\n"
            "const cors = require('cors');\n"
            "const path = require('path');\n"
            "const mongoose = require('mongoose');\n"
        )
    }
    errors = validate_import_allowlist(files)
    assert len(errors) == 1
    err = errors[0]
    assert err["rule"] == "import-allowlist"
    assert "mongoose" in err["message"]


# ==============================================================================
# 5. PACKAGE.JSON VALIDATION TESTS
# ==============================================================================

def test_package_json_valid():
    files = {
        "/package.json": '{\n  "name": "client",\n  "dependencies": {\n    "lucide-react": "^1.0.0"\n  }\n}'
    }
    errors = validate_package_json(files)
    assert errors == []


def test_package_json_single_quotes_fails_strict():
    """Verify strict parsing without blind quote replacement."""
    files = {
        "/package.json": "{ 'name': 'client', 'dependencies': { 'lucide-react': 'latest' } }"
    }
    errors = validate_package_json(files)
    assert len(errors) == 1
    err = errors[0]
    assert err["file"] == "/package.json"
    assert err["rule"] == "package-json"
    assert "Invalid JSON" in err["message"]


def test_package_json_malformed_syntax():
    files = {
        "/server/package.json": '{\n  "name": "server",\n  "dependencies": {\n}'
    }
    errors = validate_package_json(files)
    assert len(errors) == 1
    assert errors[0]["rule"] == "package-json"


# ==============================================================================
# 6. REVIEWER NODE INTEGRATION & STRUCTURED ERRORS
# ==============================================================================

def test_reviewer_node_returns_structured_errors_list():
    state = {
        "files": {
            "/server.js": "const app = ;\napp.listen(5000);",
            "/App.js": "import React from 'react';\nimport axios from 'axios';\nexport default function App() { return <div>Test</div>; }",
            "/package.json": "{ 'invalid': 'json' }"
        },
        "api_spec": [{"method": "GET", "path": "/api/items"}],
        "attempt": 1
    }
    result = reviewer_node(state)
    errors = result["errors"]
    assert isinstance(errors, list)
    assert len(errors) >= 3

    # Verify each structured error adheres to the schema: {file, line, rule, message}
    for err in errors:
        assert "file" in err
        assert "line" in err
        assert isinstance(err["line"], int)
        assert "rule" in err
        assert err["rule"] in {"syntax", "route-contract", "import-allowlist", "package-json"}
        assert "message" in err
