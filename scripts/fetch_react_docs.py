#!/usr/bin/env python3
"""
scripts/fetch_react_docs.py - Selective React documentation retrieval script.

Fetches ONLY official documentation files from react.dev under:
  - src/content/reference
  - src/content/learn
Excludes tests, site code, assets, and project meta files.
"""

import os
import sys
import shutil
import zipfile
import tempfile
import urllib.request
import subprocess

TARGET_REPO = "https://github.com/reactjs/react.dev.git"
ZIP_URL = "https://github.com/reactjs/react.dev/archive/refs/heads/main.zip"
ALLOWED_PREFIXES = (
    "src/content/reference/",
    "src/content/learn/"
)

def get_target_dir() -> str:
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(root, "knowledge_base", "react.dev")

def fetch_via_git(target_dir: str) -> bool:
    """Attempts git sparse checkout to only download reference and learn content."""
    try:
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        os.makedirs(target_dir, exist_ok=True)
        
        print("Cloning react.dev with git sparse-checkout...", flush=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", TARGET_REPO, target_dir],
            check=True,
            capture_output=True,
            text=True
        )
        subprocess.run(
            ["git", "sparse-checkout", "set", "src/content/reference", "src/content/learn"],
            cwd=target_dir,
            check=True,
            capture_output=True,
            text=True
        )
        print("Successfully fetched via git sparse-checkout.")
        return True
    except Exception as e:
        print(f"Git sparse-checkout failed ({e}). Falling back to zip archive...", flush=True)
        return False

def fetch_via_zip(target_dir: str):
    """Downloads repository archive and extracts only allowed documentation paths."""
    print(f"Downloading react.dev main zip from {ZIP_URL}...", flush=True)
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp_zip = tmp.name

    try:
        req = urllib.request.Request(
            ZIP_URL,
            headers={"User-Agent": "agentic-webdev-doc-fetcher/1.0"}
        )
        with urllib.request.urlopen(req) as resp, open(tmp_zip, "wb") as out_f:
            shutil.copyfileobj(resp, out_f)

        print("Extracting selective documentation files...", flush=True)
        os.makedirs(target_dir, exist_ok=True)
        extracted_count = 0

        with zipfile.ZipFile(tmp_zip, 'r') as zip_ref:
            for member in zip_ref.namelist():
                # Strip root prefix (e.g., 'react.dev-main/')
                parts = member.split('/', 1)
                if len(parts) < 2:
                    continue
                rel_path = parts[1]

                if any(rel_path.startswith(prefix) for prefix in ALLOWED_PREFIXES) and (rel_path.endswith('.md') or rel_path.endswith('.mdx')):
                    dest_path = os.path.join(target_dir, rel_path)
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    with zip_ref.open(member) as src, open(dest_path, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted_count += 1

        print(f"Successfully extracted {extracted_count} selective documentation files to {target_dir}")
    finally:
        if os.path.exists(tmp_zip):
            try:
                os.unlink(tmp_zip)
            except Exception:
                pass

def main():
    target_dir = get_target_dir()
    print(f"Target directory for React docs: {target_dir}")
    
    # Try git sparse checkout first; fallback to direct archive extraction
    if not fetch_via_git(target_dir):
        fetch_via_zip(target_dir)

if __name__ == "__main__":
    main()
