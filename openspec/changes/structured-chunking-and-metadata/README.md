# Structured Chunking and Metadata

**Status:** Ready for implementation ✅

## What This Change Does

Adds structured chunking strategies, metadata support, and code block extraction to ai-context-injector. This enables domain-specific indexing (like writeups, tutorials, API docs) with filtering and precise search.

## Why This Matters

Current fixed-size chunking breaks semantic boundaries. When indexing technical documents, we lose structure like sections, code blocks, and metadata. This change makes ai-context-injector more powerful for ALL projects that need structured document indexing.

## Key Features

1. **Pluggable Chunking Strategies**
   - `by_size` (current default)
   - `by_markdown_headers` (respects ## sections)
   - `by_paragraph` (splits on double newlines)

2. **Metadata Support**
   - Attach arbitrary JSON metadata to documents
   - Filter search results by metadata
   - Auto-generated fields (chunking_strategy, indexed_at)

3. **Code Block Extraction**
   - Extract ```lang blocks separately
   - Preserve surrounding context
   - Index as separate chunks with language tags

## Implementation Status

All artifacts complete:
- ✅ proposal.md
- ✅ design.md
- ✅ specs/ (3 capabilities)
- ✅ tasks.md (35 tasks across 7 groups)

## Next Steps

### Option 1: Implement Now
```bash
cd /home/dark/Project/ai-context-injector
npx --package=openspec openspec apply structured-chunking-and-metadata
# Follow the task checklist
```

### Option 2: Review First
Read the artifacts in order:
1. `proposal.md` - Why and what
2. `design.md` - How and decisions
3. `specs/*/spec.md` - Requirements and scenarios
4. `tasks.md` - Implementation checklist

### Option 3: Delegate to Agent
```bash
# Use task03 agent to implement
@task03 "Implement structured-chunking-and-metadata change in ai-context-injector"
```

## After Implementation

Once this is done in ai-context-injector, you can use it in memory-system:

```python
# In memory-system writeup parser
from ai_context_injector import index, search

# Index writeup with metadata
index(
    content=writeup_content,
    metadata={"os": "linux", "difficulty": "medium", "tags": ["web", "sqli"]},
    chunking_strategy="by_markdown_headers",
    extract_code_blocks=True
)

# Search with filters
results = search(
    query="privilege escalation kernel exploit",
    filters={"os": "linux", "section": "privesc"}
)
```

## Questions?

- **Why ai-context-injector and not memory-system?** Generic features belong in the library, domain-specific features (writeup parser) belong in memory-system.
- **Breaking changes?** None. All new features are opt-in with sensible defaults.
- **Performance impact?** Minimal. Metadata filtering happens after semantic search (small result set).

---

**Ready to implement?** Start with `tasks.md` and work through the checklist.
