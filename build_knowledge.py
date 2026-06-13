from langchain.vectorstores import Chroma
from langchain.embeddings import OllamaEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import DirectoryLoader
from pathlib import Path
import os
import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

"""
Production-ready knowledge base builder using LangChain and ChromaDB.
Loads Python files from the project, creates embeddings, and persists them locally.
"""


def build_knowledge_base():
    """
    Build and persist a knowledge base from Python files in the project.
    Uses LangChain and ChromaDB to create embeddings and store them locally.
    """

    # Define configuration
    project_root = Path(__file__).parent
    chroma_db_dir = project_root / "chroma_db"
    exclude_dirs = {".devcontainer", "node_modules",
                    "__pycache__", ".git", ".venv", "venv", ".pytest_cache"}

    # Step 1: Load documents
    print("\n" + "="*70)
    print("STEP 1: Loading Python files from project directory...")
    print("="*70)

    try:
        loader = DirectoryLoader(
            str(project_root),
            glob="**/*.py",
            show_progress=True,
            loader_kwargs={"encoding": "utf-8"}
        )

        documents = loader.load()

        # Filter out documents from excluded directories
        filtered_documents = []
        for doc in documents:
            doc_path = Path(doc.metadata.get("source", ""))
            if not any(excluded in doc_path.parts for excluded in exclude_dirs):
                filtered_documents.append(doc)

        print(f"✓ Successfully loaded {len(filtered_documents)} Python files")
        print(f"  Total documents found: {len(documents)}")
        print(f"  Documents after filtering: {len(filtered_documents)}")

        if not filtered_documents:
            print("⚠ Warning: No Python files found after filtering.")
            return

    except Exception as e:
        print(f"✗ Error loading documents: {str(e)}")
        raise

    # Step 2: Split documents into chunks
    print("\n" + "="*70)
    print("STEP 2: Splitting documents into chunks...")
    print("="*70)

    try:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = splitter.split_documents(filtered_documents)

        print(f"✓ Successfully split documents into chunks")
        print(f"  Total chunks created: {len(chunks)}")
        if chunks:
            avg_chunk_size = sum(len(chunk.page_content)
                                 for chunk in chunks) // len(chunks)
            print(f"  Average chunk size: {avg_chunk_size} characters")

    except Exception as e:
        print(f"✗ Error splitting documents: {str(e)}")
        raise

    # Step 3: Create embeddings
    print("\n" + "="*70)
    print("STEP 3: Creating embeddings using OllamaEmbeddings...")
    print("="*70)

    try:
        embeddings = OllamaEmbeddings(model="gemma4")
        print(f"✓ OllamaEmbeddings initialized successfully")
        print(f"  Model: gemma4")
        print(f"  Ollama will process {len(chunks)} chunks for embedding")

    except Exception as e:
        print(f"✗ Error initializing embeddings: {str(e)}")
        print("  Make sure Ollama is running with 'ollama serve' command")
        raise

    # Step 4: Create and persist vector store
    print("\n" + "="*70)
    print("STEP 4: Creating and persisting ChromaDB vector store...")
    print("="*70)

    try:
        # Ensure chroma_db directory exists
        chroma_db_dir.mkdir(exist_ok=True)

        print(f"  Processing embeddings... (this may take a while)")

        # Create Chroma vector store from documents
        vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=str(chroma_db_dir)
        )

        # Persist the vector store
        vector_store.persist()

        print(f"✓ Vector store created and persisted successfully")
        print(f"  Location: {chroma_db_dir}")
        print(f"  Total vectors stored: {len(chunks)}")

    except Exception as e:
        print(f"✗ Error creating vector store: {str(e)}")
        raise

    # Final summary
    print("\n" + "="*70)
    print("✓ KNOWLEDGE BASE BUILD COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"\nSummary:")
    print(f"  • Documents loaded: {len(filtered_documents)}")
    print(f"  • Chunks created: {len(chunks)}")
    print(f"  • Embeddings model: gemma4")
    print(f"  • Vector store location: {chroma_db_dir}")
    print(f"\nThe knowledge base is now ready for querying with RAG applications.")
    print("="*70 + "\n")


if __name__ == "__main__":
    build_knowledge_base()
