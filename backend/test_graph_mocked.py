"""
test_graph_mocked.py - Mocked-LLM end-to-end integration tests for:
1. The complete LangGraph workflow (Orchestrator -> Knowledge -> Coder -> Reviewer).
2. The FastAPI /generate HTTP endpoint.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import create_graph
from main import app

# Reusable mock LLM output definitions
MOCK_ORCHESTRATOR_OUTPUT = """# Architectural Plan
Build a high-performance Item Directory application with Node.js/Express and React.

```json:api_spec
[
  {
    "method": "GET",
    "path": "/api/items",
    "description": "List all items"
  }
]
```
"""

MOCK_BACKEND_OUTPUT = """=== FILE: /server.js ===
const express = require('express');
const cors = require('cors');
const app = express();
app.use(cors());
app.use(express.json());
app.get('/api/items', (req, res) => res.json([]));
app.get('/api/health', (req, res) => res.json({ status: 'ok', uptime: process.uptime() }));
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => console.log('Server running on port ' + PORT));
=== END FILE ===

=== FILE: /server/package.json ===
{
  "name": "server",
  "dependencies": {
    "express": "4.19.2",
    "cors": "2.8.5"
  },
  "scripts": {
    "start": "node server.js"
  }
}
=== END FILE ===
"""

MOCK_FRONTEND_OUTPUT = """=== FILE: /App.js ===
import React, { useState } from 'react';
import { CheckCircle } from 'lucide-react';
import './styles.css';
import './services/api.js';

export default function App() {
  const [items, setItems] = useState([]);
  return (
    <div>
      <CheckCircle />
      <h1>Mocked Full-Stack Test</h1>
    </div>
  );
}
=== END FILE ===

=== FILE: /services/api.js ===
export const getItems = async () => {
  return fetch('http://localhost:5000/api/items').then(r => r.json());
};
=== END FILE ===

=== FILE: /styles.css ===
body {
  margin: 0;
  font-family: sans-serif;
}
=== END FILE ===

=== FILE: /package.json ===
{
  "dependencies": {
    "react": "18.3.1",
    "react-dom": "18.3.1",
    "lucide-react": "0.453.0"
  }
}
=== END FILE ===
"""


class MockLLM:
    """Mock LLM returning appropriate responses based on prompt role."""
    def invoke(self, messages, **kwargs):
        content = " ".join([m.content for m in messages if hasattr(m, "content")])
        resp = MagicMock()
        if "Lead Architect & Orchestrator" in content:
            resp.content = MOCK_ORCHESTRATOR_OUTPUT
        elif "Lead Backend Engineer" in content:
            resp.content = MOCK_BACKEND_OUTPUT
        elif "Lead Frontend Engineer" in content:
            resp.content = MOCK_FRONTEND_OUTPUT
        else:
            resp.content = "Mock response"
        return resp


@pytest.fixture
def mock_get_llm():
    with patch("agents.orchestrator.get_llm", return_value=MockLLM()), \
         patch("agents.coder.get_llm", return_value=MockLLM()), \
         patch("agents.knowledge.get_vectorstore", return_value=None):
        yield


def test_full_langgraph_workflow_mocked(mock_get_llm):
    """
    Verifies that the entire LangGraph workflow compiles and runs end-to-end:
    Orchestrator -> Knowledge -> Coder -> Reviewer -> END.
    """
    graph = create_graph()
    initial_state = {
        "prompt": "Build a responsive items directory app",
        "attempt": 0
    }

    result = graph.invoke(initial_state)

    # Assert plan & api_spec were generated
    assert result.get("plan") is not None
    assert len(result.get("api_spec", [])) == 1
    assert result["api_spec"][0]["path"] == "/api/items"

    # Assert coder generated complete file set
    files = result.get("files", {})
    assert "/server.js" in files
    assert "/server/package.json" in files
    assert "/App.js" in files
    assert "/services/api.js" in files
    assert "/styles.css" in files
    assert "/package.json" in files

    # Assert reviewer validated successfully with 0 errors
    assert result.get("errors") == []
    assert result.get("attempt") == 1


def test_fastapi_generate_endpoint_mocked(mock_get_llm):
    """
    Verifies the FastAPI POST /generate endpoint returns HTTP 200
    with status 'success' and complete payload when LLM is mocked.
    """
    client = TestClient(app)
    response = client.post(
        "/generate",
        json={"prompt": "Build an item directory web application"}
    )

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "success"
    assert "Workflow completed" in data["message"]
    assert "/server.js" in data["files"]
    assert "/App.js" in data["files"]
    assert len(data["api_spec"]) == 1
    assert data["errors"] == []
    assert data["attempt"] == 1
