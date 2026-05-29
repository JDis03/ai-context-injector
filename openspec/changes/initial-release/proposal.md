# Proposal: Initial Release - AI Context Injector

## Problem

AI assistants lack persistent, structured context across conversations. Users repeatedly explain the same project details, past decisions, and code context. Existing solutions like Continue.dev have weaknesses:

- **Weak project isolation**: Contexts from different projects mix, causing confusion
- **No anti-hallucination safeguards**: LLMs invent information when context is ambiguous
- **Framework lock-in**: Tied to specific IDEs (VSCode)
- **No citations**: Can't verify where information came from

## Solution

Build **AI Context Injector** - a clean, framework-agnostic Python library for tag-based context retrieval with research-backed anti-hallucination techniques.

### Core Features

1. **Tag-based retrieval**: `@memory query`, `@code function`, `@session summary`
2. **Hard project isolation**: Never mix contexts without explicit user intent
3. **Anti-hallucination**: Delimiters, metadata, citations, explicit rules
4. **Plugin system**: Custom providers via simple interface
5. **Framework-agnostic**: Works with OpenAI, Anthropic, Ollama, any API
6. **Fast**: <20ms for typical queries (keyword matching v1, embeddings later)

### Key Differentiators vs Continue.dev

| Feature | Continue.dev | AI Context Injector |
|---------|--------------|---------------------|
| Project isolation | ❌ Weak | ✅ Hard (never auto-mix) |
| Anti-hallucination | ~ Basic | ✅ 5 critical rules + citations |
| Cross-project | Auto (risky) | ✅ Explicit `:all` modifier |
| Framework | VSCode only | ✅ Any (OpenAI, Claude, etc) |
| Citations | ❌ No | ✅ [memory:project:date] |

## Scope

### In Scope (v1.0)

**Core Package:**
- Tag parser (`@memory`, `@code`, `@session`)
- Context formatter (delimiters, metadata, anti-hallucination rules)
- Provider interface (IContextProvider)
- 3 built-in providers: Memory, Codebase, Session
- Plugin system for custom providers

**Examples:**
- OpenAI integration example
- Anthropic (Claude) integration example
- Ollama (local LLM) integration example

**Documentation:**
- Comprehensive README
- API documentation
- Plugin development guide
- Anti-hallucination best practices

**Testing:**
- Unit tests for all components
- Integration tests
- Example tests

**Packaging:**
- PyPI package setup
- Clean pip install experience

### Out of Scope (Future)

- Web UI (CLI only for v1)
- Automatic embedding generation (bring your own)
- Multi-user/team features
- Cloud hosting
- IDE extensions (pure Python library)

## Success Metrics

### Technical
- ✅ <20ms query performance (keyword matching)
- ✅ 100% test coverage for core
- ✅ Clean API (5-line usage example)
- ✅ Zero framework dependencies

### Adoption (6 months)
- 🎯 100+ GitHub stars
- 🎯 1,000+ PyPI downloads
- 🎯 5+ external contributors
- 🎯 Featured in AI newsletter
- 🎯 Referenced in at least 1 blog post

### Quality
- 🎯 <5 open issues
- 🎯 <48hr response time on issues
- 🎯 Comprehensive docs (users don't need to read code)

## Prior Art

### Working Implementation
Based on proven code from [hackDark](https://github.com/dark/hackDark):
- 1,473 lines of tested code
- 17.7ms performance proven
- Tag parser tested with 3 scenarios
- End-to-end working with real memory system

### Research Sources
- Continue.dev: Tag-based retrieval pattern
- Cursor AI: Anti-hallucination techniques
- OpenAI Assistants: Citation format
- n8n: Plugin architecture
- Academic papers on LLM hallucination mitigation

## Risk Assessment

### Low Risk
- ✅ Core functionality already working (hackDark)
- ✅ Clear API design from research
- ✅ Well-understood problem space

### Medium Risk
- ⚠️ Plugin system design (iterative approach planned)
- ⚠️ Documentation quality (hire technical writer if needed)

### Mitigated Risk
- ~~OSS adoption~~ → Mitigated by strong differentiators vs Continue.dev
- ~~Performance~~ → Already proven at 17.7ms
- ~~API usability~~ → Will dogfood in hackDark for 2 weeks first

## Timeline

### Week 1-2: Foundation
- Extract and clean hackDark code
- Design plugin system
- Core package structure
- Basic tests

### Week 3: Polish
- Examples (OpenAI, Anthropic, Ollama)
- Comprehensive documentation
- PyPI packaging
- Full test coverage

### Week 4: Launch Prep
- Final bug fixes
- Performance optimization
- Create demo video
- Write launch blog post

### Week 5: Launch
- Publish to PyPI
- Post to Hacker News
- Share on Reddit (r/LocalLLaMA, r/MachineLearning)
- Tweet announcement
- Email AI newsletters

### Week 6+: Iterate
- Respond to feedback
- Fix bugs quickly
- Consider feature requests
- Build community

## Open Questions

1. **Package name**: `ai-context-injector` vs `context-injector` vs `llm-context`?
   - Leaning toward `ai-context-injector` (clear, searchable)

2. **Plugin discovery**: Auto-discover via entry points or manual registration?
   - Start manual, add auto-discovery in v1.1

3. **Embedding support**: Include basic embeddings or keep it minimal?
   - Keep minimal (v1.0), document how to add embeddings in plugin

4. **Async support**: Make API async-first or sync-first?
   - Sync-first for simplicity, add async wrappers in v1.1

## Decision

**Proceed with initial-release change.**

Rationale:
- Working code already exists (de-risk)
- Clear differentiators vs competition
- Proven performance
- Strong market need
- Realistic timeline

Next: Create design.md with detailed architecture
