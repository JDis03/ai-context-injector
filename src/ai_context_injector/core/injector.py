"""Context injection orchestrator.

Main class that coordinates parsing, provider routing, aggregation,
deduplication, sorting, and formatting of context items.

This is the primary API for users of the library.
"""

import time
from pathlib import Path
from typing import Dict, List, Optional

from .types import ContextItem, ContextRequest, ContextResponse, ParsedTag
from .parser import TagParser
from .formatter import ContextFormatter
from ..providers.base import IContextProvider


class ContextInjector:
    """Main orchestrator for context injection system.
    
    Coordinates the full pipeline:
    1. Parse tags from user input
    2. Route to appropriate providers
    3. Aggregate results from multiple tags
    4. Deduplicate items
    5. Sort by relevance
    6. Format for LLM injection
    
    Performance: <25ms total (proven in memory-system at 17.7ms)
    
    Example:
        >>> injector = ContextInjector(current_project="my-project")
        >>> injector.register_provider("@memory", MyMemoryProvider())
        >>> 
        >>> result = injector.inject("@memory dark keyboard layout")
        >>> if result:
        ...     print(result)  # Formatted context ready for LLM
        
        >>> # With metrics
        >>> response = injector.inject_with_metrics("@memory query")
        >>> print(f"Found {response.total_found} items in {response.performance_ms:.2f}ms")
    """
    
    def __init__(
        self,
        current_project: Optional[str] = None,
        parser: Optional[TagParser] = None,
        formatter: Optional[ContextFormatter] = None
    ):
        """Initialize context injector.
        
        Args:
            current_project: Current project name (uses cwd basename if None)
            parser: Custom TagParser instance (creates default if None)
            formatter: Custom ContextFormatter instance (creates default if None)
            
        Example:
            >>> # Auto-detect project from cwd
            >>> injector = ContextInjector()
            >>> 
            >>> # Explicit project name
            >>> injector = ContextInjector(current_project="my-project")
            >>> 
            >>> # Custom parser/formatter
            >>> custom_parser = TagParser(custom_tags={"@docs"})
            >>> injector = ContextInjector(parser=custom_parser)
        """
        self.current_project = current_project or self._detect_project()
        self.parser = parser or TagParser()
        self.formatter = formatter or ContextFormatter()
        
        # Provider registry (empty by default - users must register)
        self.providers: Dict[str, IContextProvider] = {}
    
    def _detect_project(self) -> str:
        """Auto-detect current project from working directory.
        
        Uses the basename of the current working directory as project name.
        
        Returns:
            Project name (directory basename)
            
        Example:
            >>> # If cwd is /home/user/projects/my-app
            >>> injector = ContextInjector()
            >>> injector.current_project
            'my-app'
        """
        import os
        return Path(os.getcwd()).name
    
    def register_provider(self, tag: str, provider: IContextProvider) -> None:
        """Register a context provider for a specific tag.
        
        Args:
            tag: Tag string (e.g., "@memory", "@docs")
            provider: Provider instance implementing IContextProvider
            
        Example:
            >>> injector = ContextInjector()
            >>> injector.register_provider("@memory", MyMemoryProvider())
            >>> injector.register_provider("@code", MyCodeProvider())
        """
        if not tag.startswith("@"):
            tag = f"@{tag}"
        
        self.providers[tag] = provider
        
        # Auto-register tag in parser if not already registered
        if tag not in self.parser.valid_tags:
            self.parser.register_tag(tag)
    
    def inject(
        self,
        user_input: str,
        max_items: int = 10,
        min_relevance: float = 0.70
    ) -> Optional[str]:
        """Process user input and inject context if tags found.
        
        This is the main method for simple context injection.
        
        Args:
            user_input: User's message/query containing tags
            max_items: Maximum total context items to return
            min_relevance: Minimum relevance score (0.0-1.0)
            
        Returns:
            Formatted context string if tags found, None otherwise
            
        Example:
            >>> injector = ContextInjector()
            >>> injector.register_provider("@memory", provider)
            >>> 
            >>> context = injector.inject("@memory dark keyboard layout")
            >>> if context:
            ...     print(context)
            === BEGIN CONTEXT ===
            CRITICAL RULES FOR USING THIS CONTEXT:
            ...
        """
        # Parse tags from input
        tags = self.parser.parse(user_input)
        
        if not tags:
            return None
        
        # Process each tag
        all_items = []
        
        for tag in tags:
            # Create request
            request = ContextRequest(
                tag=tag.tag,
                query=tag.query,
                project=self.current_project,
                max_items=max_items,
                min_relevance=min_relevance,
                include_cross_project=(tag.modifier == 'all'),
                prefer_recent=True
            )
            
            # Get items from appropriate provider
            items = self._retrieve_from_provider(tag, request)
            all_items.extend(items)
        
        if not all_items:
            return None
        
        # Remove duplicates (by content hash)
        all_items = self._deduplicate_items(all_items)
        
        # Sort by relevance
        all_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit total items
        all_items = all_items[:max_items]
        
        # Format for injection (auto-detects cross-project warning)
        response = self.formatter.format(all_items, self.current_project)
        
        return response.formatted_context
    
    def inject_with_metrics(
        self,
        user_input: str,
        max_items: int = 10,
        min_relevance: float = 0.70
    ) -> ContextResponse:
        """Process user input and return full ContextResponse with metrics.
        
        Use this when you need performance metrics, item counts, etc.
        
        Args:
            user_input: User's message/query containing tags
            max_items: Maximum total context items to return
            min_relevance: Minimum relevance score (0.0-1.0)
            
        Returns:
            ContextResponse with formatted context and metrics
            
        Example:
            >>> response = injector.inject_with_metrics("@memory query")
            >>> print(f"Found {response.total_found} items")
            >>> print(f"After filtering: {response.filtered_count}")
            >>> print(f"Performance: {response.performance_ms:.2f}ms")
            >>> print(f"Filter ratio: {response.filter_ratio:.1%}")
        """
        start_time = time.time()
        
        # Parse tags
        tags = self.parser.parse(user_input)
        
        if not tags:
            return ContextResponse(
                formatted_context="",
                items=[],
                total_found=0,
                filtered_count=0
            )
        
        # Process each tag
        all_items = []
        total_found = 0
        
        for tag in tags:
            request = ContextRequest(
                tag=tag.tag,
                query=tag.query,
                project=self.current_project,
                max_items=max_items,
                min_relevance=min_relevance,
                include_cross_project=(tag.modifier == 'all'),
                prefer_recent=True
            )
            
            items = self._retrieve_from_provider(tag, request)
            all_items.extend(items)
            total_found += len(items)
        
        # Deduplicate and sort
        all_items = self._deduplicate_items(all_items)
        all_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit items
        filtered_items = all_items[:max_items]
        
        # Format (auto-detects cross-project warning)
        response = self.formatter.format(filtered_items, self.current_project)
        
        # Update metrics
        response.total_found = total_found
        response.filtered_count = len(filtered_items)
        
        # Calculate performance
        elapsed_ms = (time.time() - start_time) * 1000
        
        return ContextResponse(
            formatted_context=response.formatted_context,
            items=response.items,
            total_found=total_found,
            filtered_count=len(filtered_items),
            cross_project_warning=response.cross_project_warning,
            performance_ms=elapsed_ms
        )
    
    def _retrieve_from_provider(
        self,
        tag: ParsedTag,
        request: ContextRequest
    ) -> List[ContextItem]:
        """Retrieve context from appropriate provider.
        
        Args:
            tag: Parsed tag
            request: Context request
            
        Returns:
            List of ContextItem objects
        """
        # Get provider
        provider = self.providers.get(tag.tag)
        
        if not provider:
            # Silently skip unknown tags (no print/log in library code)
            return []
        
        # Check if available
        if not provider.is_available():
            return []
        
        # Standard retrieval
        return provider.retrieve(request)
    
    def _deduplicate_items(self, items: List[ContextItem]) -> List[ContextItem]:
        """Remove duplicate items based on content similarity.
        
        Uses first 100 characters as hash for deduplication.
        
        Args:
            items: List of ContextItem objects
            
        Returns:
            Deduplicated list
            
        Example:
            >>> # Two items with same content
            >>> items = [
            ...     ContextItem("Same content...", ...),
            ...     ContextItem("Same content...", ...),
            ...     ContextItem("Different...", ...)
            ... ]
            >>> deduplicated = injector._deduplicate_items(items)
            >>> len(deduplicated)
            2
        """
        seen_content = set()
        deduplicated = []
        
        for item in items:
            # Use first 100 chars as hash for deduplication
            content_hash = item.content[:100].strip()
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(item)
        
        return deduplicated
    
    def has_tags(self, user_input: str) -> bool:
        """Check if user input contains any context tags.
        
        Args:
            user_input: User's message/query
            
        Returns:
            True if tags found
            
        Example:
            >>> injector.has_tags("@memory dark keyboard")
            True
            >>> injector.has_tags("plain text without tags")
            False
        """
        return self.parser.has_tags(user_input)
    
    def extract_query_only(self, user_input: str) -> str:
        """Remove tags from input, leaving only the query text.
        
        Args:
            user_input: User's message/query
            
        Returns:
            Input with tags removed
            
        Example:
            >>> injector.extract_query_only("Tell me @memory query about this")
            'Tell me'
        """
        return self.parser.remove_tags(user_input)


# Convenience function for quick injection
def inject_context(
    user_input: str,
    providers: Dict[str, IContextProvider],
    project: Optional[str] = None,
    **kwargs
) -> Optional[str]:
    """Quick function to inject context from user input.
    
    Args:
        user_input: User's message/query containing tags
        providers: Dictionary mapping tags to provider instances
        project: Current project (auto-detected if None)
        **kwargs: Additional arguments (max_items, min_relevance)
        
    Returns:
        Formatted context string if tags found, None otherwise
        
    Example:
        >>> providers = {
        ...     "@memory": MyMemoryProvider(),
        ...     "@code": MyCodeProvider()
        ... }
        >>> context = inject_context("@memory query", providers)
        >>> if context:
        ...     print(context)
    """
    injector = ContextInjector(current_project=project)
    
    # Register all providers
    for tag, provider in providers.items():
        injector.register_provider(tag, provider)
    
    return injector.inject(user_input, **kwargs)
