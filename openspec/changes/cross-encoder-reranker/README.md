# Cross-Encoder Reranker

**Status:** Ready for implementation ✅

## What This Change Does

Adds a cross-encoder reranker to ai-context-injector that reads query+document TOGETHER to produce true relevance scores. Replaces cosine-only ranking at the final stage of search.

## Why This Matters

Cosine similarity measures vector angle but doesn't understand semantic relevance. A cross-encoder model reads query and document simultaneously and scores how well they match — 2-3x more accurate than vector similarity alone.

## Pipeline Change

```
BEFORE: top-100 → cosine → top-10
AFTER:  top-100 → cosine → top-30 → reranker → top-10
```

## Implementation Status

All artifacts complete:
- ✅ proposal.md
- ✅ design.md  
- ✅ specs/cross-encoder-reranker/spec.md
- ✅ tasks.md (44 tasks across 8 groups)

## Key Decisions

| Decision | Choice |
|----------|--------|
| Model | `cross-encoder/ms-marco-MiniLM-L-6-v2` (80MB, CPU) |
| Integration | After cosine, top-30 → rerank → top-10 |
| Loading | Lazy (first `rerank()` call) |
| Fallback | Cosine-only if model fails |
| Cache | 1000-entry LRU by `(query, chunk_id)` |

## API Preview

```python
from ai_context_injector import Reranker, search

# Direct rerank
reranker = Reranker()
results = reranker.rerank("kernel exploit", candidates, top_k=5)
# → candidates reordered with rerank_score and reranked=True

# Integrated search
results = search("privesc", use_reranker=True)
# → pipeline: embeddings → cosine top-30 → reranker → top-10
```

## After Implementation

memory-system uses it in `_rank_results()`:
```python
from ai_context_injector import Reranker

reranker = Reranker()
scored = reranker.rerank(query, top_30, top_k=10)
```
