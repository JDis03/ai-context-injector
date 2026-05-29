# Tasks: Initial Release

## 1. Project Setup

- [ ] 1.1 Create package structure (src/ai_context_injector/)
- [ ] 1.2 Create pyproject.toml with package metadata
- [ ] 1.3 Add py.typed marker for type hints
- [ ] 1.4 Create .gitignore for Python project
- [ ] 1.5 Setup pytest configuration
- [ ] 1.6 Create examples/ directory structure
- [ ] 1.7 Create tests/ directory mirroring src/ structure

## 2. Core Types (types.py)

- [ ] 2.1 Port ContextItem dataclass from hackDark
- [ ] 2.2 Port ContextRequest dataclass from hackDark
- [ ] 2.3 Port ContextResponse dataclass from hackDark
- [ ] 2.4 Port ParsedTag dataclass from hackDark
- [ ] 2.5 Add type hints and docstrings
- [ ] 2.6 Write unit tests for citation() method
- [ ] 2.7 Write unit tests for ContextResponse metrics

## 3. Tag Parser (parser.py)

- [ ] 3.1 Port TagParser class from hackDark
- [ ] 3.2 Remove hackDark-specific dependencies
- [ ] 3.3 Add support for custom tag registration
- [ ] 3.4 Write tests for basic tag parsing (@memory, @code, @session)
- [ ] 3.5 Write tests for modifier parsing (@memory:all)
- [ ] 3.6 Write tests for embedded tags in natural text
- [ ] 3.7 Write tests for edge cases (no tags, invalid tags)
- [ ] 3.8 Write tests for utility methods (has_tags, remove_tags)
- [ ] 3.9 Write tests for query normalization
- [ ] 3.10 Add docstrings and type hints

## 4. Provider Interface (providers/base.py)

- [ ] 4.1 Port IContextProvider abstract base class from hackDark
- [ ] 4.2 Add comprehensive docstrings with usage examples
- [ ] 4.3 Create mock provider for testing
- [ ] 4.4 Write integration test with mock provider
- [ ] 4.5 Document provider contract in docstring

## 5. Context Formatter (formatter.py)

- [ ] 5.1 Port ContextFormatter class from hackDark
- [ ] 5.2 Remove hackDark-specific dependencies
- [ ] 5.3 Add configuration options to constructor
- [ ] 5.4 Write tests for delimiter formatting
- [ ] 5.5 Write tests for anti-hallucination rules
- [ ] 5.6 Write tests for metadata formatting
- [ ] 5.7 Write tests for citation generation
- [ ] 5.8 Write tests for cross-project warnings
- [ ] 5.9 Write tests for compact format
- [ ] 5.10 Write tests for format_single()
- [ ] 5.11 Add docstrings and type hints

## 6. Context Injector (injector.py)

- [ ] 6.1 Port ContextInjector class from hackDark
- [ ] 6.2 Remove _detect_project() hardcoded paths
- [ ] 6.3 Add providers parameter to constructor
- [ ] 6.4 Add project parameter to constructor
- [ ] 6.5 Add default_max_items and default_min_relevance parameters
- [ ] 6.6 Remove auto-import of specific providers
- [ ] 6.7 Write tests for inject() with single tag
- [ ] 6.8 Write tests for inject() with multiple tags
- [ ] 6.9 Write tests for inject() with no tags
- [ ] 6.10 Write tests for cross-project modifier
- [ ] 6.11 Write tests for provider unavailability
- [ ] 6.12 Write tests for deduplication
- [ ] 6.13 Write tests for result aggregation and sorting
- [ ] 6.14 Write tests for inject_with_metrics()
- [ ] 6.15 Write tests for error handling (provider failures)
- [ ] 6.16 Add docstrings and type hints

## 7. Package Initialization (__init__.py)

- [ ] 7.1 Create core/__init__.py with public exports
- [ ] 7.2 Create providers/__init__.py with IContextProvider
- [ ] 7.3 Create main __init__.py with all public API
- [ ] 7.4 Add __version__ attribute
- [ ] 7.5 Add __all__ list for explicit exports

## 8. Example Providers

- [ ] 8.1 Create examples/providers/sqlite_memory_provider.py (port from hackDark)
- [ ] 8.2 Create examples/providers/simple_memory_provider.py (simple list-based)
- [ ] 8.3 Create examples/providers/filesystem_code_provider.py (grep-based)
- [ ] 8.4 Add docstrings to example providers
- [ ] 8.5 Test example providers work independently

## 9. Integration Examples

- [ ] 9.1 Create examples/openai_integration.py (complete working example)
- [ ] 9.2 Create examples/anthropic_integration.py (complete working example)
- [ ] 9.3 Create examples/ollama_integration.py (complete working example)
- [ ] 9.4 Add requirements.txt for examples
- [ ] 9.5 Test all examples run successfully

## 10. Documentation

- [ ] 10.1 Create comprehensive README.md with quickstart
- [ ] 10.2 Add installation instructions
- [ ] 10.3 Add 5-line usage example to README
- [ ] 10.4 Document provider interface with example
- [ ] 10.5 Document anti-hallucination features
- [ ] 10.6 Document tag syntax (@memory, @code, @session, modifiers)
- [ ] 10.7 Add comparison table vs Continue.dev
- [ ] 10.8 Create CONTRIBUTING.md
- [ ] 10.9 Create LICENSE file (MIT or Apache 2.0)
- [ ] 10.10 Add badges (PyPI version, license, tests)

## 11. PyPI Packaging

- [ ] 11.1 Configure build system in pyproject.toml
- [ ] 11.2 Add package metadata (author, description, keywords)
- [ ] 11.3 Add classifiers for PyPI
- [ ] 11.4 Configure dependencies (none for core)
- [ ] 11.5 Test package build with `python -m build`
- [ ] 11.6 Verify package structure with `twine check`
- [ ] 11.7 Test install from local wheel

## 12. Testing & Quality

- [ ] 12.1 Achieve 100% test coverage for core (types, parser)
- [ ] 12.2 Achieve 90%+ coverage for formatter and injector
- [ ] 12.3 Add pytest markers for unit vs integration tests
- [ ] 12.4 Add performance benchmark for inject() (<25ms target)
- [ ] 12.5 Run mypy type checking
- [ ] 12.6 Run ruff linting
- [ ] 12.7 Add pre-commit hooks for formatting

## 13. CI/CD

- [ ] 13.1 Create .github/workflows/test.yml
- [ ] 13.2 Configure pytest with coverage reporting
- [ ] 13.3 Add mypy to CI
- [ ] 13.4 Add ruff linting to CI
- [ ] 13.5 Configure coverage badge
- [ ] 13.6 Add performance benchmark check (fail if >25ms median)

## 14. Final Polish

- [ ] 14.1 Review all docstrings for completeness
- [ ] 14.2 Review all type hints
- [ ] 14.3 Test README examples work copy-paste
- [ ] 14.4 Create demo video/GIF for README
- [ ] 14.5 Write CHANGELOG.md for v1.0.0
- [ ] 14.6 Review code for TODOs and FIXMEs
- [ ] 14.7 Final performance test (verify <20ms on real data)

## 15. Launch Preparation

- [ ] 15.1 Tag v1.0.0 in git
- [ ] 15.2 Build distribution packages
- [ ] 15.3 Upload to TestPyPI
- [ ] 15.4 Test install from TestPyPI
- [ ] 15.5 Upload to PyPI
- [ ] 15.6 Verify PyPI page looks correct
- [ ] 15.7 Create GitHub release with changelog
- [ ] 15.8 Update hackDark to use published package

## 16. Community Launch

- [ ] 16.1 Write launch blog post
- [ ] 16.2 Submit to Hacker News
- [ ] 16.3 Post to r/LocalLLaMA
- [ ] 16.4 Post to r/MachineLearning
- [ ] 16.5 Tweet announcement
- [ ] 16.6 Email AI newsletters (e.g., TheSequence, ImportAI)
- [ ] 16.7 Monitor initial feedback and respond to issues
