import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

BACKEND_DOCS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "knowledge_base", "backend"))
CHROMA_DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))

def ingest_backend_docs():
    print(f"Scanning for backend documentation in: {BACKEND_DOCS_DIR}", flush=True)
    
    md_files = glob.glob(os.path.join(BACKEND_DOCS_DIR, "*.md"))
    if not md_files:
        print("No backend markdown files found!", flush=True)
        return

    print(f"Found {len(md_files)} backend document(s): {[os.path.basename(f) for f in md_files]}", flush=True)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)
    all_chunks = []

    for file_path in md_files:
        try:
            loader = TextLoader(file_path, encoding='utf-8')
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = os.path.basename(file_path)
                doc.metadata["domain"] = "backend"
            chunks = text_splitter.split_documents(docs)
            print(f"Extracted {len(chunks)} chunks from {os.path.basename(file_path)}", flush=True)
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error loading {file_path}: {e}", flush=True)

    if not all_chunks:
        print("No chunks extracted. Aborting.", flush=True)
        return

    print(f"Initializing local HuggingFace embedding model...", flush=True)
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print(f"Adding {len(all_chunks)} backend chunks into existing ChromaDB at {CHROMA_DB_DIR}...", flush=True)
    vectorstore = Chroma(persist_directory=CHROMA_DB_DIR, embedding_function=embeddings)
    vectorstore.add_documents(all_chunks)

    print(f">>> SUCCESS: Successfully ingested {len(all_chunks)} backend chunks into RAG Vector Store! <<<", flush=True)

if __name__ == "__main__":
    ingest_backend_docs()
