# Reference Implementation

This project is based on a working implementation from [hackDark](https://github.com/dark/hackDark).

## What Already Works

The following code has been tested and proven in hackDark:

### Core Components (1,473 lines)
- **Tag Parser** (196 lines) - Regex-based parsing of @memory, @code, @session tags
- **Context Formatter** (216 lines) - Anti-hallucination formatting with delimiters and citations
- **Context Injector** (292 lines) - Main orchestration logic
- **Type System** (154 lines) - Clean dataclasses for all data types
- **Memory Provider** (263 lines) - Integration with SQLite-based memory system

### Performance Proven
```
Query: @memory WAL mode database
Performance: 17.7ms ✅
Total found: 1
After filtering: 1
Filter ratio: 100.0%
```

Target: <150ms
Achieved: 17.7ms (8.5x better)

### Test Results
All parser tests passing:
- Basic tag parsing: `@memory query` ✅
- Modifier parsing: `@memory:all query` ✅
- Embedded tags: `text @memory query more text` ✅

### Anti-Hallucination Techniques (Research-Backed)

The implementation uses industry consensus from:
- Continue.dev
- Cursor AI
- OpenAI Assistants
- n8n
- Academic papers on LLM hallucination

**ALL professional systems use:**
1. Clear delimiters (=== BEGIN/END ===)
2. Metadata (source, project, timestamp, relevance)
3. Citations ([memory:project:date])
4. Explicit anti-hallucination rules
5. Relevance filtering (>0.70 threshold)

**NONE do:**
- Invisible auto-recall
- Injection without tags
- Context without metadata
- Auto-mix projects without warning

## What Needs Improvement

### 1. Remove hackDark Dependencies
Current code imports from hackDark-specific modules:
```python
from project_memory import ProjectMemory  # Make this pluggable
from config_manager import get_project_paths  # Make this configurable
```

### 2. Clean API Design
Current (hackDark-coupled):
```python
from context import inject_context
result = inject_context("@memory query")  # Assumes hackDark database
```

Desired (framework-agnostic):
```python
from ai_context_injector import ContextInjector
from ai_context_injector.providers import SQLiteMemoryProvider

injector = ContextInjector(
    providers={
        'memory': SQLiteMemoryProvider(db_path='./my_memory.db'),
        'code': MyCustomCodeProvider(),
    }
)

result = injector.inject("@memory query")
print(result.formatted_context)
```

### 3. Plugin System
Enable custom providers without modifying core:
```python
from ai_context_injector import IContextProvider

class MyCustomProvider(IContextProvider):
    def retrieve(self, request):
        # Custom logic here
        return [ContextItem(...)]
    
    # ... implement interface

injector.register_provider('@custom', MyCustomProvider())
```

### 4. Better Documentation
Current: Code comments only
Needed:
- Comprehensive README with examples
- API documentation (docstrings + Sphinx)
- Plugin development guide
- Best practices document

### 5. Packaging
Current: Part of hackDark monorepo
Needed:
- Standalone PyPI package
- setup.py with dependencies
- Version management
- Clean pip install

## Architecture Decisions Already Made

### ✅ Keep These
1. **Tag-based** (not auto-detect) - Proven better UX
2. **Keyword matching** (not embeddings for v1) - 17.7ms is plenty fast
3. **Hard project isolation** - Critical differentiator
4. **Sync API** (not async-first) - Simpler, add async later
5. **Provider pattern** - Clean, extensible

### ⚠️ Rethink These
1. **Direct SQLite coupling** - Make database pluggable
2. **Hardcoded paths** - Use configuration
3. **No async support** - Add in v1.1
4. **No embeddings** - Document how to add via plugin

## Code Location in hackDark

```
hackDark/scripts/context/
├── __init__.py          # Main exports
├── types.py             # ContextItem, ContextRequest, ContextResponse, ParsedTag
├── parser.py            # TagParser class
├── formatter.py         # ContextFormatter with anti-hallucination
├── injector.py          # ContextInjector orchestrator
└── providers/
    ├── base.py          # IContextProvider interface
    ├── memory.py        # SQLite memory provider (coupled to hackDark)
    ├── codebase.py      # Stub (TODO)
    └── session.py       # Stub (TODO)

hackDark/scripts/context-test  # CLI testing tool
```

## Migration Strategy

### Phase 1: Extract Core (Week 1)
Copy files and remove hackDark dependencies:
- types.py → ai_context_injector/core/types.py (no changes needed)
- parser.py → ai_context_injector/core/parser.py (no changes needed)
- formatter.py → ai_context_injector/core/formatter.py (no changes needed)
- base.py → ai_context_injector/providers/base.py (no changes needed)
- injector.py → ai_context_injector/core/injector.py (remove auto-detect, make configurable)

### Phase 2: Redesign Providers (Week 1-2)
- memory.py → Create clean SQLiteMemoryProvider example (not built-in)
- Add plugin registration system
- Document provider interface

### Phase 3: Examples & Docs (Week 2-3)
- Create examples/ with OpenAI, Anthropic, Ollama
- Write comprehensive README
- API documentation
- Plugin guide

### Phase 4: Package & Launch (Week 3-4)
- setup.py, PyPI metadata
- Tests
- CI/CD
- Launch prep

## Key Metrics to Preserve

From hackDark implementation:
- ✅ <20ms performance (currently 17.7ms)
- ✅ 100% test coverage for parser
- ✅ Clean 5-line usage example
- ✅ Zero hallucination in testing

## References

- hackDark source: `/home/dark/Project/hackDark/scripts/context/`
- Test results: `/tmp/context-injection-progress.md`
- Research: `/tmp/continue-architecture.md`, `/tmp/context-injection-research.md`
- Working demo: `cd ~/Project/hackDark && ./scripts/context-test "@memory WAL mode"`
