"""
test_coder_retry.py - Unit tests for coder retry mechanics, error partitioning,
targeted file re-request, shared cancellation token, and per-attempt timeout.
"""

import os
import sys
import threading
import pytest
from unittest.mock import MagicMock, patch

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.coder import (
    is_backend_error,
    extract_files_from_errors,
    format_structured_errors,
    coder_node,
    REQUIRED_BACKEND_FILES,
    REQUIRED_FRONTEND_FILES
)


def test_is_backend_error_classification():
    # Route contract error -> backend
    assert is_backend_error({"file": "/server.js", "line": 5, "rule": "route-contract", "message": "Missing route"})
    assert is_backend_error({"file": "general", "line": 1, "rule": "route-contract", "message": "Missing GET /api/items"})

    # Server syntax / file -> backend
    assert is_backend_error({"file": "/server.js", "line": 1, "rule": "syntax", "message": "Unexpected token"})
    assert is_backend_error({"file": "/server/package.json", "line": 2, "rule": "package-json", "message": "Invalid JSON"})

    # Frontend syntax / imports -> NOT backend (frontend)
    assert not is_backend_error({"file": "/App.js", "line": 10, "rule": "syntax", "message": "Missing semicolon"})
    assert not is_backend_error({"file": "/services/api.js", "line": 3, "rule": "syntax", "message": "Unexpected token"})
    assert not is_backend_error({"file": "/App.js", "line": 2, "rule": "import-allowlist", "message": "Invalid icon"})
    assert not is_backend_error({"file": "/package.json", "line": 1, "rule": "package-json", "message": "Invalid JSON"})


def test_extract_files_from_errors():
    backend_errors = [
        {"file": "/server.js", "line": 10, "rule": "syntax", "message": "Syntax error"},
        {"file": "general", "line": 1, "rule": "route-contract", "message": "Missing route"}
    ]
    files = extract_files_from_errors(backend_errors, REQUIRED_BACKEND_FILES)
    assert files == ["/server.js"]

    frontend_errors = [
        {"file": "/App.js", "line": 20, "rule": "syntax", "message": "Syntax error"},
        {"file": "/package.json", "line": 1, "rule": "package-json", "message": "Invalid JSON"}
    ]
    fe_files = extract_files_from_errors(frontend_errors, REQUIRED_FRONTEND_FILES)
    assert "/App.js" in fe_files
    assert "/package.json" in fe_files


def test_format_structured_errors():
    errors = [
        {"file": "/server.js", "line": 15, "rule": "route-contract", "message": "Missing endpoint"}
    ]
    formatted = format_structured_errors(errors)
    assert "[/server.js:15] (route-contract) Missing endpoint" in formatted


def test_coder_retry_only_runs_backend_when_only_backend_errors():
    """When only backend errors are reported, frontend is skipped and previous files retained."""
    prev_files = {
        "/server.js": "const app = express();",
        "/server/package.json": '{"name": "server"}',
        "/App.js": "export default function App() { return <div>Cached UI</div>; }",
        "/services/api.js": "export const api = {};",
        "/package.json": '{"name": "client"}',
        "/styles.css": "body { margin: 0; }"
    }

    state = {
        "files": prev_files,
        "backend_files": {"/server.js": prev_files["/server.js"]},
        "frontend_files": {k: v for k, v in prev_files.items() if k != "/server.js" and k != "/server/package.json"},
        "errors": [{"file": "/server.js", "line": 1, "rule": "route-contract", "message": "Missing route"}],
        "attempt": 1,
        "plan": "Plan",
        "api_spec": [{"method": "GET", "path": "/api/items"}]
    }

    mock_llm = MagicMock()
    # Mock LLM returns fixed /server.js
    mock_resp = MagicMock()
    mock_resp.content = """=== FILE: /server.js ===
const express = require('express');
const app = express();
app.get('/api/items', (req, res) => res.json([]));
app.listen(5000);
=== END FILE ==="""
    mock_llm.invoke.return_value = mock_resp

    with patch("agents.coder.get_llm", return_value=mock_llm):
        result = coder_node(state)

    # Backend was updated
    assert "/api/items" in result["files"]["/server.js"]
    # Frontend was untouched and retained intact from previous files
    assert "Cached UI" in result["files"]["/App.js"]
    assert result["attempt"] == 2

    # LLM was invoked only once (for backend), NOT twice!
    assert mock_llm.invoke.call_count == 1
    # Verify the backend prompt received only backend errors and previous files
    call_args = mock_llm.invoke.call_args[0][0]
    prompt_text = " ".join([m.content for m in call_args])
    assert "route-contract" in prompt_text
    assert "Requested Files to Update: /server.js" in prompt_text


def test_coder_retry_only_runs_frontend_when_only_frontend_errors():
    """When only frontend errors are reported, backend is skipped and previous files retained."""
    prev_files = {
        "/server.js": "const app = express(); app.get('/api/items', ...);",
        "/server/package.json": '{"name": "server"}',
        "/App.js": "const [items, setItems] = useState();",
        "/services/api.js": "export const api = {};",
        "/package.json": '{"name": "client"}',
        "/styles.css": "body { margin: 0; }"
    }

    state = {
        "files": prev_files,
        "backend_files": {"/server.js": prev_files["/server.js"]},
        "frontend_files": {k: v for k, v in prev_files.items() if "server" not in k},
        "errors": [{"file": "/App.js", "line": 1, "rule": "syntax", "message": "Syntax error in App.js"}],
        "attempt": 1,
        "plan": "Plan",
        "api_spec": [{"method": "GET", "path": "/api/items"}]
    }

    mock_llm = MagicMock()
    mock_resp = MagicMock()
    mock_resp.content = """=== FILE: /App.js ===
import React, { useState } from 'react';
export default function App() {
  const [items, setItems] = useState([]);
  return <div>Fixed App</div>;
}
=== END FILE ==="""
    mock_llm.invoke.return_value = mock_resp

    with patch("agents.coder.get_llm", return_value=mock_llm):
        result = coder_node(state)

    # Frontend was updated
    assert "Fixed App" in result["files"]["/App.js"]
    # Backend was untouched and retained from previous files
    assert "app.get('/api/items', ...)" in result["files"]["/server.js"]
    assert result["attempt"] == 2

    # LLM was invoked only once (for frontend)
    assert mock_llm.invoke.call_count == 1
    call_args = mock_llm.invoke.call_args[0][0]
    prompt_text = " ".join([m.content for m in call_args])
    assert "Syntax error in App.js" in prompt_text
    assert "Requested Files to Update: /App.js" in prompt_text


def test_shared_cancel_event_aborts_coder_immediately():
    """A set cancel event must immediately abort coder_node and raise TimeoutError."""
    cancel_event = threading.Event()
    cancel_event.set()

    state = {
        "cancel_event": cancel_event,
        "attempt": 0,
        "files": {},
        "errors": []
    }

    with pytest.raises(TimeoutError, match="shared cancel flag is active"):
        coder_node(state)
