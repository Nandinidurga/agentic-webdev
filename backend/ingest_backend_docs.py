"""
ingest_backend_docs.py - Idempotent documentation ingestion for Backend Node.js/Express docs.

Key Features:
- Scans knowledge_base/backend/*.md
- Applies metadata domain="backend" and source=<filename>
- Idempotent upsert via deterministic SHA-256 chunk IDs
- Collection reset support via reset_collection parameter or --reset CLI flag
- Uses modern langchain_chroma.Chroma
"""

import glob
import hashlib
import os

from dotenv import find_dotenv, load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv(find_dotenv())

BACKEND_DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "backend"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))


def get_deterministic_backend_id(source_name: str, chunk_index: int) -> str:
    """Generates a stable, reproducible SHA-256 identifier for a backend document chunk."""
    seed = f"backend:{source_name}:{chunk_index}".encode()
    return hashlib.sha256(seed).hexdigest()


def ingest_backend_docs(reset_collection: bool = False):
    """
    Scans backend documentation files, splits into chunks, applies domain='backend',
    and writes to ChromaDB with deterministic IDs for idempotent ingestion.
    """
    print(f"Scanning for backend documentation in: {BACKEND_DOCS_DIR}", flush=True)

    md_files = glob.glob(os.path.join(BACKEND_DOCS_DIR, "*.md"))
    if not md_files:
        print("No backend markdown files found!", flush=True)
        return

    print(f"Found {len(md_files)} backend document(s): {[os.path.basename(f) for f in md_files]}", flush=True)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    all_chunks = []
    deterministic_ids = []

    for file_path in md_files:
        try:
            source_name = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            docs = [Document(page_content=content, metadata={"source": source_name, "domain": "backend"})]

            chunks = text_splitter.split_documents(docs)
            for idx, chunk in enumerate(chunks):
                chunk.metadata["source"] = source_name
                chunk.metadata["domain"] = "backend"
                chunk.metadata["chunk_index"] = idx
                cid = get_deterministic_backend_id(source_name, idx)
                all_chunks.append(chunk)
                deterministic_ids.append(cid)

            print(f"Extracted {len(chunks)} chunks from {source_name}", flush=True)
        except Exception as e:
            print(f"Error loading {file_path}: {e}", flush=True)

    if not all_chunks:
        print("No chunks extracted. Aborting.", flush=True)
        return

    print("Initializing local HuggingFace embedding model...", flush=True)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"Connecting to ChromaDB at {CHROMA_DB_DIR}...", flush=True)
    vectorstore = Chroma(
        persist_directory=CHROMA_DB_DIR,
        embedding_function=embeddings,
        collection_name="langchain"
    )

    if reset_collection:
        print("Reset collection requested. Clearing existing backend chunks...", flush=True)
        try:
            vectorstore.delete(where={"domain": "backend"})
            print("Cleared existing backend documents from collection.")
        except Exception as err:
            print(f"Collection reset warning: {err}")

    print(f"Adding {len(all_chunks)} backend chunks into ChromaDB with deterministic IDs (idempotent upsert)...", flush=True)
    vectorstore.add_documents(documents=all_chunks, ids=deterministic_ids)

    print(f">>> SUCCESS: Successfully ingested {len(all_chunks)} backend chunks into RAG Vector Store idempotently! <<<", flush=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ingest Backend documentation into ChromaDB")
    parser.add_argument("--reset", action="store_true", help="Reset existing backend chunks in collection")
    args = parser.parse_args()
    ingest_backend_docs(reset_collection=args.reset)
