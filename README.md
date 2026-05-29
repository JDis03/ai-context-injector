# AI Context Injector

Tag-based context retrieval for AI assistants with anti-hallucination safeguards.

🚧 **Work in Progress** - Initial development using OpenSpec workflow

## Overview

AI Context Injector provides a clean, framework-agnostic way to inject relevant context into AI assistant prompts using simple tags like `@memory`, `@code`, and `@session`.

**Key Features:**
- 🏷️ Tag-based retrieval (`@memory query`, `@code function`, `@session summary`)
- 🛡️ Research-backed anti-hallucination techniques
- 🔒 Hard project isolation (never mix contexts accidentally)
- 🔌 Plugin system for custom providers
- ⚡ Fast (<20ms for most queries)
- 🌐 Framework-agnostic (works with any AI API)

## Status

Currently in initial development. See `openspec/changes/initial-release/` for design documents.

## Inspiration

Based on working implementation from [hackDark](https://github.com/dark/hackDark) with improvements inspired by:
- Continue.dev (tag-based retrieval)
- Cursor AI (anti-hallucination)
- OpenAI Assistants (citations)
- n8n (plugin architecture)

## Advantages over Continue.dev

| Feature | Continue.dev | AI Context Injector |
|---------|--------------|---------------------|
| Project isolation | ❌ Weak | ✅ Hard |
| Anti-hallucination | ~ Basic | ✅ Research-backed |
| Citations | ❌ No | ✅ Yes |
| Cross-project | Auto (risky) | ✅ Explicit modifier |
| Framework | VSCode only | ✅ Any framework |

## Development

This project uses [OpenSpec](https://openspec.dev) for spec-driven development.

```bash
# See current status
npx openspec status

# View design documents
cat openspec/changes/initial-release/design.md
```

## License

MIT
