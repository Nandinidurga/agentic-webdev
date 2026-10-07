"""
Unit Test Suite for Agentic IDE Backend
Tests reviewer auto-healer, defensive guards, state graph conditions, and sanitizers.
Run: python test_suite.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.reviewer import heal_frontend_code, reviewer_node
from agents.coder import unescape_json_string

def should_continue_sim(state):
    errors = state.get("errors")
    iteration = state.get("iteration", 0)
    if errors and iteration < 3:
        return "coder"
    return "__end__"

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

    def test_reviewer_passes_valid_code(self):
        valid_state = {
            "prompt": "Test app",
            "iteration": 0,
            "api_spec": [{"method": "GET", "path": "/api/items"}],
            "files": {
                "/server.js": "const express = require('express'); const cors = require('cors'); const app = express(); app.use(cors()); app.get('/api/items', (req,res) => res.json([])); app.listen(5000);",
                "/App.js": "import React, { useState } from 'react'; export default function App() { const [items, setItems] = useState([]); return <div>{items.map(x => x)}</div>; }",
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
        self.assertEqual(result["iteration"], 1)
        # Verify package.json single quotes were healed to double quotes
        self.assertIn('"', result["files"]["/package.json"])

    def test_reviewer_detects_missing_server(self):
        invalid_state = {
            "files": {
                "/App.js": "export default function App() { return <div>Hello</div>; }"
            },
            "iteration": 1
        }
        result = reviewer_node(invalid_state)
        self.assertIn("Missing `/server.js`", result["errors"])
        self.assertEqual(result["iteration"], 2)

    def test_should_continue_loop_bounds(self):
        # Iteration 1 with errors -> should continue to coder
        state1 = {"errors": "Missing route", "iteration": 1}
        self.assertEqual(should_continue_sim(state1), "coder")

        # Iteration 3 with errors -> should stop (__end__) to avoid infinite loop
        state2 = {"errors": "Missing route", "iteration": 3}
        self.assertEqual(should_continue_sim(state2), "__end__")

        # No errors -> should stop (__end__)
        state3 = {"errors": "", "iteration": 1}
        self.assertEqual(should_continue_sim(state3), "__end__")

class TestCoderSanitizer(unittest.TestCase):
    def test_unescape_json_string(self):
        raw = "Line 1\\nLine 2\\tIndented with \\\"quotes\\\" and \\\\ backslash"
        expected = 'Line 1\nLine 2\tIndented with "quotes" and \\ backslash'
        self.assertEqual(unescape_json_string(raw), expected)

if __name__ == "__main__":
    unittest.main()
