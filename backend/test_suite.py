"""
Unit Test Suite for Agentic IDE Backend
Tests reviewer auto-healer, defensive guards, real LangGraph should_continue loop semantics, and sanitizers.
Run: python test_suite.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.reviewer import heal_frontend_code, reviewer_node
from agents.coder import unescape_json_string
from graph import should_continue, END

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
                "/package.json": "{ 'dependencies': { 'lucide-react': 'latest' } }"
            },
            "backend_files": {
                "/server.js": "..."
            },
            "frontend_files": {
                "/App.js": "..."
            }
        }
        result = reviewer_node(valid_state)
        self.assertEqual(result["errors"], "")
        self.assertEqual(result["attempt"], 1)
        # Verify package.json single quotes were healed to double quotes
        self.assertIn('"', result["files"]["/package.json"])

    def test_reviewer_detects_missing_server(self):
        invalid_state = {
            "files": {
                "/App.js": "export default function App() { return <div>Hello</div>; }"
            },
            "attempt": 1
        }
        result = reviewer_node(invalid_state)
        self.assertIn("Missing `/server.js`", result["errors"])
        self.assertEqual(result["attempt"], 1)

class TestRealGraphLoopSemantics(unittest.TestCase):
    def test_real_should_continue_default_max_attempts(self):
        if "MAX_ATTEMPTS" in os.environ:
            del os.environ["MAX_ATTEMPTS"]

        # Attempt 1 with errors -> routes back to coder
        state1 = {"errors": "Syntax error in server.js", "attempt": 1}
        self.assertEqual(should_continue(state1), "coder")

        # Attempt 2 with errors -> routes back to coder
        state2 = {"errors": "Syntax error in server.js", "attempt": 2}
        self.assertEqual(should_continue(state2), "coder")

        # Attempt 3 (reached max 3 attempts) -> routes to END
        state3 = {"errors": "Syntax error in server.js", "attempt": 3}
        self.assertEqual(should_continue(state3), END)

        # No errors -> always routes to END
        state_no_err = {"errors": "", "attempt": 1}
        self.assertEqual(should_continue(state_no_err), END)

    def test_real_should_continue_custom_max_attempts_from_env(self):
        os.environ["MAX_ATTEMPTS"] = "5"
        try:
            state = {"errors": "Unresolved route", "attempt": 4}
            self.assertEqual(should_continue(state), "coder")

            state_max = {"errors": "Unresolved route", "attempt": 5}
            self.assertEqual(should_continue(state_max), END)
        finally:
            if "MAX_ATTEMPTS" in os.environ:
                del os.environ["MAX_ATTEMPTS"]

class TestCoderSanitizer(unittest.TestCase):
    def test_unescape_json_string(self):
        raw = "Line 1\\nLine 2\\tIndented with \\\"quotes\\\" and \\\\ backslash"
        expected = 'Line 1\nLine 2\tIndented with "quotes" and \\ backslash'
        self.assertEqual(unescape_json_string(raw), expected)

if __name__ == "__main__":
    unittest.main()
