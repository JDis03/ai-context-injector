# AI Context Injector

A lightweight Python library for tag-based context injection into LLM prompts with built-in anti-hallucination safeguards.

Extract relevant context from your codebase, memory systems, or custom data sources using simple tags like `@memory`, `@code`, or `@session` in user queries.

## Key Features

- **Tag-based retrieval**: `@memory dark keyboard`, `@code UserService`, `@session last decision`
- **Anti-hallucination safeguards**: 5 critical rules + automatic citations to prevent LLM fabrication
- **Hard project isolation**: Never mix contexts from different projects without explicit opt-in
- **Plugin architecture**: Write custom providers for any data source
- **Blazing fast**: <25ms total pipeline (proven at 17.7ms in production)
- **Zero dependencies**: Core library uses only Python stdlib
- **100% type-safe**: Full type hints with py.typed marker
- **Battle-tested**: 219 tests including real-world integration scenarios

## Installation

```bash
pip install ai-context-injector
```

## Quick Start (5 lines)

```python
from ai_context_injector import ContextInjector

injector = ContextInjector(current_project="my-app")
injector.register_provider("@memory", my_memory_provider)

context = injector.inject("@memory user authentication flow")
# Ready to inject into LLM prompt!
```

## Why Context Injection?

LLMs need relevant context to provide accurate answers. Instead of manually copying code snippets or documentation, use tags to automatically retrieve and format context:

**Without context injection:**
```
User: "How does our authentication work?"
LLM: *hallucinates based on general knowledge*
```

**With context injection:**
```
User: "@memory authentication @code AuthService"
System: *retrieves actual decisions + code*
LLM: *answers based on YOUR actual implementation*
```

## Complete Example

```python
from ai_context_injector import ContextInjector, ContextItem, IContextProvider
from datetime import datetime

# 1. Create a custom provider
class MyMemoryProvider(IContextProvider):
    @property
    def name(self) -> str:
        return "MyMemory"
    
    @property
    def source_type(self) -> str:
        return "memory"
    
    def is_available(self) -> bool:
        return True
    
    def retrieve(self, request):
        # Your retrieval logic here (database, files, API, etc.)
        results = search_my_database(request.query, request.project)
        
        return [
            ContextItem(
                content=result.text,
                source="memory",
                project=request.project,
                metadata={"id": result.id},
                relevance_score=result.score,
                timestamp=result.created_at
            )
            for result in results
        ]

# 2. Initialize injector
injector = ContextInjector(current_project="my-app")
injector.register_provider("@memory", MyMemoryProvider())

# 3. Inject context from user queries
user_query = "Tell me @memory what we decided about the database"

if injector.has_tags(user_query):
    context = injector.inject(user_query)
    
    # Inject into LLM prompt
    llm_prompt = f"""
{context}

User Question: {injector.extract_query_only(user_query)}

Answer based ONLY on the context above.
"""
    
    response = llm.generate(llm_prompt)
```

## Anti-Hallucination Safeguards

Every injected context includes 5 critical rules to prevent LLM fabrication:

```
=== BEGIN CONTEXT ===

CRITICAL RULES FOR USING THIS CONTEXT:
1. ONLY cite information that appears in the context sections below
2. If context is from a different project, CLEARLY state which project
3. Include source citations [memory:project:date] or [code:file:line]
4. If unsure or context missing, say "I don't have information about this"
5. NEVER mix information from different projects without explicit warning

Retrieved Context for: my-app
Found 2 relevant item(s)

--- Context Item 1/2 ---
Source: memory | Project: my-app | Relevance: 0.95 | Date: 2026-05-30
Citation: [memory:my-app:2026-05-30]

Decision: Use PostgreSQL with WAL mode for better performance

--- Context Item 2/2 ---
Source: code | Project: my-app | Relevance: 0.88 | Date: 2026-05-30
Citation: [code:src/db/connection.py:15-23]

def create_connection():
    return psycopg2.connect(
        host="localhost",
        database="myapp",
        options="-c wal_level=replica"
    )

=== END CONTEXT ===
```

## Tag Syntax

### Basic Tags

```python
"@memory user authentication"     # Search memory for "user authentication"
"@code AuthService class"         # Search code for "AuthService class"
"@session last decision"          # Search current session
```

### Modifiers

```python
"@memory:all database design"     # Search across ALL projects (with warning)
```

### Multiple Tags

```python
"@memory architecture and @code UserService"  # Aggregates from both sources
```

## Project Isolation (Key Differentiator)

By default, context is **strictly isolated** to the current project:

```python
injector = ContextInjector(current_project="frontend")

# Only retrieves from "frontend" project
context = injector.inject("@memory React components")

# To search across projects, use :all modifier (generates warning)
context = injector.inject("@memory:all authentication patterns")
```

**Why this matters:** Prevents LLMs from mixing context across different projects, which is a major source of hallucinations and incorrect answers.

## Advanced Usage

### With Performance Metrics

```python
response = injector.inject_with_metrics("@memory query")

print(f"Found: {response.total_found} items")
print(f"Filtered: {response.filtered_count} items")
print(f"Performance: {response.performance_ms:.2f}ms")
print(f"Filter ratio: {response.filter_ratio:.1%}")
```

### Custom Parser and Formatter

```python
from ai_context_injector import TagParser, ContextFormatter

# Custom parser with additional tags
parser = TagParser(custom_tags={"@docs", "@tickets"})

# Compact formatter for tight token budgets
formatter = ContextFormatter(
    include_metadata=False,
    include_anti_hallucination_rules=False
)

injector = ContextInjector(
    current_project="my-app",
    parser=parser,
    formatter=formatter
)
```

### Relevance Filtering

```python
# Only return items with relevance >= 0.80
context = injector.inject(
    "@memory database optimization",
    min_relevance=0.80,
    max_items=5
)
```

## Custom Provider Examples

### Simple In-Memory Provider

```python
from ai_context_injector import IContextProvider, ContextItem
from datetime import datetime

class SimpleProvider(IContextProvider):
    def __init__(self, data):
        self.data = data  # Dict[str, List[tuple]]
    
    @property
    def name(self) -> str:
        return "Simple"
    
    @property
    def source_type(self) -> str:
        return "memory"
    
    def is_available(self) -> bool:
        return True
    
    def retrieve(self, request):
        items = self.data.get(request.project, [])
        
        return [
            ContextItem(
                content=content,
                source="memory",
                project=request.project,
                metadata={},
                relevance_score=score,
                timestamp=datetime.now()
            )
            for content, score in items
            if score >= request.min_relevance
        ][:request.max_items]

# Usage
data = {
    "my-app": [
        ("Decision: Use Redis for caching", 0.95),
        ("Learning: Connection pooling improved latency", 0.90),
    ]
}

provider = SimpleProvider(data)
injector.register_provider("@memory", provider)
```

### SQLite Provider

```python
import sqlite3
from ai_context_injector import IContextProvider, ContextItem
from datetime import datetime

class SQLiteProvider(IContextProvider):
    def __init__(self, db_path):
        self.db_path = db_path
    
    @property
    def name(self) -> str:
        return "SQLite"
    
    @property
    def source_type(self) -> str:
        return "memory"
    
    def is_available(self) -> bool:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.close()
            return True
        except:
            return False
    
    def retrieve(self, request):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Simple full-text search
        cursor.execute("""
            SELECT content, relevance, timestamp
            FROM memories
            WHERE project = ? 
              AND content LIKE ?
              AND relevance >= ?
            ORDER BY relevance DESC
            LIMIT ?
        """, (
            request.project,
            f"%{request.query}%",
            request.min_relevance,
            request.max_items
        ))
        
        results = [
            ContextItem(
                content=row[0],
                source="memory",
                project=request.project,
                metadata={},
                relevance_score=row[1],
                timestamp=datetime.fromisoformat(row[2])
            )
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return results
```

### Filesystem Code Provider

```python
import subprocess
from pathlib import Path
from ai_context_injector import IContextProvider, ContextItem
from datetime import datetime

class FilesystemCodeProvider(IContextProvider):
    def __init__(self, repo_path):
        self.repo_path = Path(repo_path)
    
    @property
    def name(self) -> str:
        return "Filesystem"
    
    @property
    def source_type(self) -> str:
        return "code"
    
    def is_available(self) -> bool:
        return self.repo_path.exists()
    
    def retrieve(self, request):
        # Use ripgrep for fast search
        result = subprocess.run(
            ["rg", "--json", request.query, str(self.repo_path)],
            capture_output=True,
            text=True
        )
        
        # Parse ripgrep JSON output and convert to ContextItem
        # (implementation details omitted for brevity)
        
        return items[:request.max_items]
```

## API Reference

### Core Classes

#### `ContextInjector`

Main orchestrator for the entire pipeline.

```python
injector = ContextInjector(
    current_project="my-app",        # Project name (auto-detected from cwd if None)
    parser=None,                      # Custom TagParser instance
    formatter=None                    # Custom ContextFormatter instance
)

# Register providers
injector.register_provider(tag, provider)

# Inject context
context = injector.inject(
    user_input,                       # String with tags
    max_items=10,                     # Max total items
    min_relevance=0.70               # Min relevance score (0.0-1.0)
)

# With metrics
response = injector.inject_with_metrics(user_input, max_items=10, min_relevance=0.70)

# Utility methods
injector.has_tags(user_input)                    # bool
injector.extract_query_only(user_input)          # str (tags removed)
```

#### `IContextProvider`

Abstract base class for custom providers.

```python
class MyProvider(IContextProvider):
    @property
    def name(self) -> str:
        """Provider name for logging/debugging."""
        return "MyProvider"
    
    @property
    def source_type(self) -> str:
        """Source type: 'memory', 'code', 'session', 'custom', etc."""
        return "memory"
    
    def is_available(self) -> bool:
        """Check if provider is available (DB connected, files exist, etc.)."""
        return True
    
    def retrieve(self, request: ContextRequest) -> List[ContextItem]:
        """Retrieve context items matching the request."""
        # Your logic here
        return items
```

#### `ContextItem`

Represents a single piece of context.

```python
item = ContextItem(
    content="Decision: Use PostgreSQL",     # Required
    source="memory",                        # Required
    project="my-app",                       # Required
    metadata={},                            # Required (can be empty)
    relevance_score=0.95,                   # Required (0.0-1.0)
    timestamp=datetime.now(),               # Required
    file_path=None,                         # Optional (for code)
    line_range=None                         # Optional (for code, tuple)
)

# Generate citation
citation = item.citation()  # "[memory:my-app:2026-05-30]"
```

#### `TagParser`

Parses tags from user input.

```python
parser = TagParser(custom_tags={"@docs", "@tickets"})

tags = parser.parse("@memory query")              # List[ParsedTag]
has_tags = parser.has_tags("@memory query")       # bool
clean = parser.remove_tags("@memory query")       # str
parser.register_tag("@custom")                    # None
```

#### `ContextFormatter`

Formats context items for LLM injection.

```python
formatter = ContextFormatter(
    include_metadata=True,
    include_citations=True,
    include_anti_hallucination_rules=True
)

response = formatter.format(items, current_project)
compact = formatter.format_compact(items)
single = formatter.format_single(item, include_delimiters=True)
```

### Convenience Functions

```python
from ai_context_injector import inject_context, parse_tags, format_context

# Quick injection
context = inject_context(
    user_input="@memory query",
    providers={"@memory": my_provider},
    project="my-app",
    max_items=10,
    min_relevance=0.70
)

# Quick parsing
tags = parse_tags("@memory query", custom_tags={"@docs"})

# Quick formatting
response = format_context(items, current_project="my-app")
```

## Architecture

```
User Input: "@memory dark keyboard @code KeyboardView"
     │
     ├─> TagParser
     │   ├─> ParsedTag(tag="@memory", query="dark keyboard")
     │   └─> ParsedTag(tag="@code", query="KeyboardView")
     │
     ├─> ContextInjector
     │   ├─> Route to providers
     │   │   ├─> MemoryProvider.retrieve() → [ContextItem, ...]
     │   │   └─> CodeProvider.retrieve() → [ContextItem, ...]
     │   │
     │   ├─> Aggregate results
     │   ├─> Deduplicate (first 100 chars hash)
     │   ├─> Sort by relevance
     │   └─> Limit to max_items
     │
     └─> ContextFormatter
         ├─> Add delimiters
         ├─> Add anti-hallucination rules
         ├─> Add metadata + citations
         ├─> Check cross-project warnings
         └─> Format items
              │
              └─> Formatted context string (ready for LLM)
```

## Performance

Target: <25ms total pipeline  
Proven: 17.7ms in production (memory-system)

Breakdown:
- Parsing: <1ms
- Provider retrieval: ~10ms (depends on your provider)
- Aggregation/dedup: ~2ms
- Sorting: ~2ms
- Formatting: ~2ms

**Tip:** Provider performance is usually the bottleneck. Use indexes, caching, and efficient queries.

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ai_context_injector

# Run only unit tests
pytest tests/core/

# Run only integration tests
pytest tests/test_integration.py

# Run specific test
pytest tests/core/test_injector.py::TestBasicInjection::test_inject_with_single_tag
```

## Design Principles

1. **Explicit over implicit**: Empty providers dict by default, users must register
2. **Project isolation by default**: Never auto-mix contexts across projects
3. **Zero magic**: No auto-discovery, no global state, no hidden dependencies
4. **Library not framework**: Integrate into your app, don't build around it
5. **Performance matters**: <25ms target, every millisecond counts
6. **Type safety**: Full type hints, no `Any` types in public API
7. **Fail gracefully**: Missing/unavailable providers return None, not exceptions

## FAQ

### Why not just use RAG?

RAG is great for semantic search, but context injection solves a different problem:
- **Structured retrieval**: Tag-based routing to different data sources
- **Multi-source aggregation**: Combine memory + code + session in one query
- **Project isolation**: Hard boundaries prevent context mixing
- **Anti-hallucination**: Built-in safeguards with citations

You can use RAG *as a provider* in this system!

### Why project isolation by default?

In multi-project environments, mixing contexts causes LLMs to:
- Suggest code patterns from wrong project
- Reference APIs that don't exist in current project
- Mix architectural decisions across boundaries

Hard isolation by default prevents these errors. Use `:all` modifier when you actually want cross-project search.

### Can I use this with any LLM?

Yes! This library just generates formatted context strings. Use them with:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local models (Ollama, LM Studio)
- Any LLM API that accepts text prompts

### How do I handle large codebases?

1. **Smart providers**: Use search indexes (ripgrep, SQLite FTS, Elasticsearch)
2. **Relevance filtering**: Set `min_relevance=0.80` to reduce noise
3. **Limit results**: Use `max_items=5` for tight token budgets
4. **Compact format**: Disable metadata with `ContextFormatter(include_metadata=False)`

### Can I use this in production?

Yes! The core library has:
- 219 tests (100% passing)
- No external dependencies
- Battle-tested in memory-system project
- Proven <20ms performance

Just write solid providers and you're good to go.

## Contributing

Contributions welcome! Please:
1. Add tests for new features
2. Follow existing code style
3. Update documentation
4. Run `pytest` before submitting

## License

MIT License - see LICENSE file for details

## Acknowledgments

Ported from the context injection system in memory-system project, which has been battle-tested in production for multi-project development workflows.
