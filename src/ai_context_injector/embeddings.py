"""Semantic embeddings and vector search.

Provides provider-agnostic embedding generation using local models
(sentence-transformers) with fallback to keyword search.

Architecture inspired by Vercel AI SDK (provider-agnostic API),
Chroma (embedding + metadata in one call), and FAISS (fast cosine search).

Example:
    >>> from ai_context_injector import embed_many, search_semantic
    >>> 
    >>> embeddings = embed_many(["docker escape", "privesc technique"])
    >>> results = search_semantic("container breakout", embeddings, top_k=5)
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .core.types import Chunk

# ---------------------------------------------------------------------------
# Pure math — no model dependencies
# ---------------------------------------------------------------------------


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors.
    
    Pure numpy implementation, no model dependencies.
    Works with any embedding vectors of the same dimension.
    
    Args:
        a: First embedding vector
        b: Second embedding vector
        
    Returns:
        Cosine similarity score between 0.0 and 1.0
        
    Example:
        >>> cosine_similarity([1.0, 0.0], [0.0, 1.0])
        0.0
        >>> cosine_similarity([1.0, 0.0], [1.0, 0.0])
        1.0
    """
    if len(a) != len(b):
        raise ValueError(
            f"Vector dimensions must match: {len(a)} vs {len(b)}"
        )
    
    a_arr = np.array(a, dtype=np.float64)
    b_arr = np.array(b, dtype=np.float64)
    
    dot = np.dot(a_arr, b_arr)
    norm_a = np.linalg.norm(a_arr)
    norm_b = np.linalg.norm(b_arr)
    
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    
    return float(dot / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# Embedding generation — provider-agnostic
# ---------------------------------------------------------------------------

# Global model cache (lazy-loaded)
_embedding_model = None
_embedding_model_name = None
_embedding_dim = None


def _get_local_model(model_name: str = "all-MiniLM-L6-v2"):
    """Lazy-load sentence-transformers model.
    
    Args:
        model_name: HuggingFace model ID (default: all-MiniLM-L6-v2, 80MB)
        
    Returns:
        tuple of (model, dimension, model_name) or (None, None, None) if not available
    """
    global _embedding_model, _embedding_model_name, _embedding_dim
    
    # Return cached model if same name
    if _embedding_model is not None and _embedding_model_name == model_name:
        return _embedding_model, _embedding_dim
    
    try:
        from sentence_transformers import SentenceTransformer
        
        _embedding_model = SentenceTransformer(model_name)
        _embedding_model_name = model_name
        
        # Get embedding dimension from a test encoding
        test = _embedding_model.encode(["test"], show_progress_bar=False)
        _embedding_dim = test.shape[1] if len(test.shape) > 1 else len(test)
        
        return _embedding_model, _embedding_dim
        
    except ImportError:
        # sentence-transformers not installed — graceful fallback
        return None, None
    except Exception:
        # Model loading failed — graceful fallback
        _embedding_model = None
        return None, None


def embed(
    text: str,
    model: Optional[str] = None
) -> Optional[List[float]]:
    """Generate embedding for a single text.
    
    Args:
        text: Text to embed
        model: Model name or provider string
               - None: default local model (all-MiniLM-L6-v2)
               - "sentence-transformers/model_name": any HuggingFace model
               - "ollama/model_name": Ollama local model (future)
               - "openai/model_name": OpenAI embeddings (future)
        
    Returns:
        Embedding vector as list of floats, or None if model unavailable
        
    Example:
        >>> embedding = embed("docker escape technique")
        >>> len(embedding) >= 384
        True
    """
    if not text or not text.strip():
        return None
    
    # Model resolution
    actual_model = model or "all-MiniLM-L6-v2"
    
    # For now, only local sentence-transformers
    if model and (model.startswith("ollama/") or model.startswith("openai/")):
        # Future: support Ollama and OpenAI providers
        raise NotImplementedError(
            f"Provider '{model}' not yet supported. "
            "Currently only local sentence-transformers models are available."
        )
    
    st_model, _ = _get_local_model(actual_model)
    
    if st_model is None:
        return None
    
    embedding = st_model.encode(
        [text],
        show_progress_bar=False
    )
    
    # Flatten to list
    if len(embedding.shape) > 1:
        return embedding[0].tolist()
    return embedding.tolist()


def embed_many(
    texts: List[str],
    model: Optional[str] = None
) -> Tuple[List[Optional[List[float]]], bool]:
    """Generate embeddings for multiple texts.
    
    Provider-agnostic: uses local model by default with extensibility
    for Ollama, OpenAI, and other providers.
    
    Args:
        texts: List of texts to embed
        model: Model name or provider string (None = local default)
        
    Returns:
        Tuple of (embeddings_list, success_flag) where:
        - embeddings_list: List of embedding vectors (same order as texts)
        - success_flag: True if model loaded successfully
        
    Example:
        >>> embeddings, ok = embed_many(["docker", "kubernetes"])
        >>> ok
        True
        >>> len(embeddings) == 2
        True
    """
    if not texts:
        return [], True
    
    # Filter empty texts
    valid_texts = [t for t in texts if t and t.strip()]
    if not valid_texts:
        return [None] * len(texts), True
    
    actual_model = model or "all-MiniLM-L6-v2"
    st_model, _ = _get_local_model(actual_model)
    
    if st_model is None:
        return [None] * len(texts), False
    
    embeddings = st_model.encode(
        valid_texts,
        show_progress_bar=False
    )
    
    # Convert to list of lists
    result = embeddings.tolist()
    
    return result, True


# ---------------------------------------------------------------------------
# Semantic search — Chroma-style: embeddings + metadata + filters
# ---------------------------------------------------------------------------


def search_semantic(
    query: str,
    chunks: List[Chunk],
    embeddings: Optional[List[List[float]]] = None,
    top_k: int = 10,
    min_similarity: float = 0.0,
    filters: Optional[Dict[str, Any]] = None,
    model: Optional[str] = None
) -> List[Tuple[Chunk, float]]:
    """Semantic search over chunks using cosine similarity.
    
    If embeddings are pre-computed, uses those. Otherwise generates them.
    Results are filtered by metadata and sorted by relevance.
    
    Args:
        query: Search query text
        chunks: List of Chunk objects to search
        embeddings: Pre-computed embeddings (same order as chunks, optional)
        top_k: Maximum results to return
        min_similarity: Minimum cosine similarity threshold (0.0-1.0)
        filters: Metadata key-value pairs to filter results
        model: Embedding model to use (None = local default)
        
    Returns:
        List of (chunk, similarity_score) tuples sorted by similarity desc
        
    Example:
        >>> chunks = index("docker escape via bind mount")
        >>> results = search_semantic("container breakout", chunks)
        >>> results[0][1] >= 0.5  # Similarity >= 0.5
        True
    """
    if not chunks:
        return []
    
    # Generate query embedding
    query_embedding = embed(query, model=model)
    
    if query_embedding is None:
        # Fallback to keyword search if embeddings unavailable
        return _keyword_search_chunks(query, chunks, top_k, filters)
    
    # Generate or use pre-computed chunk embeddings
    if embeddings is None:
        chunk_texts = [c.content for c in chunks]
        chunk_embeddings, ok = embed_many(chunk_texts, model=model)
        if not ok or not chunk_embeddings:
            return _keyword_search_chunks(query, chunks, top_k, filters)
    else:
        chunk_embeddings = embeddings
    
    if query_embedding is None:
        return []
        
    # Compute similarities
    scored = []
    for i, chunk in enumerate(chunks):
        if i >= len(chunk_embeddings) or chunk_embeddings[i] is None:
            continue
        
        sim = cosine_similarity(query_embedding, chunk_embeddings[i])
        
        if sim < min_similarity:
            continue
        
        # Apply metadata filters
        if filters and not _match_filters(chunk.metadata, filters):
            continue
        
        scored.append((chunk, sim))
    
    # Sort by similarity descending
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[:top_k]


def _keyword_search_chunks(
    query: str,
    chunks: List[Chunk],
    top_k: int,
    filters: Optional[Dict[str, Any]] = None
) -> List[Tuple[Chunk, float]]:
    """Fallback keyword search when embeddings unavailable.
    
    Simple substring matching with artificial scores.
    
    Args:
        query: Search query
        chunks: List of chunks
        top_k: Max results
        filters: Metadata filters
        
    Returns:
        List of (chunk, pseudo_similarity) tuples
    """
    query_lower = query.lower()
    words = query_lower.split()
    results = []
    
    for chunk in chunks:
        content_lower = chunk.content.lower()
        
        # Score: count matching words
        matches = sum(1 for w in words if w in content_lower)
        if matches == 0:
            continue
        
        # Apply filters
        if filters and not _match_filters(chunk.metadata, filters):
            continue
        
        # Pseudo-similarity: % of words matched
        pseudo_score = matches / len(words)
        results.append((chunk, pseudo_score))
    
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_k]


def _match_filters(metadata: dict, filters: dict) -> bool:
    """Check if metadata matches all filter criteria.
    
    Supports nested field access using dot notation.
    
    Args:
        metadata: Chunk metadata dict
        filters: Filter criteria dict
        
    Returns:
        True if all filters match
    """
    for key, value in filters.items():
        current = metadata
        parts = key.split(".")
        
        for part in parts[:-1]:
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return False
        
        if isinstance(current, dict):
            actual = current.get(parts[-1])
        else:
            return False
        
        if isinstance(actual, list) and not isinstance(value, list):
            if value not in actual:
                return False
        elif actual != value:
            return False
    
    return True


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def pair_distance(
    a_embedding: List[float],
    b_embedding: List[float],
    metric: str = "cosine"
) -> float:
    """Compute distance between two embeddings.
    
    Args:
        a_embedding: First embedding vector
        b_embedding: Second embedding vector
        metric: Distance metric ("cosine", "euclidean", "dot")
        
    Returns:
        Distance/similarity score
        
    Raises:
        ValueError: If metric is invalid
    """
    if metric == "cosine":
        return cosine_similarity(a_embedding, b_embedding)
    
    a_arr = np.array(a_embedding, dtype=np.float64)
    b_arr = np.array(b_embedding, dtype=np.float64)
    
    if metric == "euclidean":
        return float(1.0 / (1.0 + np.linalg.norm(a_arr - b_arr)))
    
    if metric == "dot":
        return float(np.dot(a_arr, b_arr))
    
    raise ValueError(
        f"Unknown metric: '{metric}'. "
        "Valid: 'cosine', 'euclidean', 'dot'"
    )
