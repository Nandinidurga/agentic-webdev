"""
file_parser.py - High-reliability delimited block file parser for multi-file generation.

Format:
=== FILE: /path/to/file.ext ===
<raw unescaped code>
=== END FILE ===

Eliminates JSON escaping, quote-nesting failures, and regex heuristic salvage.
Includes Markdown-aware fence unwrapping that preserves inner code blocks in README files.
"""

import re
from typing import Dict


def strip_markdown_fences(body: str, is_markdown: bool = False) -> str:
    """
    Strips markdown code fence wrappers (```...```) if the model wrapped the emitted file.
    
    For Markdown files (e.g. /README.md):
    - Carefully checks if the document itself was wrapped in an outer envelope (e.g. ```markdown ... ```).
    - NEVER blindly strips trailing fences (```) from markdown files when they belong to
      legitimate inner code blocks at the end of the document.
    """
    body_stripped = body.strip()
    if not body_stripped:
        return body

    lines = body_stripped.splitlines()
    if len(lines) < 2:
        return body

    first_line = lines[0].strip()
    last_line = lines[-1].strip()

    if is_markdown:
        # If the whole markdown document was wrapped in an outer fence envelope:
        # e.g., ```markdown \n # Title \n ```bash \n npm start \n ``` \n ```
        if first_line.startswith("```") and last_line == "```":
            # Count the code fence markers in the middle lines
            middle_lines = lines[1:-1]
            middle_fences = sum(1 for line in middle_lines if line.strip().startswith("```"))
            # If middle fences are balanced (even number), the outer fences are envelope wrappers
            if middle_fences % 2 == 0:
                return "\n".join(middle_lines).strip()
        # If not an outer envelope, preserve all markdown fences (including trailing code blocks) intact!
        return body

    # For non-markdown files (.js, .jsx, .json, .css, etc.):
    if first_line.startswith("```") and last_line == "```":
        return "\n".join(lines[1:-1]).strip()
    elif first_line.startswith("```"):
        return "\n".join(lines[1:]).strip()
    elif last_line == "```":
        return "\n".join(lines[:-1]).strip()

    return body


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

        norm_path = raw_path if raw_path.startswith('/') else f"/{raw_path}"
        is_md = norm_path.lower().endswith(('.md', '.markdown'))

        cleaned_body = strip_markdown_fences(body, is_markdown=is_md)
        files[norm_path] = cleaned_body.strip()

    return files
