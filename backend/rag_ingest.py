import os
import glob
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_community.vectorstores import Chroma
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

KNOWLEDGE_BASE_DIR = "../knowledge_base"
CHROMA_DB_DIR = "./chroma_db"

def ingest_docs():
    print(f"Scanning {KNOWLEDGE_BASE_DIR} for PDFs, MD, and MDX files...")
    
    pdf_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "**/*.pdf"), recursive=True)
    md_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "**/*.md"), recursive=True)
    mdx_files = glob.glob(os.path.join(KNOWLEDGE_BASE_DIR, "**/*.mdx"), recursive=True)
    
    all_files = pdf_files + md_files + mdx_files
    
    if not all_files:
        print("No documents found.")
        return

    print(f"Found {len(all_files)} documents. Loading and splitting...")
    
    all_chunks = []
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

    for file_path in all_files:
        try:
            if file_path.endswith('.pdf'):
                loader = PyPDFLoader(file_path)
            else:
                loader = TextLoader(file_path, encoding='utf-8')
            
            docs = loader.load()
            chunks = text_splitter.split_documents(docs)
            print(f"Extracted {len(chunks)} chunks from {os.path.basename(file_path)}")
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")

    if not all_chunks:
        print("No content could be extracted.")
        return

    print("Initializing embedding model (HuggingFace Local)...")
    from langchain_huggingface import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    print(f"Storing {len(all_chunks)} chunks in ChromaDB at {CHROMA_DB_DIR} in batches to avoid rate limits...")
    
    import time
    batch_size = 100
    vectorstore = None
    
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        print(f"Processing batch {i//batch_size + 1}/{(len(all_chunks)//batch_size) + 1} ({len(batch)} chunks)...")
        
        try:
            if vectorstore is None:
                vectorstore = Chroma.from_documents(
                    documents=batch,
                    embedding=embeddings,
                    persist_directory=CHROMA_DB_DIR
                )
            else:
                vectorstore.add_documents(batch)
            
            # Wait to avoid hitting Google's rate limits
            if i + batch_size < len(all_chunks):
                print("Sleeping for 10 seconds to respect API rate limits...")
                time.sleep(10)
        except Exception as e:
            print(f"Rate limit or error hit on batch {i//batch_size + 1}: {e}")
            print("Waiting 60 seconds before continuing...")
            time.sleep(60)
            
    print("Ingestion complete!")

if __name__ == "__main__":
    ingest_docs()
