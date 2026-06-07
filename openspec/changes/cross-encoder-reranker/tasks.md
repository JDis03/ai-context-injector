## 1. Core Reranker Module

- [ ] 1.1 Create `ai_context_injector/reranker.py` with `Reranker` class
- [ ] 1.2 Implement lazy model loading via `_load_model()` method
- [ ] 1.3 Implement `rerank(query, candidates, top_k)` public API
- [ ] 1.4 Format candidates as `(query, text)` pairs for cross-encoder
- [ ] 1.5 Batch predict all pairs in single model call
- [ ] 1.6 Sort by cross-encoder score descending
- [ ] 1.7 Return top_k with `rerank_score` and `reranked=True` fields

## 2. Model Management

- [ ] 2.1 Default model: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- [ ] 2.2 Accept custom model via constructor parameter
- [ ] 2.3 Handle model download on first use with user-visible message
- [ ] 2.4 Add `preload()` method for eager model loading
- [ ] 2.5 Thread-safe singleton pattern for model instance

## 3. Prediction Cache

- [ ] 3.1 Implement LRU cache with 1000 entry limit
- [ ] 3.2 Cache key: `hash(query + chunk_content)`
- [ ] 3.3 Check cache before model inference
- [ ] 3.4 Store computed scores in cache after inference
- [ ] 3.5 Add `clear_cache()` method for testing
- [ ] 3.6 Add `cache_stats()` method returning hits/misses

## 4. Fallback & Error Handling

- [ ] 4.1 Catch model download failures → return candidates unchanged
- [ ] 4.2 Catch model inference exceptions → return candidates unchanged
- [ ] 4.3 Set `reranked=False` on all fallback results
- [ ] 4.4 Log warning on first fallback, debug on subsequent
- [ ] 4.5 Preserve original cosine score order on fallback

## 5. Search Pipeline Integration

- [ ] 5.1 Add `use_reranker: bool = False` parameter to `search()` function
- [ ] 5.2 In search pipeline: top-100 → cosine top-30 → reranker → top_k
- [ ] 5.3 Only rerank if `use_reranker=True` and more than 1 candidate
- [ ] 5.4 Return `reranked` flag in search response
- [ ] 5.5 Add `rerank_time_ms` to search performance metrics

## 6. API Surface

- [ ] 6.1 `Reranker()` — constructor with optional model parameter
- [ ] 6.2 `reranker.rerank(query, candidates, top_k)` — main method
- [ ] 6.3 `reranker.preload()` — eager load
- [ ] 6.4 `reranker.clear_cache()` — reset cache
- [ ] 6.5 `reranker.cache_stats()` — cache metrics
- [ ] 6.6 Top-level convenience: `from ai_context_injector import rerank`
- [ ] 6.7 Export `Reranker` in `__init__.py`

## 7. Tests

- [ ] 7.1 Test lazy loading (import without model download)
- [ ] 7.2 Test rerank reorders by relevance (mock model.predict)
- [ ] 7.3 Test rerank returns top_k
- [ ] 7.4 Test empty candidates returns empty
- [ ] 7.5 Test cache hit (mock to verify no second predict call)
- [ ] 7.6 Test cache eviction at 1000 entries
- [ ] 7.7 Test fallback on model error
- [ ] 7.8 Test fallback preserves original order
- [ ] 7.9 Test `reranked=True/False` in results
- [ ] 7.10 Test custom model parameter
- [ ] 7.11 Test `search()` pipeline with `use_reranker=True`
- [ ] 7.12 Test `search()` pipeline default behavior unchanged

## 8. Documentation

- [ ] 8.1 Update README with reranker usage example
- [ ] 8.2 Document model options (default + custom)
- [ ] 8.3 Document performance characteristics (latency, memory)
- [ ] 8.4 Add docstrings to all public methods
- [ ] 8.5 Update CHANGELOG.md
- [ ] 8.6 Bump version to 1.2.0
