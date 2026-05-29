"""Core data types for context injection system.

This module defines the fundamental data structures used throughout the library:
- ContextItem: Single piece of retrieved context
- ContextRequest: Request for context retrieval
- ContextResponse: Formatted response ready for LLM injection
- ParsedTag: Result of parsing a tag from user input
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ContextItem:
    """Single piece of context retrieved from a provider.
    
    Attributes:
        content: The actual context text to inject
        source: Source type ("memory", "codebase", "session", or custom)
        project: Project name this context belongs to
        metadata: Provider-specific metadata (JSON-serializable)
        relevance_score: Relevance to query (0.0-1.0, higher is better)
        timestamp: When this context was created
        file_path: Optional file path (for code snippets)
        line_range: Optional line range tuple (start, end) for code
        session_id: Optional session identifier (for session context)
    
    Example:
        >>> item = ContextItem(
        ...     content="Decision: Use SQLite with WAL mode",
        ...     source="memory",
        ...     project="my-project",
        ...     metadata={"type": "decision"},
        ...     relevance_score=0.95,
        ...     timestamp=datetime.now()
        ... )
        >>> item.citation()
        '[memory:my-project:2026-05-29]'
    """
    
    content: str
    source: str
    project: str
    metadata: Dict[str, Any]
    relevance_score: float
    timestamp: datetime
    
    # Optional fields
    file_path: Optional[str] = None
    line_range: Optional[Tuple[int, int]] = None
    session_id: Optional[str] = None
    
    def citation(self) -> str:
        """Generate citation string for LLM to use.
        
        Returns:
            Citation string in format [source:identifier:date]
            
        Examples:
            Memory: [memory:project:2026-05-29]
            Code: [code:parser.py:10-25]
            Session: [session:abc123:2026-05-29]
        """
        date_str = self.timestamp.strftime('%Y-%m-%d')
        
        if self.source == "memory":
            return f"[memory:{self.project}:{date_str}]"
        elif self.source == "codebase":
            if self.file_path and self.line_range:
                return f"[code:{self.file_path}:{self.line_range[0]}-{self.line_range[1]}]"
            elif self.file_path:
                return f"[code:{self.file_path}]"
            else:
                return f"[code:{self.project}:{date_str}]"
        elif self.source == "session":
            if self.session_id:
                return f"[session:{self.session_id}:{date_str}]"
            else:
                return f"[session:{self.project}:{date_str}]"
        else:
            # Custom source type
            return f"[{self.source}:{self.project}:{date_str}]"
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return (f"ContextItem(source={self.source}, project={self.project}, "
                f"score={self.relevance_score:.2f}, content='{content_preview}')")


@dataclass
class ContextRequest:
    """Request for context retrieval.
    
    Attributes:
        tag: Tag string (e.g., "@memory", "@code", "@session")
        query: The search query text
        project: Current project name
        max_items: Maximum number of items to return
        min_relevance: Minimum relevance score (0.0-1.0) to include
        include_cross_project: Whether to search across all projects
        prefer_recent: Whether to weight recent items higher
    
    Example:
        >>> request = ContextRequest(
        ...     tag="@memory",
        ...     query="dark keyboard layout",
        ...     project="DarkKeyboard",
        ...     max_items=10,
        ...     min_relevance=0.70
        ... )
    """
    
    tag: str
    query: str
    project: str
    max_items: int = 10
    min_relevance: float = 0.70
    
    # Advanced options
    include_cross_project: bool = False
    prefer_recent: bool = True
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"ContextRequest(tag={self.tag}, query='{self.query}', "
                f"project={self.project}, max={self.max_items})")


@dataclass
class ContextResponse:
    """Response with formatted context ready for LLM injection.
    
    Attributes:
        formatted_context: Formatted string ready to inject into prompt
        items: Original ContextItem objects retrieved
        total_found: Total matches before filtering
        filtered_count: Number of items after relevance filtering
        cross_project_warning: Warning if cross-project results included
        performance_ms: Time taken to retrieve (milliseconds)
    
    Properties:
        has_context: True if any context was retrieved
        filter_ratio: Ratio of filtered/total (quality indicator)
    
    Example:
        >>> response = ContextResponse(
        ...     formatted_context="=== BEGIN CONTEXT ===\\n...",
        ...     items=[item1, item2],
        ...     total_found=5,
        ...     filtered_count=2
        ... )
        >>> response.has_context
        True
        >>> response.filter_ratio
        0.4
    """
    
    formatted_context: str
    items: List[ContextItem]
    total_found: int
    filtered_count: int
    
    # Optional metadata
    cross_project_warning: Optional[str] = None
    performance_ms: Optional[float] = None
    
    @property
    def has_context(self) -> bool:
        """Check if any context was retrieved."""
        return len(self.items) > 0
    
    @property
    def filter_ratio(self) -> float:
        """Ratio of filtered items to total found (quality indicator).
        
        Returns:
            Float between 0.0 and 1.0 (1.0 = all results were high quality)
        """
        if self.total_found == 0:
            return 0.0
        return self.filtered_count / self.total_found
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"ContextResponse(items={len(self.items)}, "
                f"total_found={self.total_found}, "
                f"filter_ratio={self.filter_ratio:.2%})")


@dataclass
class ParsedTag:
    """Result of parsing a tag from user input.
    
    Attributes:
        tag: Tag string (e.g., "@memory", "@code", "@session")
        modifier: Optional modifier (e.g., "all" from "@memory:all")
        query: The search query text
        full_match: Complete matched string from input
        start_pos: Start position in original text
        end_pos: End position in original text
    
    Properties:
        tag_with_modifier: Full tag including modifier if present
    
    Example:
        >>> parsed = ParsedTag(
        ...     tag="@memory",
        ...     modifier="all",
        ...     query="dark keyboard",
        ...     full_match="@memory:all dark keyboard",
        ...     start_pos=0,
        ...     end_pos=26
        ... )
        >>> parsed.tag_with_modifier
        '@memory:all'
    """
    
    tag: str
    modifier: Optional[str]
    query: str
    full_match: str
    start_pos: int
    end_pos: int
    
    @property
    def tag_with_modifier(self) -> str:
        """Get full tag including modifier if present.
        
        Returns:
            Tag string with modifier (e.g., "@memory:all") or just tag
        """
        if self.modifier:
            return f"{self.tag}:{self.modifier}"
        return self.tag
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"ParsedTag({self.tag_with_modifier}, query='{self.query}')"
