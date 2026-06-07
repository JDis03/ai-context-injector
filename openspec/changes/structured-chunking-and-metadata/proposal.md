## Why

Current chunking is fixed-size and ignores document structure. When indexing technical documents (writeups, tutorials, API docs), we lose semantic boundaries like sections, code blocks, and metadata. This makes search results less precise because chunks mix unrelated content. We need structured chunking that respects document boundaries and preserves metadata for filtering.

## What Changes

- Add configurable chunking strategies: `by_size` (current), `by_markdown_headers`, `by_paragraph`
- Add metadata support: attach arbitrary JSON metadata to indexed documents
- Add metadata filtering: search with filters like `{"os": "linux", "difficulty": "medium"}`
- Add code block extraction: detect and index code blocks separately with language and context
- Maintain backward compatibility: existing code continues to work with default `by_size` strategy

## Capabilities

### New Capabilities
- `chunking-strategies`: Pluggable chunking strategies that respect document structure (markdown headers, paragraphs, custom delimiters)
- `metadata-filtering`: Attach and filter by arbitrary JSON metadata during indexing and search
- `code-extraction`: Extract and index code blocks separately with language tags and surrounding context

### Modified Capabilities
<!-- No existing capabilities are being modified - this is purely additive -->

## Impact

**Code:**
- `ai_context_injector/chunker.py`: Add strategy pattern for chunking
- `ai_context_injector/indexer.py`: Accept metadata parameter, store in index
- `ai_context_injector/searcher.py`: Add filters parameter, apply metadata filtering
- `ai_context_injector/extractors.py`: New module for code block extraction

**APIs:**
- `index(content, metadata={}, chunking_strategy="by_size")`: Add optional metadata and strategy
- `search(query, filters={})`: Add optional metadata filters
- `extract_code_blocks(content)`: New function returning code blocks with context

**Dependencies:**
- No new dependencies required (uses existing regex and markdown parsing)

**Backward Compatibility:**
- All changes are additive with sensible defaults
- Existing code continues to work without modification
