"""AI Context Injector - Tag-based context injection with anti-hallucination safeguards.

A standalone Python library for injecting relevant context into LLM prompts based on
tags in user input (@memory, @code, @session, etc.). Ported from memory-system to
provide a clean, reusable API for any project.

Key features:
- Tag-based context retrieval (@memory query, @code class_name, etc.)
- Anti-hallucination safeguards (5 critical rules + citations)
- Hard project isolation by default (differentiator vs Continue.dev)
- Plugin system via provider registration
- <25ms performance (proven 17.7ms in memory-system)
- 100% test coverage

Basic usage:
    >>> from ai_context_injector import ContextInjector, ContextItem
    >>> from datetime import datetime
    >>> 
    >>> # Create injector
    >>> injector = ContextInjector(current_project="my-project")
    >>> 
    >>> # Register a provider
    >>> injector.register_provider("@memory", my_memory_provider)
    >>> 
    >>> # Inject context
    >>> context = injector.inject("@memory dark keyboard layout")
    >>> if context:
    ...     print(context)

Advanced usage with metrics:
    >>> response = injector.inject_with_metrics("@memory query")
    >>> print(f"Found {response.total_found} items in {response.performance_ms:.2f}ms")
    >>> print(f"Filter ratio: {response.filter_ratio:.1%}")

Custom provider example:
    >>> from ai_context_injector.providers import IContextProvider
    >>> 
    >>> class MyProvider(IContextProvider):
    ...     @property
    ...     def name(self) -> str:
    ...         return "MyProvider"
    ...     
    ...     @property
    ...     def source_type(self) -> str:
    ...         return "custom"
    ...     
    ...     def is_available(self) -> bool:
    ...         return True
    ...     
    ...     def retrieve(self, request):
    ...         # Your retrieval logic here
    ...         return [
    ...             ContextItem(
    ...                 content="Example content",
    ...                 source="custom",
    ...                 project=request.project,
    ...                 metadata={},
    ...                 relevance_score=0.9,
    ...                 timestamp=datetime.now()
    ...             )
    ...         ]

For detailed documentation, see:
https://github.com/JDis03/ai-context-injector
"""

__version__ = "1.1.0"
__author__ = "Dark"
__license__ = "MIT"

# Core types
from .core.types import (
    ContextItem,
    ContextRequest,
    ContextResponse,
    ParsedTag,
    Chunk,
)

# Core functionality
from .core.parser import TagParser, parse_tags
from .core.formatter import ContextFormatter, format_context
from .core.injector import ContextInjector, inject_context

# Chunking and indexing
from .chunking import (
    chunk_content,
    BySizeChunker,
    ByMarkdownHeadersChunker,
    ByParagraphChunker,
)
from .indexing import index, search, clear_index

# Embeddings and semantic search
from .embeddings import (
    embed,
    embed_many,
    cosine_similarity,
    search_semantic,
    pair_distance,
)

# Provider interface
from .providers.base import IContextProvider

# Public API
__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__license__",
    
    # Core types
    "ContextItem",
    "ContextRequest",
    "ContextResponse",
    "ParsedTag",
    "Chunk",
    
    # Core functionality
    "TagParser",
    "parse_tags",
    "ContextFormatter",
    "format_context",
    "ContextInjector",
    "inject_context",
    
    # Chunking
    "chunk_content",
    "BySizeChunker",
    "ByMarkdownHeadersChunker",
    "ByParagraphChunker",
    
    # Indexing
    "index",
    "search",
    "clear_index",
    
    # Embeddings
    "embed",
    "embed_many",
    "cosine_similarity",
    "search_semantic",
    "pair_distance",
    
    # Provider interface
    "IContextProvider",
]
