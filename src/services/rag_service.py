import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

CURRENT_DIR = Path(__file__).resolve().parent
ROOT_DIR = CURRENT_DIR.parents[1]
sys.path.append(str(ROOT_DIR))

from src.rag.vector_store import load_vector_db

# In-memory caches
_cached_vector_db = None
_query_cache: Dict[str, Dict[str, Any]] = {}

def get_cached_vector_db():
    """
    Retrieve loaded FAISS database from cache or load it if not cached.
    Prevents repeated loading from disk.
    """
    global _cached_vector_db
    if _cached_vector_db is None:
        logger.info("Loading FAISS vector database into memory cache...")
        _cached_vector_db = load_vector_db()
    return _cached_vector_db

def retrieve_knowledge_cached(query: str, language: str = None, level: str = None, k: int = 3) -> dict:
    """
    Retrieves and filters knowledge chunks from FAISS, utilizing in-memory caching.
    """
    cache_key = f"{language or ''}_{level or ''}_{query}_{k}"
    if cache_key in _query_cache:
        # print(f"RAG Cache Hit for: {cache_key[:40]}...")
        return _query_cache[cache_key]

    # Use the cached vector database
    vector_db = get_cached_vector_db()
    
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

    result = {
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
    
    # Store in query cache
    _query_cache[cache_key] = result
    return result
