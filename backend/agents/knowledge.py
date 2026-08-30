from langchain_community.vectorstores import Chroma

import os

def knowledge_node(state):
    print("--- RAG KNOWLEDGE AGENT ---")
    plan = state.get("plan", "")
    
    # We will mock the RAG retrieval if DB is not populated yet, or retrieve if it is
    db_path = "./chroma_db"
    context = ""
    if os.path.exists(db_path):
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            vectorstore = Chroma(persist_directory=db_path, embedding_function=embeddings)
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
            docs = retriever.invoke(plan)
            context = "\n".join([doc.page_content for doc in docs])
            print("Retrieved context from ChromaDB.")
        except Exception as e:
            print(f"Error querying ChromaDB: {e}")
            context = "No specific context found. Rely on base training."
    else:
        context = "No RAG DB found. Rely on base training."
        
    return {"context": context}
