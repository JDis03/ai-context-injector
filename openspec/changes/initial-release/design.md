# Design: Initial Release - AI Context Injector

## Context

### Background

AI Context Injector is extracted from a working implementation in hackDark (1,473 lines, 17.7ms performance proven). The goal is to create a clean, framework-agnostic Python library that any developer can use regardless of their LLM provider or infrastructure.

### Current State (hackDark)

The existing implementation has proven functionality but tight coupling:

```python
# Current (hackDark-coupled)
from project_memory import ProjectMemory  # Requires hackDark database
from config_manager import get_project_paths  # Hardcoded paths

injector = ContextInjector()  # Auto-detects project from cwd
result = injector.inject("@memory query")  # Uses hackDark's memory.db
```

Problems:
- Direct import of `ProjectMemory` from hackDark
- Hardcoded project paths in `_detect_project()`
- No way to configure providers at runtime
- Assumes `~/.hackdark/memory.db` exists

### Constraints

1. **Backwards compatibility not required** - This is a new library
2. **Python 3.9+** - No need to support older versions
3. **No async in v1.0** - Sync-first, async can be added in v1.1
4. **Minimal dependencies** - Core should only need `dataclasses` (stdlib)

### Stakeholders

- **Primary**: Developers building AI-powered tools who need context injection
- **Secondary**: hackDark (will adopt this as dependency after launch)

## Goals / Non-Goals

**Goals:**
- Clean 5-line usage example that works out of the box
- Plugin system allowing custom providers without forking
- Zero framework dependencies (works with OpenAI, Anthropic, Ollama, etc.)
- Hard project isolation by default (never auto-mix contexts)
- Research-backed anti-hallucination formatting
- <20ms query performance maintained
- PyPI installable with `pip install ai-context-injector`

**Non-Goals:**
- Embeddings/vector search (v1 uses keyword matching; document how to add via plugin)
- Async API (add in v1.1)
- Web UI or REST API (pure Python library)
- Built-in memory persistence (users bring their own storage)
- Multi-tenancy or cloud features
- IDE extensions (VSCode, IntelliJ, etc.)

## Decisions

### Decision 1: Provider Registration Architecture

**Choice**: Dictionary-based registration with interface contracts

**Rationale**: Simpler than entry points, explicit, easy to understand

**Alternatives Considered**:
- Entry points (setuptools): More "Pythonic" but adds complexity for simple use cases
- Decorator-based: Magical, harder to debug
- Class registry pattern: Overkill for 3-5 providers

**Implementation**:
```python
from ai_context_injector import ContextInjector, IContextProvider

class MyProvider(IContextProvider):
    def retrieve(self, request): ...
    def is_available(self) -> bool: ...
    @property
    def name(self) -> str: ...
    @property
    def source_type(self) -> str: ...

injector = ContextInjector(
    providers={
        '@memory': MyProvider(db_path='./data.db'),
        '@custom': AnotherProvider(),
    }
)
```

### Decision 2: Configuration Model

**Choice**: Configuration via constructor arguments, no config files in v1

**Rationale**: 
- Explicit is better than implicit
- No magic file loading that could fail
- Users control their own config management

**Alternatives Considered**:
- YAML/JSON config files: Adds file I/O complexity, parsing errors
- Environment variables: Not suitable for complex config (providers)
- Pydantic models: Adds dependency

**Implementation**:
```python
injector = ContextInjector(
    providers={...},
    default_max_items=10,
    default_min_relevance=0.70,
    include_anti_hallucination_rules=True,
    include_citations=True,
)
```

### Decision 3: Package Structure

**Choice**: Flat structure with clear submodules

**Rationale**: Easy to navigate, mirrors logical organization

```
ai_context_injector/
├── __init__.py          # Public exports
├── core/
│   ├── __init__.py
│   ├── types.py         # ContextItem, ContextRequest, ContextResponse, ParsedTag
│   ├── parser.py        # TagParser
│   ├── formatter.py     # ContextFormatter
│   └── injector.py      # ContextInjector (main orchestrator)
├── providers/
│   ├── __init__.py      # IContextProvider interface
│   └── base.py          # Abstract base class
└── py.typed             # PEP 561 marker
```

**Alternatives Considered**:
- Single module: Would become unwieldy as code grows
- Deep nesting: Harder to import from

### Decision 4: Tag System

**Choice**: Keep existing tag syntax (`@memory`, `@code`, `@session`) with optional modifiers

**Rationale**: Proven UX from hackDark, matches Continue.dev patterns

**Tags supported**:
- `@memory query` - Search project memory
- `@memory:all query` - Cross-project search (explicit opt-in)
- `@code query` - Search codebase
- `@session query` - Search session history

**Custom tags**:
```python
# Users can register any tag they want
injector = ContextInjector(
    providers={
        '@docs': DocumentationProvider(),
        '@tickets': JiraProvider(api_key=...),
    }
)
```

### Decision 5: Anti-Hallucination Strategy

**Choice**: Mandatory delimiters + optional metadata/citations/rules

**Rationale**: Research shows delimiters are critical; other features are configurable based on token budget

**Always included**:
```
=== BEGIN CONTEXT ===
...content...
=== END CONTEXT ===
```

**Configurable**:
- Anti-hallucination rules (5 critical rules)
- Per-item metadata (source, project, timestamp, relevance)
- Citations ([memory:project:date])
- Cross-project warnings

**Implementation**:
```python
formatter = ContextFormatter(
    include_metadata=True,          # Default: True
    include_citations=True,         # Default: True
    include_anti_hallucination_rules=True,  # Default: True
)

# Or use compact format for tight token budgets
formatted = formatter.format_compact(items)
```

### Decision 6: Project Isolation

**Choice**: Hard isolation by default, explicit `:all` modifier for cross-project

**Rationale**: Continue.dev's weak isolation causes confusion; explicit is safer

**Behavior**:
- `@memory query` - Only searches current project
- `@memory:all query` - Searches all projects, adds warning
- Cross-project results always include warning in output

### Decision 7: Error Handling

**Choice**: Return empty results on provider errors, never raise exceptions from public API

**Rationale**: Context injection is optional enhancement; failures shouldn't break the user's application

**Implementation**:
```python
def inject(self, user_input: str) -> Optional[str]:
    """Returns None if no tags found or all providers fail."""
    try:
        # ... implementation
    except Exception as e:
        self._log_error(e)  # Internal logging
        return None  # Graceful degradation
```

**Alternatives Considered**:
- Raise exceptions: Would require try/catch in every usage
- Return error objects: More complex API
- Callbacks: Overkill for v1

### Decision 8: No Built-in Providers

**Choice**: Ship with `IContextProvider` interface only, no built-in implementations

**Rationale**: 
- Keeps core library minimal and dependency-free
- Users don't pay for providers they don't use
- Avoids coupling to any specific storage backend

**Alternatives Considered**:
- Include SQLite provider: Adds sqlite3 dependency (stdlib but still coupling)
- Include filesystem provider: Would make assumptions about project structure

**Example providers will be in `examples/` directory**:
```
examples/
├── sqlite_memory_provider.py    # Port of hackDark's MemoryProvider
├── openai_integration.py        # Full OpenAI usage example
├── anthropic_integration.py     # Full Anthropic usage example
└── ollama_integration.py        # Full Ollama usage example
```

## Risks / Trade-offs

### [Low Risk] Performance Regression

**Risk**: Refactoring might slow down queries from proven 17.7ms

**Mitigation**: 
- Benchmark suite from day 1
- CI fails if median query time >25ms
- No new allocations in hot path

### [Medium Risk] Plugin API Instability

**Risk**: Users build providers against v1.0 API, we need breaking changes in v1.1

**Mitigation**:
- Keep `IContextProvider` interface minimal (4 methods)
- Document that interface may evolve before v2.0
- Semantic versioning: breaking changes = major version bump

### [Medium Risk] Adoption Friction

**Risk**: No built-in providers means more setup work for users

**Mitigation**:
- Comprehensive examples that work copy-paste
- README with 5-line quickstart using example provider
- Document common patterns (SQLite, filesystem, API-backed)

### [Low Risk] Tag Conflicts

**Risk**: User wants `@docs` but it conflicts with future built-in

**Mitigation**:
- Reserve only `@memory`, `@code`, `@session` for future built-in
- Document reserved tags in API docs
- Users can override even reserved tags (their config wins)

### [Trade-off] Sync-Only API

**Benefit**: Simpler API, no async complexity
**Cost**: Users with async codebases need `asyncio.to_thread()`
**Decision**: Accept for v1.0, add native async in v1.1

### [Trade-off] No Auto-Discovery

**Benefit**: Explicit configuration, no magic
**Cost**: Users must manually register each provider
**Decision**: Accept for v1.0, consider entry points in v1.1

## Public API Surface

### Core Classes

```python
# Main entry point
from ai_context_injector import ContextInjector

# Types for building providers
from ai_context_injector import (
    IContextProvider,
    ContextItem,
    ContextRequest,
    ContextResponse,
    ParsedTag,
)

# Utilities
from ai_context_injector import (
    TagParser,
    ContextFormatter,
)
```

### Minimal Usage Example

```python
from ai_context_injector import ContextInjector, IContextProvider, ContextItem, ContextRequest

class SimpleMemoryProvider(IContextProvider):
    """Example provider that searches a list of strings."""
    
    def __init__(self, memories: list[str]):
        self.memories = memories
    
    @property
    def name(self) -> str:
        return "Simple Memory"
    
    @property
    def source_type(self) -> str:
        return "memory"
    
    def is_available(self) -> bool:
        return True
    
    def retrieve(self, request: ContextRequest) -> list[ContextItem]:
        # Simple keyword matching
        results = []
        for memory in self.memories:
            if request.query.lower() in memory.lower():
                results.append(ContextItem(
                    content=memory,
                    source=self.source_type,
                    project=request.project,
                    metadata={},
                    relevance_score=0.9,
                    timestamp=datetime.now(),
                ))
        return results[:request.max_items]

# Usage
injector = ContextInjector(
    providers={'@memory': SimpleMemoryProvider(["Decision: Use SQLite", "Learning: WAL mode is faster"])},
    project="my-project"
)

context = injector.inject("@memory SQLite decision")
# Returns formatted context with anti-hallucination rules
```

## Open Questions

1. **Package name availability**: Need to verify `ai-context-injector` is available on PyPI
   - Fallback: `context-injector`, `llm-context-injector`

2. **Type stubs**: Include inline types or separate stubs package?
   - Leaning: Inline types with `py.typed` marker

3. **Logging**: Use stdlib logging or structlog?
   - Leaning: stdlib logging with NullHandler default

4. **Version strategy**: CalVer or SemVer?
   - Leaning: SemVer (clearer for breaking changes)
