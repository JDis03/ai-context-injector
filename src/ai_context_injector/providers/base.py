"""Base interface for context providers.

All context providers must implement the IContextProvider interface.
This enables a clean plugin system where users can create custom providers
without modifying the core library.

Proven pattern from memory-system: 4 methods only, simple and extensible.
"""

from abc import ABC, abstractmethod
from typing import List
from ..core.types import ContextItem, ContextRequest


class IContextProvider(ABC):
    """Abstract base class that all context providers must implement.
    
    The provider pattern enables:
    - Custom data sources (SQLite, Postgres, APIs, filesystems, etc.)
    - Pluggable retrieval strategies (keyword, embeddings, hybrid)
    - Framework-agnostic design (works with any LLM provider)
    
    Contract:
    - retrieve(): Fetch context items based on request
    - is_available(): Check if provider is ready to use
    - name: Human-readable name for logging
    - source_type: Type string for ContextItem ("memory", "code", etc.)
    
    Example implementation:
        >>> from datetime import datetime
        >>> from ai_context_injector import IContextProvider, ContextItem, ContextRequest
        >>> 
        >>> class SimpleMemoryProvider(IContextProvider):
        ...     def __init__(self, memories: list[str]):
        ...         self.memories = memories
        ...     
        ...     @property
        ...     def name(self) -> str:
        ...         return "Simple Memory"
        ...     
        ...     @property
        ...     def source_type(self) -> str:
        ...         return "memory"
        ...     
        ...     def is_available(self) -> bool:
        ...         return True
        ...     
        ...     def retrieve(self, request: ContextRequest) -> list[ContextItem]:
        ...         results = []
        ...         for memory in self.memories:
        ...             if request.query.lower() in memory.lower():
        ...                 results.append(ContextItem(
        ...                     content=memory,
        ...                     source=self.source_type,
        ...                     project=request.project,
        ...                     metadata={},
        ...                     relevance_score=0.9,
        ...                     timestamp=datetime.now()
        ...                 ))
        ...         return results[:request.max_items]
    
    Performance expectations:
    - retrieve() should complete in <50ms for typical queries
    - is_available() should be fast (<1ms), ideally cached
    
    Error handling:
    - retrieve() should return empty list on errors, not raise exceptions
    - Providers handle their own logging internally
    - The injector will skip unavailable providers gracefully
    """
    
    @abstractmethod
    def retrieve(self, request: ContextRequest) -> List[ContextItem]:
        """Retrieve context items based on request.
        
        This is the core method that providers must implement. It receives
        a ContextRequest with query, project, and filtering parameters, and
        returns matching ContextItem objects.
        
        Args:
            request: ContextRequest containing:
                - tag: Tag string (e.g., "@memory")
                - query: Search query text
                - project: Current project name
                - max_items: Maximum items to return (default: 10)
                - min_relevance: Minimum relevance score (default: 0.70)
                - include_cross_project: Whether to search all projects
                - prefer_recent: Whether to weight recent items higher
        
        Returns:
            List of ContextItem objects matching the request.
            Should return empty list if no matches or on error.
            
        Implementation requirements:
            - Respect max_items limit
            - Filter by min_relevance (items below threshold excluded)
            - Handle project isolation (unless include_cross_project=True)
            - Sort by relevance_score descending (highest first)
            - Populate all required ContextItem fields correctly
            - Return empty list on errors (don't raise exceptions)
            
        Example:
            >>> def retrieve(self, request: ContextRequest) -> List[ContextItem]:
            ...     # Search your data source
            ...     matches = self.search(request.query, request.project)
            ...     
            ...     # Filter by relevance
            ...     filtered = [m for m in matches if m.score >= request.min_relevance]
            ...     
            ...     # Sort by relevance
            ...     filtered.sort(key=lambda x: x.score, reverse=True)
            ...     
            ...     # Limit results
            ...     return filtered[:request.max_items]
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available and ready to use.
        
        This method should quickly verify that the provider's dependencies
        are met and it can successfully retrieve context. Examples:
        - Database file exists
        - API credentials are valid
        - Required services are reachable
        
        Returns:
            True if provider can be used, False otherwise
            
        Performance:
            - Should be very fast (<1ms)
            - Consider caching the result
            - Called before every retrieve() by the injector
            
        Example:
            >>> def is_available(self) -> bool:
            ...     # Check if database exists
            ...     if not os.path.exists(self.db_path):
            ...         return False
            ...     
            ...     # Optionally verify connectivity
            ...     try:
            ...         self.db.ping()
            ...         return True
            ...     except:
            ...         return False
        
        Note:
            The ContextInjector will skip providers that return False.
            This prevents crashes when optional providers are unavailable.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get human-readable provider name for logging and debugging.
        
        Returns:
            Descriptive string like "SQLite Memory Provider" or "Filesystem Code Provider"
            
        Example:
            >>> @property
            >>> def name(self) -> str:
            ...     return "SQLite Memory Provider"
        """
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        """Get source type identifier for ContextItem objects.
        
        Returns:
            Source type string. Built-in types:
            - "memory": For project memory, decisions, learnings
            - "code": For code snippets, files, functions
            - "session": For session history, chat logs
            - Custom: Any string for custom providers (e.g., "docs", "tickets")
            
        Example:
            >>> @property
            >>> def source_type(self) -> str:
            ...     return "memory"  # or "code", "session", "docs", etc.
        
        Note:
            This value is used in ContextItem.citation() to generate
            citation strings like [memory:project:date] or [code:file:line]
        """
        pass
