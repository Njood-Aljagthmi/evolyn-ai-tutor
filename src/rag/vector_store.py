import os
import pickle
from dotenv import load_dotenv

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS


load_dotenv()

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.normpath(os.path.join(CURRENT_DIR, "../../"))
CHUNKS_FILE = os.path.join(BASE_DIR, "data", "processed_chunks.pkl")
FAISS_DIR = os.path.join(BASE_DIR, "data", "faiss_index")


def build_vector_db():
    """Build FAISS vector database from processed_chunks.pkl."""
    if not os.path.exists(CHUNKS_FILE):
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_FILE}")

    with open(CHUNKS_FILE, "rb") as f:
        chunks = pickle.load(f)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    vector_db = FAISS.from_documents(chunks, embeddings)
    vector_db.save_local(FAISS_DIR)

    return {
        "status": "success",
        "message": "FAISS vector database created successfully",
        "total_chunks": len(chunks),
        "path": FAISS_DIR,
    }


def load_vector_db():
    """Load existing FAISS vector database."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    return FAISS.load_local(
        FAISS_DIR,
        embeddings,
        allow_dangerous_deserialization=True
    )


def retrieve_knowledge(query, language=None, level=None, k=3):
    """Retrieve relevant chunks from FAISS."""
    vector_db = load_vector_db()
    # Fetch a larger pool of documents to filter accurately in-memory
    docs = vector_db.similarity_search(query, k=100)

    filtered_docs = []

    for doc in docs:
        metadata = doc.metadata

        if language and str(metadata.get("language", "")).lower() != language.lower():
            continue

        if level and str(metadata.get("level", "")).lower() != level.lower():
            continue

        filtered_docs.append(doc)
        if len(filtered_docs) >= k:
            break

    return {
        "status": "success",
        "query": query,
        "results": [
            {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            for doc in filtered_docs
        ]
    }


if __name__ == "__main__":

    result = build_vector_db()
    print(result)

    test = retrieve_knowledge(
        query="What are variables in Python?",
        language="python",
        level="beginner"
    )

    print("STATUS:", test["status"])
    print("RESULTS COUNT:", len(test["results"]))

    if test["results"]:
        print("FIRST RESULT:")
        print(test["results"][0]["content"][:500])
        print("METADATA:")
        print(test["results"][0]["metadata"])

    print("\n===== RESULT =====\n")
    print(test["results"][0]["content"])
