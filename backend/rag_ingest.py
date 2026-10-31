"""
rag_ingest.py - Selective, idempotent documentation ingestion for React documentation.

Key Features:
- Selectively targets ONLY:
  - knowledge_base/react.dev/src/content/reference
  - knowledge_base/react.dev/src/content/learn
- Skips non-documentation assets: CONTRIBUTING, CODE_OF_CONDUCT, LICENSE, .claude, etc.
- Injects metadata: `domain="frontend"`, `source=<relative_path>`.
- Fully idempotent: deterministic chunk IDs (SHA-256) and collection reset support.
- Zero sleep stalls: runs local HuggingFace embeddings at maximum processing speed.
"""

import os
import glob
import hashlib
from typing import List, Dict, Any, Optional
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
KNOWLEDGE_BASE_DIR = os.path.join(BASE_DIR, "knowledge_base", "react.dev")
CHROMA_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))

ALLOWED_SUBDIRS = [
    os.path.join(KNOWLEDGE_BASE_DIR, "src", "content", "reference"),
    os.path.join(KNOWLEDGE_BASE_DIR, "src", "content", "learn")
]

SKIP_PATTERNS = [
    "contributing", "code_of_conduct", "license", ".claude",
    ".github", ".husky", "eslint", "package.json", "yarn.lock"
]


def should_skip_path(path: str) -> bool:
    """Checks if a file path should be excluded from ingestion."""
    norm = path.replace("\\", "/").lower()
    return any(pattern in norm for pattern in SKIP_PATTERNS)


def get_deterministic_id(source_path: str, chunk_index: int) -> str:
    """Generates a stable, reproducible SHA-256 identifier for a document chunk."""
    seed = f"frontend:{source_path}:{chunk_index}".encode("utf-8")
    return hashlib.sha256(seed).hexdigest()


def ingest_docs(reset_collection: bool = False):
    """
    Scans selected React documentation directories, splits documents into chunks,
    applies metadata domain='frontend', and writes to ChromaDB with deterministic IDs.
    """
    print(f"Scanning selective documentation directories in: {KNOWLEDGE_BASE_DIR}", flush=True)
    all_files = []

    for target_dir in ALLOWED_SUBDIRS:
        if not os.path.exists(target_dir):
            print(f"Directory not found, skipping: {target_dir}", flush=True)
            continue

        for ext in ("**/*.md", "**/*.mdx"):
            matched = glob.glob(os.path.join(target_dir, ext), recursive=True)
            for file_path in matched:
                if not should_skip_path(file_path):
                    all_files.append(file_path)

    if not all_files:
        print("No matching documentation files found in reference or learn paths.", flush=True)
        return

    print(f"Found {len(all_files)} selective documents for frontend ingestion.", flush=True)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    all_chunks = []
    deterministic_ids = []

    for file_path in all_files:
        try:
            rel_path = os.path.relpath(file_path, KNOWLEDGE_BASE_DIR).replace("\\", "/")
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()

            for doc in docs:
                doc.metadata["source"] = rel_path
                doc.metadata["domain"] = "frontend"

            chunks = text_splitter.split_documents(docs)
            for idx, chunk in enumerate(chunks):
                # Ensure each chunk carries domain metadata
                chunk.metadata["domain"] = "frontend"
                chunk.metadata["source"] = rel_path
                chunk.metadata["chunk_index"] = idx
                cid = get_deterministic_id(rel_path, idx)
                all_chunks.append(chunk)
                deterministic_ids.append(cid)

        except Exception as e:
            print(f"Error processing {file_path}: {e}", flush=True)

    if not all_chunks:
        print("No content chunks could be extracted. Aborting.", flush=True)
        return

    print(f"Extracted {len(all_chunks)} total chunks. Initializing local HuggingFace embeddings...", flush=True)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"Connecting to ChromaDB at {CHROMA_DB_DIR}...", flush=True)
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
        collection_name="langchain"
    )

    if reset_collection:
        print("Reset collection requested. Clearing existing frontend chunks...", flush=True)
        try:
            vectorstore.delete(where={"domain": "frontend"})
            print("Cleared existing frontend documents from collection.")
        except Exception as err:
            print(f"Collection reset warning: {err}")

    print(f"Writing {len(all_chunks)} chunks with deterministic IDs (idempotent upsert)...", flush=True)
    batch_size = 200
    for i in range(0, len(all_chunks), batch_size):
        batch_docs = all_chunks[i:i + batch_size]
        batch_ids = deterministic_ids[i:i + batch_size]
        print(f"Adding batch {i // batch_size + 1}/{(len(all_chunks) - 1) // batch_size + 1} ({len(batch_docs)} chunks)...", flush=True)
        vectorstore.add_documents(documents=batch_docs, ids=batch_ids)

    print(">>> SUCCESS: Frontend selective documentation ingestion completed idempotently! <<<", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest React documentation into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Reset existing frontend chunks in collection")
    args = parser.parse_args()
    ingest_docs(reset_collection=args.reset)
