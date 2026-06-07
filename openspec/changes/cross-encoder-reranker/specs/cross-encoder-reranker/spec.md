## ADDED Requirements

### Requirement: Load cross-encoder model lazily
The system SHALL load the cross-encoder model on first use, not at import time.

#### Scenario: Import is instant
- **WHEN** module is imported with `from ai_context_injector import Reranker`
- **THEN** import completes in under 100ms without model download

#### Scenario: First rerank loads model
- **WHEN** `rerank()` is called for the first time
- **THEN** model is downloaded (if not cached) and loaded into memory

#### Scenario: Subsequent calls reuse model
- **WHEN** `rerank()` is called after model is loaded
- **THEN** no additional download or loading occurs

### Requirement: Re-rank candidates by relevance
The system SHALL accept a query and candidate documents, returning them reordered by true relevance score.

#### Scenario: Re-ranking improves order
- **WHEN** `rerank("python exploit", [chunk1_about_java, chunk2_about_python_exploit])` is called
- **THEN** chunk2 receives higher score than chunk1

#### Scenario: Top-k truncation
- **WHEN** `rerank(query, candidates, top_k=3)` is called with 10 candidates
- **THEN** only top 3 are returned

#### Scenario: Empty candidates returns empty
- **WHEN** `rerank(query, candidates=[])` is called
- **THEN** empty list is returned with `reranked=False`

### Requirement: Use default model ms-marco-MiniLM-L-6-v2
The system SHALL use `cross-encoder/ms-marco-MiniLM-L-6-v2` as the default model.

#### Scenario: Default model loads successfully
- **WHEN** `Reranker()` is instantiated without model parameter
- **THEN** `cross-encoder/ms-marco-MiniLM-L-6-v2` is loaded

#### Scenario: Custom model via parameter
- **WHEN** `Reranker(model="cross-encoder/stsb-roberta-base")` is instantiated
- **THEN** specified model is loaded instead of default

### Requirement: Cache predictions for repeated queries
The system SHALL cache re-ranker predictions by `(query_hash, chunk_content_hash)`.

#### Scenario: Repeated query uses cache
- **WHEN** same query and same chunk content are passed to `rerank()` twice
- **THEN** second call returns cached score without model inference

#### Scenario: Different query bypasses cache
- **WHEN** different query is passed to `rerank()`
- **THEN** model inference runs fresh

#### Scenario: Cache is bounded
- **WHEN** cache exceeds 1000 entries
- **THEN** least recently used entries are evicted

### Requirement: Graceful fallback on model failure
The system SHALL return cosine-ordered candidates unchanged if the model fails to load or crashes.

#### Scenario: Model download fails
- **WHEN** model download fails due to network error
- **THEN** `rerank()` returns candidates unchanged with `reranked=False` and a warning

#### Scenario: Model inference crashes
- **WHEN** model raises exception during prediction
- **THEN** `rerank()` catches exception, returns candidates unchanged with `reranked=False`

#### Scenario: Fallback preserves original order
- **WHEN** fallback occurs
- **THEN** candidates maintain their original cosine-similarity order

### Requirement: Batch prediction for efficiency
The system SHALL predict all query-document pairs in a single batch.

#### Scenario: Single model call for all candidates
- **WHEN** `rerank(query, [c1, c2, c3])` is called
- **THEN** model.predict() is called once with 3 pairs, not 3 separate calls

#### Scenario: Batch size respects memory limits
- **WHEN** more than 50 candidates are passed
- **THEN** predictions are processed in batches of 50

### Requirement: Return structured results with scores
The system SHALL return results with original chunk data plus reranking metadata.

#### Scenario: Result includes score
- **WHEN** reranking succeeds
- **THEN** each result includes `rerank_score` field with float value

#### Scenario: Result includes flag
- **WHEN** reranking succeeds
- **THEN** response includes `reranked=True`

#### Scenario: Original fields preserved
- **WHEN** reranking modifies order
- **THEN** each result retains original `content`, `metadata`, `cosine_score` fields
