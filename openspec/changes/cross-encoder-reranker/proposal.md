## Why

Current search returns results ranked by cosine similarity only. Cosine similarity measures vector proximity but does NOT understand semantic relevance between a query and a document. A cross-encoder reads query and document TOGETHER, producing a true relevance score. This significantly improves search quality for technical content like writeups, code searches, and documentation lookups.

## What Changes

- Add `rerank(query, candidates, top_k)` function using a cross-encoder model
- Bundle `ms-marco-MiniLM-L-6-v2` (80MB, 50ms per pair) as default model
- Support custom cross-encoder models via HuggingFace model ID
- Integrate into search pipeline: top-100 embedding results → top-30 → reranker → top-10
- Fall back to cosine-only if re-ranker fails (graceful degradation)
- Cache re-ranker predictions for repeated query-document pairs

## Capabilities

### New Capabilities
- `cross-encoder-reranker`: Load a cross-encoder model and re-rank candidate documents by true semantic relevance. Supports default model, custom models, graceful fallback, and prediction caching.

### Modified Capabilities
<!-- None -->

## Impact

**Code:**
- `ai_context_injector/reranker.py`: New module with `Reranker` class
- `ai_context_injector/search.py`: Integrate reranker into search pipeline
- `ai_context_injector/cache.py`: Extend embedding cache for reranker predictions

**Dependencies:**
- `sentence-transformers` (already available, used by existing embedding pipeline)
- No new external services (runs locally)

**Backward Compatibility:**
- Fully additive — reranking is opt-in via `use_reranker=True` parameter
- Default behavior unchanged (cosine-only)
