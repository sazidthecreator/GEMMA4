from langchain.chains import RetrievalQA
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import Chroma
from pathlib import Path
import os
import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

"""
Production-grade RAG (Retrieval-Augmented Generation) Query Agent.
Uses LangChain, ChromaDB, and Ollama to answer questions based on indexed codebase knowledge.
"""


def initialize_rag_agent():
    """
    Initialize and configure the RAG agent with vector store, embeddings, and LLM.

    Returns:
        tuple: (qa_chain, vector_store) - The RAG chain and vector store
    """

    print("\n" + "="*80)
    print("INITIALIZING NEXUS CORE AI ASSISTANT - RAG AGENT")
    print("="*80)

    # Step 1: Initialize embeddings
    print("\n[System] Initializing OllamaEmbeddings with gemma4 model...")
    try:
        embeddings = OllamaEmbeddings(model="gemma4")
        print("✓ OllamaEmbeddings initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing embeddings: {str(e)}")
        print("  Ensure Ollama is running with: ollama serve")
        raise

    # Step 2: Load vector store
    print("\n[System] Loading ChromaDB vector store from './chroma_db'...")
    chroma_db_path = Path("./chroma_db")

    if not chroma_db_path.exists():
        print(f"✗ Vector store not found at {chroma_db_path}")
        print("  Please run 'python build_knowledge.py' first to create the knowledge base")
        raise FileNotFoundError(f"ChromaDB not found at {chroma_db_path}")

    try:
        vector_store = Chroma(
            persist_directory=str(chroma_db_path),
            embedding_function=embeddings
        )
        vector_count = vector_store._collection.count()
        print(f"✓ ChromaDB vector store loaded successfully")
        print(f"  Vectors in store: {vector_count}")
    except Exception as e:
        print(f"✗ Error loading vector store: {str(e)}")
        raise

    # Step 3: Initialize Language Model
    print("\n[System] Initializing ChatOllama with gemma4 model...")
    try:
        llm = ChatOllama(
            model="gemma4",
            temperature=0.3,
            base_url="http://127.0.0.1:11434"
        )
        print("✓ ChatOllama initialized successfully")
        print("  Model: gemma4")
        print("  Temperature: 0.3")
    except Exception as e:
        print(f"✗ Error initializing LLM: {str(e)}")
        print("  Ensure Ollama is running with: ollama serve")
        raise

    # Step 4: Create custom system prompt with XML-style structure
    print("\n[System] Configuring Nexus Core AI Assistant system prompt...")

    system_prompt = """<nexus_core_ai>
<identity>
You are the Nexus Core AI Assistant, a specialized code and knowledge base retrieval expert powered by advanced semantic understanding and retrieval-augmented generation (RAG).
</identity>

<core_directives>
<directive priority="critical">
ANSWER ONLY based on the context retrieved from the knowledge base. Do not use external knowledge or assumptions.
</directive>
<directive priority="high">
If the retrieved context is insufficient to accurately answer the query, respond with: "Context insufficient for an accurate solution. The knowledge base does not contain relevant information about this topic."
</directive>
<directive priority="high">
Provide clear, concise, and technically accurate responses tailored to the retrieved context.
</directive>
<directive priority="medium">
When referencing code or context, cite the source file or module when available.
</directive>
<directive priority="medium">
Format your responses for readability using markdown when appropriate.
</directive>
</core_directives>

<operational_constraints>
- Strictly adhere to retrieved context only
- Never hallucinate or invent information
- Acknowledge knowledge gaps honestly
- Provide actionable insights when possible
- Maintain a professional and helpful tone
</operational_constraints>

<context>
Retrieved knowledge base documents:
{context}
</context>
</nexus_core_ai>"""

    # Create prompt template
    prompt_template = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template("{question}")
    ])

    print("✓ System prompt configured successfully")

    # Step 5: Set up retriever
    print("\n[System] Setting up contextual retriever...")
    try:
        retriever = vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 3}
        )
        print("✓ Retriever configured successfully")
        print("  Search type: similarity")
        print("  Top-k results: 3")
    except Exception as e:
        print(f"✗ Error setting up retriever: {str(e)}")
        raise

    # Step 6: Create RetrievalQA chain
    print("\n[System] Creating RetrievalQA pipeline...")
    try:
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
            chain_type_kwargs={
                "prompt": prompt_template,
                "verbose": False
            }
        )
        print("✓ RetrievalQA pipeline created successfully")
    except Exception as e:
        print(f"✗ Error creating QA chain: {str(e)}")
        raise

    print("\n" + "="*80)
    print("✓ NEXUS CORE AI ASSISTANT READY")
    print("="*80)
    print("\nAgent Status: ONLINE")
    print("Model: gemma4")
    print("Knowledge Base: Active")
    print("\nType 'exit' or 'quit' to terminate the session.")
    print("="*80 + "\n")

    return qa_chain, vector_store


def format_response(response_data):
    """
    Format the QA response with source documents and context.

    Args:
        response_data: Dictionary containing 'result' and 'source_documents'

    Returns:
        str: Formatted response string
    """
    result = response_data.get("result", "")
    source_docs = response_data.get("source_documents", [])

    formatted = f"\n{result}"

    if source_docs:
        formatted += "\n\n[Sources]"
        for i, doc in enumerate(source_docs, 1):
            source = doc.metadata.get("source", "Unknown")
            formatted += f"\n  {i}. {source}"

    return formatted


def run_interactive_session(qa_chain):
    """
    Run the interactive CLI loop for querying the knowledge base.

    Args:
        qa_chain: The initialized RetrievalQA chain
    """
    session_count = 0

    while True:
        try:
            print("[Input] Enter your query (or 'exit' to quit):")
            user_query = input(">>> ").strip()

            # Check for exit commands
            if user_query.lower() in ["exit", "quit", "q"]:
                print("\n" + "="*80)
                print("[System] Nexus Core AI Assistant shutting down...")
                print(f"[System] Total queries processed: {session_count}")
                print("="*80)
                print("\nThank you for using the Nexus Core AI Assistant. Goodbye!\n")
                break

            # Skip empty inputs
            if not user_query:
                print("[System] Please enter a valid query.\n")
                continue

            session_count += 1

            # Process query
            print("\n[Thinking...] Processing your query with RAG pipeline...")

            try:
                response_data = qa_chain({
                    "query": user_query
                })

                print("[Response]")
                formatted_response = format_response(response_data)
                print(formatted_response)
                print()

            except Exception as e:
                print(f"\n[Error] Failed to process query: {str(e)}")
                print(
                    "[Suggestion] Ensure Ollama is running and the knowledge base is properly initialized.\n")

        except KeyboardInterrupt:
            print("\n\n[System] Session interrupted by user.")
            print(f"[System] Total queries processed: {session_count}")
            print("="*80)
            print("\nThank you for using the Nexus Core AI Assistant. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n[Error] Unexpected error: {str(e)}\n")
            continue


def main():
    """
    Main entry point for the RAG Query Agent.
    """
    try:
        # Initialize the RAG agent
        qa_chain, vector_store = initialize_rag_agent()

        # Start interactive session
        run_interactive_session(qa_chain)

    except Exception as e:
        print(f"\n✗ Fatal error: {str(e)}")
        print("\nSetup Instructions:")
        print("1. Ensure Ollama is running: ollama serve")
        print("2. Build the knowledge base: python build_knowledge.py")
        print("3. Then run this script: python query_agent.py")
        exit(1)


if __name__ == "__main__":
    main()
