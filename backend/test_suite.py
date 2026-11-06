"""
Unit Test Suite for Agentic IDE Backend
Tests reviewer auto-healer, defensive guards, real LangGraph should_continue loop semantics,
token-budgeted RAG context packing, selective ingestion heuristics, and delimited file parsing.
Run: python backend/test_suite.py
"""

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.reviewer import heal_frontend_code, reviewer_node
from agents.coder import build_budgeted_context
from file_parser import parse_delimited_files
from graph import should_continue, END
from rag_ingest import should_skip_path, get_deterministic_id
from ingest_backend_docs import get_deterministic_backend_id
import agents.knowledge as knowledge_mod

class TestReviewerAutoHealer(unittest.TestCase):
    def test_heal_uninitialized_state(self):
        input_code = "const [items, setItems] = useState();\nconst [data, setData] = useState(undefined);"
        healed = heal_frontend_code(input_code)
        self.assertIn("useState([])", healed)
        self.assertNotIn("useState()", healed)
        self.assertNotIn("useState(undefined)", healed)

    def test_heal_defensive_array_map(self):
        input_code = "return items.map(item => <div>{item.name}</div>);"
        healed = heal_frontend_code(input_code)
        self.assertIn("(items || []).map(", healed)

    def test_heal_defensive_to_fixed(self):
        input_code = "<span>{expense.amount.toFixed(2)}</span>"
        healed = heal_frontend_code(input_code)
        self.assertIn("(Number(expense.amount) || 0).toFixed(2)", healed)

    def test_heal_regex_env_flag_behavior(self):
        # 1. Default (HEAL_REGEX unset / "0"): frontend code is NOT regex-healed
        os.environ["HEAL_REGEX"] = "0"
        raw_code = "const [items, setItems] = useState(); return items.map(x => x);"
        state = {
            "files": {
                "/server.js": "const express = require('express'); const app = express(); app.listen(5000);",
                "/App.js": raw_code
            },
            "attempt": 1
        }
        res_default = reviewer_node(state)
        self.assertEqual(res_default["files"]["/App.js"], raw_code)

        # 2. When HEAL_REGEX="1": frontend code is regex-healed
        os.environ["HEAL_REGEX"] = "1"
        res_healed = reviewer_node(state)
        self.assertIn("useState([])", res_healed["files"]["/App.js"])
        self.assertIn("(items || []).map(", res_healed["files"]["/App.js"])
        # Reset env
        os.environ["HEAL_REGEX"] = "0"

    def test_reviewer_passes_valid_code(self):
        valid_state = {
            "prompt": "Test app",
            "attempt": 1,
            "api_spec": [{"method": "GET", "path": "/api/items"}],
            "files": {
                "/server.js": "const express = require('express'); const cors = require('cors'); const app = express(); app.use(cors()); app.get('/api/items', (req,res) => res.json([])); app.listen(5000);",
                "/App.js": "import React, { useState } from 'react'; export default function App() { const [items, setItems] = useState([]); return <div>{(items || []).map(x => x)}</div>; }",
                "/services/api.js": "export const api = { get: async () => [] }; export default api;",
                "/package.json": '{\n  "dependencies": {\n    "lucide-react": "latest"\n  }\n}'
            },
            "backend_files": {
                "/server.js": "..."
            },
            "frontend_files": {
                "/App.js": "..."
            }
        }
        result = reviewer_node(valid_state)
        # Empty structured errors list means validation passed completely
        self.assertEqual(result["errors"], [])
        self.assertEqual(result["attempt"], 1)

    def test_reviewer_detects_missing_server(self):
        invalid_state = {
            "files": {
                "/App.js": "export default function App() { return <div>Hello</div>; }"
            },
            "attempt": 1
        }
        result = reviewer_node(invalid_state)
        self.assertTrue(any("Missing `/server.js`" in e["message"] for e in result["errors"]))
        self.assertEqual(result["attempt"], 1)

class TestRealGraphLoopSemantics(unittest.TestCase):
    def test_real_should_continue_default_max_attempts(self):
        if "MAX_ATTEMPTS" in os.environ:
            del os.environ["MAX_ATTEMPTS"]

        # Attempt 1 with errors (string or structured error list) -> routes back to coder
        state1 = {"errors": [{"file": "/server.js", "line": 1, "rule": "syntax", "message": "Syntax error"}], "attempt": 1}
        self.assertEqual(should_continue(state1), "coder")

        # Attempt 2 with errors -> routes back to coder
        state2 = {"errors": [{"file": "/server.js", "line": 1, "rule": "syntax", "message": "Syntax error"}], "attempt": 2}
        self.assertEqual(should_continue(state2), "coder")

        # Attempt 3 (reached max 3 attempts) -> routes to END
        state3 = {"errors": [{"file": "/server.js", "line": 1, "rule": "syntax", "message": "Syntax error"}], "attempt": 3}
        self.assertEqual(should_continue(state3), END)

        # No errors -> always routes to END
        state_no_err = {"errors": [], "attempt": 1}
        self.assertEqual(should_continue(state_no_err), END)

    def test_real_should_continue_custom_max_attempts_from_env(self):
        os.environ["MAX_ATTEMPTS"] = "5"
        try:
            state = {"errors": [{"file": "/server.js", "line": 1, "rule": "route-contract", "message": "Unresolved route"}], "attempt": 4}
            self.assertEqual(should_continue(state), "coder")

            state_max = {"errors": [{"file": "/server.js", "line": 1, "rule": "route-contract", "message": "Unresolved route"}], "attempt": 5}
            self.assertEqual(should_continue(state_max), END)
        finally:
            if "MAX_ATTEMPTS" in os.environ:
                del os.environ["MAX_ATTEMPTS"]

class TestDelimitedBlockParser(unittest.TestCase):
    def test_parse_delimited_files_basic(self):
        raw = """=== FILE: /server.js ===
const express = require('express');
const app = express();
app.listen(5000);
=== END FILE ===

=== FILE: /package.json ===
{
  "name": "app"
}
=== END FILE ==="""
        files = parse_delimited_files(raw)
        self.assertIn("/server.js", files)
        self.assertIn("/package.json", files)
        self.assertIn("express()", files["/server.js"])
        self.assertIn('"name": "app"', files["/package.json"])

    def test_parse_delimited_files_with_code_fences(self):
        raw = """=== FILE: /App.js ===
```jsx
export default function App() {
  return <div>Test</div>;
}
```
=== END FILE ==="""
        files = parse_delimited_files(raw)
        self.assertIn("/App.js", files)
        self.assertFalse(files["/App.js"].startswith("```"))
        self.assertIn("export default function App()", files["/App.js"])

    def test_parse_delimited_files_implicit_termination(self):
        # File 1 does not have explicit === END FILE ===
        raw = """=== FILE: /server.js ===
const port = 5000;
=== FILE: /services/api.js ===
export const api = {};
=== END FILE ==="""
        files = parse_delimited_files(raw)
        self.assertEqual(files["/server.js"], "const port = 5000;")
        self.assertEqual(files["/services/api.js"], "export const api = {};")

    def test_parse_delimited_files_readme_preserves_internal_code_fences(self):
        # A README with an unclosed code snippet at the bottom must NOT lose its trailing fence
        raw = """=== FILE: /README.md ===
# My Quickstart
```bash
npm start
```
=== END FILE ==="""
        files = parse_delimited_files(raw)
        self.assertIn("/README.md", files)
        self.assertTrue(files["/README.md"].endswith("```"))
        self.assertIn("npm start", files["/README.md"])

    def test_parse_delimited_files_wrapped_readme(self):
        # An entire README wrapped in an outer ```markdown envelope must unwrap cleanly
        raw = """=== FILE: /README.md ===
```markdown
# Outer Envelope
```bash
npm test
```
```
=== END FILE ==="""
        files = parse_delimited_files(raw)
        self.assertIn("/README.md", files)
        self.assertFalse(files["/README.md"].startswith("```markdown"))
        self.assertTrue(files["/README.md"].endswith("```"))
        self.assertIn("npm test", files["/README.md"])

    def test_token_budgeting_prioritizes_high_scoring_chunks(self):
        state = {
            "rag_chunks": [
                {"domain": "backend", "source": "low_score.md", "score": 0.45, "content": "LOW PRIORITY CHUNK " * 20},
                {"domain": "backend", "source": "high_score.md", "score": 0.95, "content": "HIGH PRIORITY CHUNK CONTENT"}
            ]
        }
        # Budget for only ~30 tokens (enough for high score, not enough for both)
        context = build_budgeted_context(state, max_tokens=30)
        self.assertIn("HIGH PRIORITY CHUNK CONTENT", context)
        self.assertNotIn("LOW PRIORITY CHUNK", context)

class TestRAGSelectiveIngestion(unittest.TestCase):
    def test_rag_ingest_path_filtering_and_deterministic_ids(self):
        self.assertTrue(should_skip_path("knowledge_base/react.dev/CONTRIBUTING.md"))
        self.assertTrue(should_skip_path("knowledge_base/react.dev/CODE_OF_CONDUCT.md"))
        self.assertTrue(should_skip_path("knowledge_base/react.dev/LICENSE.md"))
        self.assertTrue(should_skip_path("knowledge_base/react.dev/.claude/settings.json"))
        self.assertFalse(should_skip_path("knowledge_base/react.dev/src/content/reference/react/useState.md"))
        self.assertFalse(should_skip_path("knowledge_base/react.dev/src/content/learn/describing-the-ui.md"))

        # Verify 'eslint' is NOT in SKIP_PATTERNS
        self.assertFalse(should_skip_path("src/content/reference/react/eslint-plugin-react-hooks.md"))

        id1 = get_deterministic_id("reference/react/useState.md", 0)
        id2 = get_deterministic_id("reference/react/useState.md", 0)
        id3 = get_deterministic_id("reference/react/useState.md", 1)
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)

class TestBackendIdempotencyAndSingletonRetry(unittest.TestCase):
    def test_backend_deterministic_chunk_ids(self):
        id1 = get_deterministic_backend_id("express_api_guide.md", 0)
        id2 = get_deterministic_backend_id("express_api_guide.md", 0)
        id3 = get_deterministic_backend_id("express_api_guide.md", 1)
        self.assertEqual(id1, id2)
        self.assertNotEqual(id1, id3)

    def test_knowledge_singleton_retries_after_failure(self):
        # Reset module state
        knowledge_mod._VECTORSTORE = None

        # Simulate a transient failure
        with patch("os.path.exists", return_value=False):
            vs1 = knowledge_mod.get_vectorstore()
            self.assertIsNone(vs1)
            # Ensure _VECTORSTORE is not permanently poisoned
            self.assertIsNone(knowledge_mod._VECTORSTORE)

        # On subsequent call when directory exists, it attempts initialization (retries)
        with patch("os.path.exists", return_value=True),              patch("langchain_huggingface.HuggingFaceEmbeddings"),              patch("langchain_chroma.Chroma", return_value="mock_vectorstore"):
            vs2 = knowledge_mod.get_vectorstore()
            self.assertEqual(vs2, "mock_vectorstore")

        # Clean up
        knowledge_mod._VECTORSTORE = None


if __name__ == "__main__":
    unittest.main()
