"""
file_parser.py - High-reliability delimited block file parser for multi-file generation.

Format:
=== FILE: /path/to/file.ext ===
<raw unescaped code>
=== END FILE ===

Eliminates JSON escaping, quote-nesting failures, and regex heuristic salvage.
"""

import re
from typing import Dict

def parse_delimited_files(text: str) -> Dict[str, str]:
    """
    Parses files emitted in delimited block format:
    === FILE: /path/to/file ===
    ...file content...
    === END FILE ===

    Guarantees:
    - Preserves exact code syntax without JSON escape sequences.
    - Strips markdown code fences if model wrapped the file body.
    - Handles missing === END FILE === if next === FILE: block begins or EOF is reached.
    - Normalizes all output file keys to start with a leading slash.
    """
    files: Dict[str, str] = {}
    if not text or not isinstance(text, str):
        return files

    # Match === FILE: <path> === ... (terminated by next FILE block, END FILE, or EOF)
    pattern = re.compile(
        r'===\s*FILE:\s*([^\s=]+)\s*===\s*\r?\n(.*?)(?=(?:===\s*FILE:)|(?:===\s*END\s*FILE\s*===)|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    for match in pattern.finditer(text):
        raw_path = match.group(1).strip()
        body = match.group(2)

        # Strip markdown code fence wrappers if present
        body_stripped = body.strip()
        fence_match = re.match(r'^```[a-zA-Z0-9_\-\.]*\r?\n(.*)\r?\n```$', body_stripped, re.DOTALL)
        if fence_match:
            body = fence_match.group(1)
        else:
            body = re.sub(r'^```[a-zA-Z0-9_\-\.]*\r?\n', '', body)
            body = re.sub(r'\r?\n```\s*$', '', body)

        norm_path = raw_path if raw_path.startswith('/') else f"/{raw_path}"
        files[norm_path] = body.strip()

    return files
