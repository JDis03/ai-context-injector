## Context

**Current pipeline:**
```
query → embedding → cosine(top-100) → filter(top-k)
```

Cosine similarity measures vector angle, not semantic relevance. Two chunks can have high cosine similarity but low real relevance (e.g., same topic but wrong context).

**Cross-encoder difference:**
```
Bi-encoder (cosine):   encode(query) · encode(doc)        — vectors compared
Cross-encoder:         model(query, doc) → score           — read together
```

Cross-encoders are ~10x slower per pair but 2-3x more accurate. The trade-off is handled by only running the cross-encoder on top-N candidates (30), not the full set.

**Stakeholders:**
- memory-system: uses reranker in `_rank_results()` to improve writeup/code search
- All projects using ai-context-injector search

## Goals / Non-Goals

**Goals:**
- Add cross-encoder reranking as optional post-processing step
- Use lightweight model (80MB, runs on CPU)
- Cache predictions to avoid re-computing for repeated queries
- Graceful fallback to cosine-only if model fails to load
- Simple API: `rerank(query, candidates, top_k)`

**Non-Goals:**
- GPU acceleration (CPU-only for simplicity)
- Custom model training/fine-tuning
- Replacing cosine similarity (reranking is additive)

## Decisions

### Decision 1: Model — `ms-marco-MiniLM-L-6-v2`

**Choice:** Cross-encoder/ms-marco-MiniLM-L-6-v2

**Rationale:**
- 80MB download, runs on CPU
- 50ms per pair (1.5s for top-30)
- Trained on MS MARCO (Bing search queries) — good for informational/search relevance
- Battle-tested in production RAG systems

**Alternatives Considered:**
- ❌ `bge-reranker-large`: 560MB, needs GPU, overkill
- ❌ `cross-encoder/stsb-roberta-base`: Semantic similarity, not search relevance
- ❌ Cohere rerank API: Requires internet, API key, latency

### Decision 2: Pipeline Integration Point

**Choice:** After semantic search, before final top-k selection

```
Current:  top-100 → cosine → top-k
New:      top-100 → cosine → top-30 → reranker → top-k
```

**Rationale:**
- Cosine narrows 100 to 30 (fast)
- Cross-encoder re-ranks 30 to 10 (precise)
- Golden ratio: 3x candidates → 1x results

### Decision 3: Prediction Cache

**Choice:** LRU cache keyed by `(query_hash, chunk_id)`

**Rationale:**
- Same query often re-searched (pentest workflow: "what was that privesc?")
- 1000-entry LRU uses negligible memory
- Cache invalidation: never (predictions are deterministic)

### Decision 4: Lazy Model Loading

**Choice:** Model loaded on first `rerank()` call, not at import

**Rationale:**
- Import should be instant
- If reranking is never used, model is never loaded
- Thread-safe: load once, use many times

### Decision 5: Fallback Strategy

**Choice:** If model fails to load, rerank() returns candidates unchanged with `reranked=False` flag

**Rationale:**
- Search still works (cosine only)
- Caller can check `reranked` field to know if reranking was applied
- No exceptions propagate to user

## Risks / Trade-offs

### Risk 1: 1.5s latency for 30 candidates
**Risk:** Cross-encoder adds ~1.5s to search time

**Mitigation:**
- Only rerank top-30 (not all 100)
- Show cosine results immediately, reranker runs async? (Future)
- Cache predictions for repeated queries

### Risk 2: Model download on first use
**Risk:** First `rerank()` call downloads 80MB model

**Mitigation:**
- `sentence-transformers` caches models in `~/.cache/`
- Warn in docs about first-use latency
- Provide `preload_model()` for eager loading

### Risk 3: Memory footprint
**Risk:** 80MB model + existing embeddings model = ~300MB total

**Mitigation:**
- Models are shared across processes (OS page cache)
- Reranker model is optional (not loaded if not used)
- Acceptable for desktop/server use

## Open Questions

1. **Should reranking be the default or opt-in?**
   - Lean toward opt-in (`use_reranker=True`) for now
   - Make it default once latency is validated

2. **Should we support GPU?**
   - Defer to future release
   - `sentence-transformers` auto-detects CUDA if available, no code change needed

3. **Should we expose the reranker as a standalone MCP tool?**
   - Interesting but out of scope for this change
   - memory-system calls it internally via the Python API
