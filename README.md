# AI Context Injector

> Framework-agnostic Python library for tag-based context injection with anti-hallucination safeguards

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Status: Planning](https://img.shields.io/badge/status-planning-orange.svg)]()

## What is this?

AI Context Injector solves the problem of **persistent, structured context** for AI assistants. Instead of repeatedly explaining project details, past decisions, and code context, use simple tags like `@memory`, `@code`, and `@session` to inject relevant context automatically.

## Key Features

- **Tag-based retrieval**: `@memory keyboard layout`, `@code ContextItem class`
- **Hard project isolation**: Never mix contexts without explicit user intent
- **Anti-hallucination**: Research-backed formatting with delimiters, metadata, citations
- **Plugin system**: Custom providers via simple interface
- **Framework-agnostic**: Works with OpenAI, Anthropic, Ollama, any LLM
- **Fast**: <20ms for typical queries

## Quick Example

```python
from ai_context_injector import ContextInjector, IContextProvider

# Define your provider (or use examples)
class MyMemoryProvider(IContextProvider):
    def retrieve(self, request):
        # Your retrieval logic here
        return [...]

# Initialize and use
injector = ContextInjector(
    providers={'@memory': MyMemoryProvider()},
    project="my-project"
)

context = injector.inject("@memory database decisions")
# Returns formatted context ready for your LLM prompt
```

## Why AI Context Injector vs Continue.dev?

| Feature | Continue.dev | AI Context Injector |
|---------|--------------|---------------------|
| Project isolation | ❌ Weak | ✅ Hard (never auto-mix) |
| Anti-hallucination | ~ Basic | ✅ 5 critical rules + citations |
| Cross-project | Auto (risky) | ✅ Explicit `:all` modifier |
| Framework | VSCode only | ✅ Any (OpenAI, Claude, etc) |
| Citations | ❌ No | ✅ [memory:project:date] |

## Status

🚧 **Currently in development** - See [OpenSpec change `initial-release`](./openspec/changes/initial-release/) for detailed specifications and progress.

### Roadmap

- ✅ Proposal (completed)
- ✅ Design (completed)
- ✅ Specifications (completed)
- ✅ Tasks breakdown (completed)
- ⏳ Implementation (in progress)
- ⏳ Testing & documentation
- ⏳ PyPI release

## Prior Art

Based on proven code from [hackDark](https://github.com/dark/hackDark):
- 1,473 lines of tested code
- 17.7ms performance proven
- Tag parser tested with 3 scenarios
- End-to-end working with real memory system

## Documentation

Full documentation will be available after v1.0.0 release. For now, see:

- [Proposal](./openspec/changes/initial-release/proposal.md) - Problem statement and solution overview
- [Design](./openspec/changes/initial-release/design.md) - Technical architecture and decisions
- [Specs](./openspec/changes/initial-release/specs/) - Detailed requirements for each capability
- [Tasks](./openspec/changes/initial-release/tasks.md) - Implementation checklist

## Contributing

Contributions welcome after v1.0.0 release. For now, follow progress in the OpenSpec documentation.

## License

MIT (to be confirmed)

## Author

Built with [OpenSpec](https://github.com/openspec/openspec) - Spec-Driven Development
