"""
test_export_scaffold.py - Integration test for ExportButton project scaffolding.

Tests:
1. Generates the known-good client scaffold (package.json with react, react-dom, vite, start script, index.html, src/main.jsx).
2. Merges generated files into the scaffold.
3. Strictly ignores the model's client package.json and enforces pinned dependency versions.
4. Unzips the generated export zip.
5. Runs `node --check` on server.js.
6. Runs `npm install` on the unzipped server directory.
"""

import os
import sys
import subprocess
import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_export_scaffold_unzip_and_npm_install():
    """
    Executes scripts/test_export_scaffold.mjs which:
    - Packs the full-stack bundle using ExportButton's exportScaffold module
    - Writes the zip archive to disk
    - Unzips the archive
    - Verifies pinned versions and that model's package.json is ignored
    - Verifies index.html and src/main.jsx
    - Runs `node --check server/server.js`
    - Runs `npm install` on server
    """
    script_path = os.path.join(ROOT_DIR, "scripts", "test_export_scaffold.mjs")
    assert os.path.exists(script_path), f"Script not found: {script_path}"

    result = subprocess.run(
        ["node", "--no-warnings", script_path],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

    assert result.returncode == 0
    assert "ALL EXPORT SCAFFOLD INTEGRATION TESTS PASSED" in result.stdout
