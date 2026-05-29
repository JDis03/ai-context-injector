# Learnings from hackDark Implementation

This document captures real-world learnings from implementing and testing the context injection system in hackDark. Use this to inform design decisions in ai-context-injector.

**Last Updated:** 2026-05-29

**hackDark Implementation:** `/home/dark/Project/hackDark/scripts/context/`

---

## ✅ What Works Well (Keep These)

### 1. Tag-Based Retrieval
**Status:** ✅ Proven in testing

```python
# User input
"@memory dark keyboard layout"
"@memory:all what is openspec"
"@code ContextItem class"
```

**Why it works:**
- Clear user intent (no ambiguity)
- Fast parsing (regex-based, <1ms)
- No unnecessary searches
- Explicit cross-project with `:all` modifier

**Evidence:**
- Parser tested with 3 scenarios: ✅ All passing
- End-to-end test: ✅ 17.7ms performance
- Zero false positives in tag detection

**Recommendation for ai-context-injector:**
- ✅ Keep tag-based approach
- ✅ Support modifiers (`:all`, `:recent`, etc)
- ✅ Regex pattern: `@(memory|code|session)(?::\w+)?\s+(.+)`

---

### 2. Keyword-Based Relevance (v1)
**Status:** ✅ Fast enough, good enough

**Current implementation:**
```python
def _calculate_relevance(query: str, text: str) -> float:
    keywords = query.split()
    matches = sum(1 for kw in keywords if kw in text)
    base_score = matches / len(keywords)
    
    # Boost for exact phrase
    if query in text:
        base_score += 0.3
    
    return 0.5 + (base_score * 0.5)  # Scale to 0.5-1.0
```

**Performance:**
- 17.7ms average query time
- Target was <150ms
- **8.5x better than target** 🎉

**Why NOT use embeddings in v1:**
- Keyword matching is plenty fast
- Embeddings add complexity (Ollama dependency)
- Can add embeddings later without breaking API
- KISS principle

**Recommendation for ai-context-injector:**
- ✅ Ship v1 with keyword matching
- ✅ Document how to add embeddings via plugin
- ✅ Add embeddings in v1.1 or v2.0
- ❌ Don't over-engineer v1

---

### 3. Hard Project Isolation
**Status:** ✅ Critical differentiator vs Continue.dev

**Implementation:**
```python
# Default: Only current project
request = ContextRequest(
    project="hackDark",
    include_cross_project=False  # DEFAULT
)

# Explicit cross-project
@memory:all query  # User must type :all
```

**Why this matters:**
- Continue.dev auto-mixes projects (users confused)
- Prevents hallucinations from wrong project
- User explicitly requests cross-project

**Evidence from hackDark:**
- Zero context bleeding in testing
- Cross-project warning works correctly
- Users know exactly what project context came from

**Recommendation for ai-context-injector:**
- ✅ Hard isolation by default
- ✅ Require explicit modifier for cross-project
- ✅ Always show warning when mixing projects
- ✅ Include project name in every citation

---

### 4. Anti-Hallucination Techniques
**Status:** ✅ Research-backed, proven effective

**Implementation:**
```
=== BEGIN CONTEXT ===

CRITICAL RULES FOR USING THIS CONTEXT:
1. ONLY cite information that appears in context sections
2. If context is from different project, CLEARLY state which
3. Include source citations [memory:project:date]
4. If unsure or missing, say "I don't have information"
5. NEVER mix information from different projects

Retrieved Context for: hackDark
Found 1 relevant item(s)

--- Context Item 1/1 ---
Source: memory | Project: hackDark | Relevance: 0.83 | Date: 2026-05-29
Citation: [memory:hackDark:2026-05-29]

<actual content>

=== END CONTEXT ===
```

**Why this works:**
- Delimiters prevent confusion
- Explicit rules reduce hallucination
- Citations enable verification
- Metadata adds context

**Industry consensus (all use this):**
- Continue.dev: Delimiters ✅
- Cursor AI: Anti-hallucination rules ✅
- OpenAI Assistants: Citations ✅
- n8n: Metadata ✅

**Recommendation for ai-context-injector:**
- ✅ Keep exact format (proven)
- ✅ Make rules customizable but default to these 5
- ✅ Always include citations
- ✅ Metadata configurable (some users want compact mode)

---

### 5. Provider Pattern
**Status:** ✅ Clean, extensible

**Interface:**
```python
class IContextProvider(ABC):
    @abstractmethod
    def retrieve(self, request: ContextRequest) -> List[ContextItem]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        pass
```

**Why this works:**
- Simple interface (4 methods only)
- Easy to implement custom providers
- `is_available()` prevents crashes
- Type-safe with ContextRequest/ContextItem

**Recommendation for ai-context-injector:**
- ✅ Keep this exact interface
- ✅ Add plugin discovery in v1.1
- ✅ Start with manual registration (simpler)
- ✅ Document with example custom provider

---

## ⚠️ What Needs Improvement

### 1. Database Coupling
**Status:** ❌ Too coupled to hackDark

**Current problem:**
```python
from project_memory import ProjectMemory  # hackDark-specific!

class MemoryProvider:
    def _get_project_memory(self):
        return ProjectMemory(db_path=self.db_path)  # Assumes hackDark schema
```

**Why this is bad:**
- Can't use with other databases
- Assumes specific table schema
- Not reusable

**Solution for ai-context-injector:**
```python
# Don't include MemoryProvider as built-in
# Instead, provide it as an EXAMPLE

# examples/sqlite_memory_provider.py
class SQLiteMemoryProvider(IContextProvider):
    """Example provider using SQLite.
    
    Adapt this to your database schema.
    """
    def __init__(self, db_path: str, query_function: Callable):
        self.db_path = db_path
        self.query_fn = query_function  # User provides query logic
```

**Recommendation:**
- ❌ Don't ship built-in database providers
- ✅ Ship examples that users adapt
- ✅ Document common patterns (SQLite, Postgres, Supabase)
- ✅ Let users bring their own storage

---

### 2. Configuration Hardcoded
**Status:** ❌ Paths hardcoded

**Current problem:**
```python
def __init__(self, db_path: Optional[str] = None):
    if db_path is None:
        db_path = os.path.expanduser("~/.hackdark/memory.db")  # HARDCODED!
```

**Solution for ai-context-injector:**
```python
# No defaults, require explicit configuration
injector = ContextInjector(
    providers={
        'memory': MyMemoryProvider(config={'db_path': './my.db'}),
        'code': MyCodeProvider(config={'index_path': './index/'}),
    },
    project="my-project"  # Explicit, no auto-detect
)
```

**Recommendation:**
- ✅ No magic defaults
- ✅ Require explicit configuration
- ✅ Document common setups
- ✅ Fail fast with clear error messages

---

### 3. Auto-Detection Fragile
**Status:** ⚠️ Works for hackDark, won't generalize

**Current problem:**
```python
def _detect_project(self) -> str:
    cwd = os.getcwd()
    
    # Hardcoded paths!
    project_paths = {
        "/home/dark/Project/hackDark": "hackDark",
        "/home/dark/Project/darkkeyboard": "DarkKeyboard",
        # ...
    }
```

**Why this is bad:**
- Only works on my machine
- Assumes directory structure
- Not portable

**Solution for ai-context-injector:**
```python
# No auto-detection in library
# User must specify project

injector = ContextInjector(
    project="my-project",  # REQUIRED
    # OR provide project detector function
    project_detector=lambda: get_git_repo_name()
)
```

**Recommendation:**
- ❌ Don't auto-detect in library
- ✅ Make `project` required parameter
- ✅ Document how to write custom detector
- ✅ Provide example detectors (git-based, config-based)

---

### 4. Sync-Only API
**Status:** ⚠️ Fine for v1, will need async later

**Current:**
```python
result = injector.inject(query)  # Blocking
```

**Future users will want:**
```python
result = await injector.inject_async(query)  # Non-blocking
```

**Recommendation for ai-context-injector:**
- ✅ Ship v1 with sync API (simpler)
- ✅ Design for async (don't make blocking assumptions)
- ✅ Add async wrappers in v1.1
- ✅ Document both patterns

---

## 🚧 Not Yet Tested (Implement Carefully)

### 1. CodebaseProvider (Stub in hackDark)
**Status:** 📝 Designed but not implemented

**What we know:**
- Will integrate with RAG system
- Needs file path + line numbers in metadata
- Should return code snippets with context
- Relevance from embeddings (unlike memory)

**What we DON'T know:**
- Best way to chunk code
- How much context around snippet
- Performance with large codebases
- Cache strategy

**Recommendation:**
- ⚠️ Implement in hackDark FIRST
- ⚠️ Test with real codebase
- ⚠️ Then port learnings to ai-context-injector
- ❌ Don't guess, validate

---

### 2. SessionProvider (Stub in hackDark)
**Status:** 📝 Designed but not implemented

**What we know:**
- Should search session summaries
- Recent sessions more relevant
- Useful for "what did we do last time"

**What we DON'T know:**
- How far back to search
- How to rank sessions
- Whether to include individual messages or just summaries

**Recommendation:**
- ⚠️ Implement in hackDark FIRST
- ⚠️ Use for 1-2 weeks
- ⚠️ See what users actually need
- ❌ Don't ship unvalidated

---

### 3. Embeddings Integration
**Status:** 📝 Planned for v1.1+

**What we know:**
- Will improve relevance vs keyword matching
- Adds Ollama/OpenAI dependency
- Slower than keyword matching

**What we DON'T know:**
- Which embedding model works best
- Whether performance trade-off is worth it
- How to handle offline scenarios

**Recommendation:**
- ❌ Don't include in v1.0
- ✅ Document plugin approach
- ✅ Provide example embedding provider
- ✅ Let users choose (keyword vs embeddings)

---

## 📊 Performance Benchmarks (hackDark)

### Query Performance
```
Query: @memory WAL mode database
Performance: 17.7ms
Total found: 1
After filtering: 1
Filter ratio: 100.0%
```

**Breakdown:**
- Tag parsing: <1ms
- Database query: ~10ms
- Relevance calculation: ~5ms
- Formatting: ~2ms
- **Total: 17.7ms**

**Target:** <150ms
**Achieved:** 17.7ms (8.5x better)

**Recommendation:**
- ✅ <20ms is PLENTY fast
- ✅ Don't optimize prematurely
- ✅ Focus on correctness first
- ⚠️ Monitor performance but don't obsess

---

## 🎓 Design Principles (Validated)

### 1. KISS (Keep It Simple, Stupid)
- ✅ Keyword matching > Embeddings (v1)
- ✅ Manual registration > Auto-discovery (v1)
- ✅ Sync API > Async (v1)
- ✅ Examples > Built-in providers

### 2. Explicit > Implicit
- ✅ `@memory:all` > Auto cross-project
- ✅ Required config > Magic defaults
- ✅ Clear errors > Silent failures

### 3. Extensible > Comprehensive
- ✅ Plugin system > Many built-ins
- ✅ Examples > Batteries included
- ✅ User adapts > We predict every use case

### 4. Proven > Theoretical
- ✅ Use it in hackDark first
- ✅ Validate in real usage
- ✅ Then generalize for library

---

## 🔍 Edge Cases Found in Testing

### 1. Empty Results
**What happens:** Query returns no matches

**Current behavior:**
```
Query: @memory nonexistent query
Performance: 12.1ms
Total found: 0
After filtering: 0

No context found for query.
```

**Good:** Clear message, fast
**Recommendation:** ✅ Keep this behavior

---

### 2. Low Relevance Results
**What happens:** Results exist but all below 0.70 threshold

**Current behavior:** Filtered out, returns empty

**Question:** Should we return low-relevance results with warning?

**Recommendation:**
- ⚠️ Test in hackDark first
- ⚠️ See if users complain about "no results"
- ⚠️ Maybe add `--show-all` flag in v1.1

---

### 3. Multiple Tags in One Query
**What happens:** `"@memory X and @code Y"`

**Current behavior:** Processes both, deduplicates, returns combined

**Status:** ✅ Works correctly

**Recommendation:** ✅ Keep this behavior

---

## 📚 Integration Patterns Tested

### Pattern 1: Simple Script
```python
from context import inject_context

result = inject_context("@memory query")
if result:
    print(result)
```

**Status:** ✅ Works
**Use case:** Quick scripts, testing

---

### Pattern 2: With Metrics
```python
from context import ContextInjector

injector = ContextInjector()
response = injector.inject_with_metrics("@memory query")

print(f"Found {response.filtered_count} items in {response.performance_ms:.1f}ms")
print(response.formatted_context)
```

**Status:** ✅ Works
**Use case:** Production monitoring, debugging

---

### Pattern 3: Custom Providers (Not tested yet)
```python
# TODO: Test in hackDark before documenting
```

**Status:** ⚠️ Needs validation

---

## 🚀 Next Steps for ai-context-injector

### Phase 1: Core (Use These Learnings)
1. ✅ Copy types.py (no changes needed)
2. ✅ Copy parser.py (no changes needed)
3. ✅ Copy formatter.py (no changes needed)
4. ⚠️ Adapt injector.py (remove auto-detect, require config)
5. ⚠️ Document provider interface (don't ship built-in providers)

### Phase 2: Examples (Based on hackDark)
1. Create `examples/sqlite_memory_provider.py` (adapt from hackDark)
2. Create `examples/openai_integration.py`
3. Create `examples/anthropic_integration.py`
4. Create `examples/ollama_integration.py`

### Phase 3: Documentation (From Real Usage)
1. "Quick Start" (5-line example)
2. "Creating Custom Providers" (based on hackDark MemoryProvider)
3. "Anti-Hallucination Best Practices" (proven in hackDark)
4. "Performance Tuning" (17.7ms benchmark)

### Phase 4: Validation (Use hackDark)
1. Migrate hackDark to use ai-context-injector library
2. If it works there, it'll work anywhere
3. Document migration in case study

---

## 📝 How to Use This Document

### When Designing:
```bash
# In ai-context-injector chat
User: "Read LEARNINGS_FROM_HACKDARK.md section on 'Anti-Hallucination Techniques'"
User: "Check if there are learnings about X"
```

### When Implementing:
```bash
# Reference proven patterns
User: "Implement provider interface. Use the pattern from LEARNINGS_FROM_HACKDARK.md"
```

### When Stuck:
```bash
# Check if we already solved it
User: "Search LEARNINGS for 'performance' or 'edge cases'"
```

### When Updating:
```bash
# After testing in hackDark
cd ~/Project/hackDark
# Document what you learned
./scripts/project_memory.py add-learning "X works better than Y" "tested with Z"

# Then update this file
cd ~/Project/ai-context-injector
# Add to appropriate section
```

---

## 🔗 Additional Resources

- **Source Code:** `/home/dark/Project/hackDark/scripts/context/`
- **Tests:** Run `cd ~/Project/hackDark && ./scripts/context-test "@memory query"`
- **Memory Database:** `~/.hackdark/memory.db` (use `@memory:all hackDark <query>`)
- **Research:** `/tmp/context-injection-research.md`, `/tmp/continue-architecture.md`

---

## ✅ Summary for ai-context-injector

**KEEP (Proven):**
- Tag-based retrieval
- Keyword matching (v1)
- Hard project isolation
- Anti-hallucination format
- Provider pattern
- <20ms performance target

**CHANGE (Improve):**
- Remove database coupling → Examples only
- Remove hardcoded config → Require explicit
- Remove auto-detection → User provides project
- Add async support → v1.1

**VALIDATE (Test First):**
- CodebaseProvider → Implement in hackDark first
- SessionProvider → Test in real usage
- Embeddings → Plugin example, not built-in

**The golden rule:** If hackDark doesn't use it, why would anyone else?

---

**Last Updated:** 2026-05-29 by hackDark development
**Next Update:** After implementing CodebaseProvider or SessionProvider
