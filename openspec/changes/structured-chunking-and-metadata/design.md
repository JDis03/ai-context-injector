## Context

**Current State:**
- Chunking is hardcoded to fixed-size chunks (default 1000 chars)
- No metadata support - all documents are treated equally
- Code blocks are chunked like regular text, losing language context
- Search returns all results without filtering capability

**Problem:**
When indexing technical documents (writeups, tutorials, API docs), fixed-size chunking breaks semantic boundaries. A chunk might contain half of a "Reconnaissance" section and half of "Exploitation", making search results imprecise.

**Stakeholders:**
- memory-system: needs writeup indexing with metadata (os, difficulty, tags)
- Future users: need structured chunking for any domain-specific documents

## Goals / Non-Goals

**Goals:**
- Pluggable chunking strategies that respect document structure
- Metadata attachment and filtering without breaking existing code
- Code block extraction with language tags and context
- Backward compatibility with existing indexes

**Non-Goals:**
- Automatic metadata extraction (user provides metadata explicitly)
- Support for non-markdown formats (focus on markdown first)
- Changing existing index format (additive only)

## Decisions

### Decision 1: Strategy Pattern for Chunking

**Choice:** Use strategy pattern with pluggable chunkers

**Rationale:**
- Allows users to choose chunking strategy per document type
- Easy to add new strategies without modifying core code
- Default strategy (`by_size`) maintains backward compatibility

**Alternatives Considered:**
- ❌ Single configurable chunker: Too rigid, can't mix strategies
- ❌ Auto-detect strategy: Too magical, hard to debug

**Implementation:**
```python
class ChunkingStrategy(Protocol):
    def chunk(self, content: str) -> List[Chunk]:
        ...

class BySizeChunker(ChunkingStrategy):
    def chunk(self, content: str) -> List[Chunk]:
        # Current implementation
        ...

class ByMarkdownHeadersChunker(ChunkingStrategy):
    def chunk(self, content: str) -> List[Chunk]:
        # Split on ## headers, preserve section titles
        sections = re.split(r'^##\s+(.+)$', content, flags=re.MULTILINE)
        ...
```

### Decision 2: Metadata as JSON Column

**Choice:** Store metadata as JSON in existing index structure

**Rationale:**
- No schema migration needed (additive)
- Flexible - supports any metadata shape
- Easy to filter with JSON queries

**Alternatives Considered:**
- ❌ Separate metadata table: Adds complexity, requires joins
- ❌ Predefined columns: Not flexible enough for different domains

**Implementation:**
```python
# Indexing
index(content, metadata={"os": "linux", "difficulty": "medium"})

# Storage (in existing index structure)
{
    "content": "...",
    "embedding": [...],
    "metadata": {"os": "linux", "difficulty": "medium"}  # New field
}

# Searching
search(query, filters={"os": "linux"})
# → Filter results where metadata["os"] == "linux"
```

### Decision 3: Code Block Extraction as Preprocessing

**Choice:** Extract code blocks during chunking, store as separate chunks with `chunk_type="code"`

**Rationale:**
- Code blocks can be searched independently
- Preserves language tag and surrounding context
- Doesn't break existing text chunks

**Alternatives Considered:**
- ❌ Post-processing: Loses context of where code appeared
- ❌ Inline markers: Pollutes text chunks with code

**Implementation:**
```python
def extract_code_blocks(content: str) -> List[CodeBlock]:
    pattern = r'```(\w+)\n(.*?)```'
    blocks = []
    for match in re.finditer(pattern, content, re.DOTALL):
        lang = match.group(1)
        code = match.group(2)
        context = get_surrounding_text(content, match.start(), match.end())
        blocks.append(CodeBlock(lang=lang, code=code, context=context))
    return blocks
```

### Decision 4: Backward Compatibility via Defaults

**Choice:** All new parameters are optional with sensible defaults

**Rationale:**
- Existing code continues to work without changes
- Users opt-in to new features explicitly
- No breaking changes to API

**Implementation:**
```python
# Old code still works
index(content)  # Uses by_size, no metadata

# New code opts in
index(content, metadata={"os": "linux"}, chunking_strategy="by_markdown_headers")
```

## Risks / Trade-offs

### Risk 1: Metadata Filtering Performance
**Risk:** Filtering large result sets by metadata could be slow

**Mitigation:**
- Filter AFTER semantic search (smaller result set)
- Add indexes on common metadata fields if needed
- Document recommended metadata structure (flat, not deeply nested)

### Risk 2: Chunking Strategy Mismatch
**Risk:** User indexes with `by_size`, searches expecting `by_markdown_headers` results

**Mitigation:**
- Store chunking strategy in metadata automatically
- Document that strategy is per-document, not per-search
- Provide `reindex()` utility to change strategy

### Risk 3: Code Block Context Loss
**Risk:** Extracting code blocks loses surrounding narrative

**Mitigation:**
- Store surrounding text (2-3 sentences before/after) in `context` field
- Keep code blocks in original text chunks too (duplication is OK)
- Return both code chunk and parent text chunk in results

## Migration Plan

**Phase 1: Add Features (Non-Breaking)**
1. Add `ChunkingStrategy` protocol and implementations
2. Add `metadata` parameter to `index()`
3. Add `filters` parameter to `search()`
4. Add `extract_code_blocks()` utility

**Phase 2: Test with memory-system**
1. Use new features in memory-system writeup parser
2. Validate performance with 100+ writeups
3. Gather feedback on API ergonomics

**Phase 3: Document and Release**
1. Update README with examples
2. Add migration guide for existing users
3. Release as minor version (backward compatible)

**Rollback Strategy:**
- All changes are additive - no rollback needed
- If bugs found, users can continue using old API (no metadata, default chunking)

## Open Questions

1. **Should we support custom chunking strategies via plugins?**
   - Lean toward "yes" but defer to future release
   - Current design allows it (strategy pattern)

2. **Should metadata be validated against a schema?**
   - Lean toward "no" for flexibility
   - Users can validate in their own code if needed

3. **Should we auto-detect code blocks in all chunking strategies?**
   - Lean toward "yes" - make it a preprocessing step
   - Add `extract_code_blocks=True` parameter to `index()`
