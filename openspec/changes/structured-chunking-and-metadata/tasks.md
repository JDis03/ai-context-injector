## 1. Core Infrastructure

- [ ] 1.1 Create `ChunkingStrategy` protocol in `ai_context_injector/chunking.py`
- [ ] 1.2 Implement `BySizeChunker` (refactor existing logic)
- [ ] 1.3 Implement `ByMarkdownHeadersChunker` with section title extraction
- [ ] 1.4 Implement `ByParagraphChunker` (split on double newlines)
- [ ] 1.5 Add `max_chunk_size` enforcement to all chunkers

## 2. Metadata Support

- [ ] 2.1 Add `metadata: dict` parameter to `index()` function
- [ ] 2.2 Store metadata in index structure (JSON field)
- [ ] 2.3 Auto-generate metadata fields (`chunking_strategy`, `indexed_at`)
- [ ] 2.4 Validate metadata is JSON-serializable
- [ ] 2.5 Add `filters: dict` parameter to `search()` function
- [ ] 2.6 Implement metadata filtering logic (post-semantic-search)

## 3. Code Block Extraction

- [ ] 3.1 Create `ai_context_injector/extractors.py` module
- [ ] 3.2 Implement `extract_code_blocks()` function (triple backtick and tilde)
- [ ] 3.3 Capture surrounding context (200 chars before/after)
- [ ] 3.4 Respect section boundaries when extracting context
- [ ] 3.5 Add `extract_code_blocks: bool` parameter to `index()`
- [ ] 3.6 Create separate chunks for code blocks with `chunk_type="code"` metadata
- [ ] 3.7 Add `parent_chunk_id` reference to code chunks

## 4. API Updates

- [ ] 4.1 Update `index()` signature: `index(content, metadata={}, chunking_strategy="by_size", extract_code_blocks=False, max_chunk_size=1000)`
- [ ] 4.2 Update `search()` signature: `search(query, filters={})`
- [ ] 4.3 Ensure backward compatibility (all new params optional with defaults)
- [ ] 4.4 Update return types to include metadata in results

## 5. Tests

- [ ] 5.1 Test `BySizeChunker` (existing behavior unchanged)
- [ ] 5.2 Test `ByMarkdownHeadersChunker` (section splitting, title extraction, nested headers)
- [ ] 5.3 Test `ByParagraphChunker` (paragraph splitting)
- [ ] 5.4 Test max_chunk_size enforcement across all strategies
- [ ] 5.5 Test metadata storage and retrieval
- [ ] 5.6 Test metadata filtering (exact match, multiple criteria, nested fields)
- [ ] 5.7 Test code block extraction (fenced blocks, language tags, context)
- [ ] 5.8 Test code chunk creation and parent references
- [ ] 5.9 Test backward compatibility (old API still works)
- [ ] 5.10 Test invalid inputs (non-JSON metadata, invalid strategy name)

## 6. Documentation

- [ ] 6.1 Update README with chunking strategy examples
- [ ] 6.2 Update README with metadata filtering examples
- [ ] 6.3 Update README with code extraction examples
- [ ] 6.4 Add migration guide for existing users
- [ ] 6.5 Document recommended metadata structure (flat, common fields)
- [ ] 6.6 Add docstrings to all new functions and classes

## 7. Integration

- [ ] 7.1 Verify integration with memory-system (no breaking changes)
- [ ] 7.2 Test with real writeup documents (100+ files)
- [ ] 7.3 Benchmark performance (indexing and search with metadata filtering)
- [ ] 7.4 Update CHANGELOG.md with new features
- [ ] 7.5 Bump version to next minor (backward compatible)
