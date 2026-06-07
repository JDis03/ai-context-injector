"""Cross-encoder reranker for improving search relevance.

Cross-encoders read query and document TOGETHER, producing true relevance scores.
This is 2-3x more accurate than cosine similarity but ~10x slower per pair.
The trade-off is handled by only reranking top-N candidates (30).

Based on cross-encoder/ms-marco-MiniLM-L-6-v2 (80MB, 50ms per pair, CPU).

Features:
- Lazy model loading (no download until first rerank)
- LRU prediction cache (1000 entries)
- Graceful fallback to original order on model failure
- Thread-safe singleton pattern

Example:
    >>> reranker = Reranker()
    >>> results = reranker.rerank("privesc", [
    ...     ("docker escape", 0.85),
    ...     ("windows exploit", 0.80),
    ...     ("bind mount breakout", 0.75),
    ... ], top_k=2)
"""

import hashlib
import logging
import threading
import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# LRU Cache
# ---------------------------------------------------------------------------

class _LRUCache:
    """Simple LRU cache with configurable max size."""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict = OrderedDict()
        self._hits = 0
        self._misses = 0
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[float]:
        """Get value and move to end (most recently used)."""
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            self._hits += 1
            self._cache.move_to_end(key)
            return self._cache[key]
    
    def set(self, key: str, value: float):
        """Set value, evict oldest if at max size."""
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.max_size:
                    self._cache.popitem(last=False)  # Remove oldest
            self._cache[key] = value
    
    def clear(self):
        """Reset cache."""
        with self._lock:
            self._cache.clear()
            self._hits = 0
            self._misses = 0
    
    def stats(self) -> Dict[str, Any]:
        """Return cache metrics."""
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": self._hits / total if total > 0 else 0.0,
            }


# ---------------------------------------------------------------------------
# Reranker
# ---------------------------------------------------------------------------

class Reranker:
    """Cross-encoder reranker for improving search result relevance.
    
    Uses a cross-encoder model that reads query + document text TOGETHER
    to produce a true relevance score. Significantly more accurate than
    cosine similarity but ~10x slower per pair.
    
    Default model: cross-encoder/ms-marco-MiniLM-L-6-v2
    Size: 80MB download
    Speed: ~50ms per pair on CPU (1.5s for top-30)
    
    Example:
        >>> reranker = Reranker()
        >>> 
        >>> candidates = [
        ...     ("docker container escape technique", 0.85),  # (content, cosine_score)
        ...     ("windows kernel exploit", 0.82),
        ... ]
        >>> 
        >>> results = reranker.rerank(
        ...     query="container breakout",
        ...     candidates=candidates,
        ...     top_k=1
        ... )
        >>> results[0][0]  # Best match content after reranking
        'docker container escape technique'
    """
    
    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    DEFAULT_CACHE_SIZE = 1000
    
    def __init__(
        self,
        model: Optional[str] = None,
        cache_size: int = DEFAULT_CACHE_SIZE
    ):
        """Initialize reranker.
        
        Args:
            model: Cross-encoder model name (None = default)
            cache_size: LRU cache size for predictions
        """
        self.model_name = model or self.DEFAULT_MODEL
        self.model = None  # Lazy-loaded
        self._fallback_active = False
        self._fallback_reason = ""
        self._model_lock = threading.Lock()
        self.cache = _LRUCache(max_size=cache_size)
    
    def _load_model(self) -> bool:
        """Lazy-load the cross-encoder model.
        
        Returns:
            True if model loaded successfully
        """
        with self._model_lock:
            # Double-check inside lock
            if self.model is not None:
                return True
            
            try:
                from sentence_transformers import CrossEncoder
                
                # Fix naming: convert HuggingFace "cross-encoder/X" to "X"
                if self.model_name.startswith("cross-encoder/"):
                    hf_name = self.model_name
                else:
                    hf_name = f"cross-encoder/{self.model_name}"
                
                logger.info(f"Loading reranker model: {hf_name}")
                self.model = CrossEncoder(hf_name)
                return True
                
            except ImportError:
                self._fallback_active = True
                self._fallback_reason = "sentence-transformers not installed"
                logger.warning(
                    f"Reranker unavailable: {self._fallback_reason}. "
                    "Install with: pip install sentence-transformers"
                )
                return False
                
            except Exception as e:
                self._fallback_active = True
                self._fallback_reason = f"model load failed: {e}"
                logger.error(f"Failed to load reranker model: {e}")
                return False
    
    def preload(self) -> bool:
        """Eagerly load the model instead of lazy loading.
        
        Returns:
            True if model loaded successfully
        """
        return self._load_model()
    
    def rerank(
        self,
        query: str,
        candidates: Sequence[Tuple[str, float]],
        top_k: int = 10,
        max_candidates: int = 30
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        """Rerank candidate documents using cross-encoder.
        
        Args:
            query: Search query text
            candidates: List of (content, score) tuples from initial search
            top_k: Number of results to return
            max_candidates: Max candidates to rerank (top-N from input)
            
        Returns:
            List of (content, reranker_score, metadata) tuples sorted by score desc.
            Metadata includes: reranked=True/False, time_ms, original_score
            
        Example:
            >>> reranker = Reranker()
            >>> candidates = [
            ...     ("docker escape", 0.9),
            ...     ("linux privesc", 0.8),
            ...     ("windows exploit", 0.7),
            ... ]
            >>> results = reranker.rerank("container breakout", candidates, top_k=2)
            >>> len(results) <= 2
            True
        """
        start_time = time.time()
        
        if not candidates:
            return []
        
        # Limit to max_candidates
        subset = list(candidates[:max_candidates])
        
        # Normalize subset to list of tuples for internal processing
        normalized: List[Tuple[str, float]] = []
        for item in subset:
            if isinstance(item, dict) and 'content' in item:
                normalized.append((str(item['content']), float(item.get('score', 0.5))))
            elif isinstance(item, str):
                normalized.append((item, 0.5))
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                normalized.append((str(item[0]), float(item[1])))
            else:
                normalized.append((str(item), 0.5))
        
        # Try to load model if not already loaded
        if not self._load_model():
            # Fallback: return original order
            elapsed = (time.time() - start_time) * 1000
            return [
                (content, score, {
                    "reranked": False,
                    "rerank_time_ms": elapsed,
                    "original_score": score,
                    "fallback_reason": self._fallback_reason,
                })
                for content, score in normalized[:top_k]
            ]
        
        # Format pairs: (query, document) for cross-encoder
        pairs = [(query, content) for content, _ in normalized]
        
        # Check cache for each pair
        cached_scores = []
        uncached_indices = []
        uncached_pairs = []
        
        for i, (content, _score) in enumerate(normalized):
            cache_key = self._make_cache_key(query, content)
            cached = self.cache.get(cache_key)
            
            if cached is not None:
                cached_scores.append((i, cached))
            else:
                uncached_indices.append(i)
                uncached_pairs.append(pairs[i])
        
        # Predict uncached pairs
        if uncached_pairs:
            try:
                predictions = self.model.predict(uncached_pairs)
                
                # Cache predictions
                for j, (orig_idx, pred) in enumerate(zip(uncached_indices, predictions)):
                    score = float(pred)
                    content_text = normalized[orig_idx][0]
                    cache_key = self._make_cache_key(query, content_text)
                    self.cache.set(cache_key, score)
                    cached_scores.append((orig_idx, score))
                    
            except Exception as e:
                logger.error(f"Reranker prediction failed: {e}")
                elapsed = (time.time() - start_time) * 1000
                return [
                    (content, score, {
                        "reranked": False,
                        "rerank_time_ms": elapsed,
                        "original_score": score,
                        "fallback_reason": str(e),
                    })
                    for content, score in normalized[:top_k]
                ]
        
        # Sort by reranker score descending
        cached_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Build result as tuples
        elapsed = (time.time() - start_time) * 1000
        result = [
            (normalized[i][0], score, {
                "reranked": True,
                "rerank_time_ms": elapsed,
                "original_score": normalized[i][1],
            })
            for i, score in cached_scores[:top_k]
        ]
        
        return result
    
    def clear_cache(self):
        """Clear prediction cache."""
        self.cache.clear()
    
    def cache_stats(self) -> Dict[str, Any]:
        """Return cache metrics.
        
        Returns:
            Dict with size, max_size, hits, misses, hit_rate
        """
        return self.cache.stats()
    
    @staticmethod
    def _make_cache_key(query: str, content: str) -> str:
        """Create cache key from query and content.
        
        Uses SHA256 hash for stable, bounded-size keys.
        """
        combined = f"{query}|||{content[:500]}"  # Limit content to 500 chars
        return hashlib.sha256(combined.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

# Module-level singleton (lazy-initialized)
_reranker: Optional[Reranker] = None
_reranker_lock = threading.Lock()


def rerank(
    query: str,
    candidates: Sequence[Tuple[str, float]],
    top_k: int = 10,
    model: Optional[str] = None,
    max_candidates: int = 30
) -> List[Tuple[str, float, Dict[str, Any]]]:
    """Convenience function for one-shot reranking.
    
    Creates or reuses a module-level reranker instance.
    
    Args:
        query: Search query text
        candidates: List of (content, score) tuples
        top_k: Number of results to return
        model: Custom model name (None = default)
        max_candidates: Max candidates to rerank
        
    Returns:
        Reranked results with metadata
        
    Example:
        >>> from ai_context_injector import rerank
        >>> 
        >>> results = rerank(
        ...     "container breakout",
        ...     [("docker escape", 0.9), ("linux privesc", 0.8)],
        ...     top_k=1
        ... )
    """
    global _reranker
    
    with _reranker_lock:
        if _reranker is None or (model and _reranker.model_name != model):
            _reranker = Reranker(model=model)
        
        return _reranker.rerank(query, candidates, top_k, max_candidates)
