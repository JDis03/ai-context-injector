# Examples

This directory contains working examples of how to use ai-context-injector.

## Directory Structure

- `providers/` - Example provider implementations
  - `simple_memory_provider.py` - Simple list-based provider
  - `sqlite_memory_provider.py` - SQLite-based provider (adapted from hackDark)
  - `filesystem_code_provider.py` - Grep-based code search provider

- `integrations/` - Full integration examples with LLM providers
  - `openai_integration.py` - OpenAI API integration
  - `anthropic_integration.py` - Anthropic (Claude) integration
  - `ollama_integration.py` - Ollama (local LLM) integration

## Installation

Install examples dependencies:

```bash
pip install -e ".[examples]"
```

Or install specific providers:

```bash
pip install openai  # For OpenAI example
pip install anthropic  # For Anthropic example
```

## Quick Start

See each example file for specific usage instructions.
