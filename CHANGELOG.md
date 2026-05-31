# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-31

### Added

#### Core Features
- **Tag-based context injection** with `@memory`, `@code`, `@session` tags
- **Anti-hallucination safeguards** with 5 critical rules and automatic citations
- **Hard project isolation** by default (never auto-mix contexts)
- **Plugin architecture** via `IContextProvider` interface
- **High performance** pipeline (<25ms, proven 17.7ms in production)

#### Core Components
- `ContextInjector`: Main orchestrator coordinating the full pipeline
- `TagParser`: Regex-based tag parsing with custom tag registration
- `ContextFormatter`: Formats context with delimiters, metadata, and citations
- `IContextProvider`: Abstract base class for custom providers
- `ContextItem`, `ContextRequest`, `ContextResponse`, `ParsedTag`: Core types

#### Features
- Cross-project search with explicit `:all` modifier
- Automatic cross-project warning generation
- Relevance-based filtering and sorting
- Deduplication using first 100 chars hash
- Multi-tag aggregation in single query
- Performance metrics tracking via `inject_with_metrics()`
- Utility methods: `has_tags()`, `extract_query_only()`
- Compact formatting for tight token budgets
- Citation generation: `[memory:project:date]`, `[code:file:line]`

#### Testing
- 219 comprehensive tests (100% passing)
- Unit tests for all core components (158 tests)
- 41 edge case tests (Unicode, extreme inputs, boundary conditions)
- 19 integration tests with real provider implementation
- Performance: <0.2s for entire test suite

#### Documentation
- Comprehensive README with examples
- Complete API reference
- 3 provider implementation examples (Simple, SQLite, Filesystem)
- Architecture diagram
- Design principles
- FAQ section
- MIT License

#### Development
- Full type hints with `py.typed` marker
- Zero runtime dependencies (stdlib only)
- Optional dev dependencies (pytest, mypy, ruff)
- pytest configuration with coverage
- mypy strict mode
- ruff linting

### Technical Details

- **Performance**: <25ms total pipeline (parsing <1ms, formatting ~2ms)
- **Python support**: 3.9, 3.10, 3.11, 3.12, 3.13
- **Type safety**: 100% type-safe with strict mypy
- **Test coverage**: 219 tests covering unit, integration, and edge cases
- **Dependencies**: Zero (core), Optional (dev tools)

### Design Principles

1. **Explicit over implicit**: Empty providers dict by default
2. **Project isolation by default**: Never auto-mix contexts
3. **Zero magic**: No auto-discovery, no global state
4. **Library not framework**: Integrate into your app
5. **Performance matters**: <25ms target
6. **Type safety**: Full type hints, no `Any` in public API
7. **Fail gracefully**: Missing providers return None, not exceptions

### Known Limitations

- Regex-based parsing (no AST parsing)
- Deduplication uses first 100 chars (may miss some duplicates)
- Provider performance depends on implementation (not library bottleneck)
- No built-in providers (bring your own or use examples)

## [Unreleased]

### Planned for Future Releases

- v1.1.0: Async provider support
- v1.2.0: Built-in embedding support
- v1.3.0: Streaming context injection
- v2.0.0: AST-based parsing, advanced deduplication

[1.0.0]: https://github.com/JDis03/ai-context-injector/releases/tag/v1.0.0
