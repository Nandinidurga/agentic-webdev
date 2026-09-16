import os
from langchain_community.vectorstores import Chroma

def knowledge_node(state):
    print("--- RAG KNOWLEDGE AGENT (FULL-STACK DUAL RETRIEVAL) ---", flush=True)
    prompt = state.get("prompt", "")
    plan = state.get("plan", "")
    
    # Locate chroma_db relative to this file
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    context = ""
    
    if os.path.exists(db_path):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
            
            # 1. Retrieve Backend-specific documentation (Express, routing, REST, middleware)
            backend_query = f"Express Node.js REST API routes endpoints middleware error handling data store {prompt}"
            backend_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
            backend_docs = backend_retriever.invoke(backend_query)
            
            # 2. Retrieve Frontend-specific documentation (React, components, state, hooks)
            frontend_query = f"React components hooks state layout UI JSX Tailwind {prompt}"
            frontend_retriever = vectorstore.as_retriever(search_kwargs={"k": 2})
            frontend_docs = frontend_retriever.invoke(frontend_query)
            
            backend_context = "\n---\n".join([
                f"[Source: {doc.metadata.get('source', 'backend')}]:\n{doc.page_content}" 
                for doc in backend_docs
            ])
            frontend_context = "\n---\n".join([
                f"[Source: {doc.metadata.get('source', 'frontend')}]:\n{doc.page_content}" 
                for doc in frontend_docs
            ])
            
            context = f"""=== BACKEND REFERENCE DOCUMENTATION (RAG) ===
{backend_context}

=== FRONTEND REFERENCE DOCUMENTATION (RAG) ===
{frontend_context}"""

            print(f"Retrieved {len(backend_docs)} backend doc chunks and {len(frontend_docs)} frontend doc chunks from ChromaDB.", flush=True)
        except Exception as e:
            print(f"Error querying ChromaDB: {e}", flush=True)
            context = "RAG context query failed. Rely on base training."
    else:
        context = "No RAG DB found. Rely on base training."
        
    return {"context": context}

