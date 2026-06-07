"""Indexing and search API for structured document chunking.

Provides the main entry points for indexing content with metadata,
chunking strategies, and code block extraction.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from .chunking import ChunkingStrategy, BySizeChunker, chunk_content
from .core.types import Chunk
from .extractors import extract_code_from_chunks


# In-memory index for demo/testing (production would use a database)
class _MemoryIndex:
    """Simple in-memory index for storing and searching chunks."""
    
    def __init__(self):
        self.chunks: List[Chunk] = []
        self.sources: Dict[str, dict] = {}
    
    def add(self, chunks: List[Chunk], source: str = ""):
        """Add chunks to the index."""
        for chunk in chunks:
            chunk.source = source
            self.chunks.append(chunk)
    
    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[Chunk]:
        """Search chunks with optional metadata filtering.
        
        Simple substring matching for demo purposes.
        Production would use semantic/vector search.
        """
        results = []
        query_lower = query.lower()
        
        for chunk in self.chunks:
            # Basic relevance: substring match
            if query_lower in chunk.content.lower():
                results.append(chunk)
        
        # Apply metadata filters
        if filters:
            results = [
                chunk for chunk in results
                if _match_filters(chunk.metadata, filters)
            ]
        
        return results[:limit]
    
    def clear(self):
        """Clear the index."""
        self.chunks = []
        self.sources = {}


# Global index instance
_index = _MemoryIndex()


def _match_filters(metadata: dict, filters: dict) -> bool:
    """Check if metadata matches all filter criteria.
    
    Supports nested field access using dot notation for string keys
    and exact match for values.
    
    Args:
        metadata: Chunk metadata dict
        filters: Filter criteria dict
        
    Returns:
        True if all filters match
    """
    for key, value in filters.items():
        # Support nested access: "os.type" → metadata["os"]["type"]
        current = metadata
        parts = key.split(".")
        
        for part in parts[:-1]:
            if isinstance(current, dict):
                current = current.get(part, {})
            else:
                return False
        
        # Check last part
        if isinstance(current, dict):
            actual = current.get(parts[-1])
        else:
            return False
        
        # Support list containment
        if isinstance(actual, list) and not isinstance(value, list):
            if value not in actual:
                return False
        elif actual != value:
            return False
    
    return True


def index(
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    chunking_strategy: str = "by_size",
    extract_code_blocks: bool = False,
    max_chunk_size: int = 1000,
    source: str = ""
) -> List[Chunk]:
    """Index content using the specified chunking strategy and metadata.
    
    This is the main entry point for adding content to the index.
    All parameters beyond content are optional with sensible defaults.
    
    Args:
        content: Document text to index
        metadata: Arbitrary metadata dict (must be JSON-serializable)
        chunking_strategy: Strategy name ("by_size", "by_markdown_headers", "by_paragraph")
        extract_code_blocks: Extract code blocks as separate chunks
        max_chunk_size: Maximum characters per chunk
        source: Source document identifier
        
    Returns:
        List of Chunk objects added to the index
        
    Raises:
        ValueError: If metadata is not JSON-serializable or strategy is invalid
        
    Example:
        >>> chunks = index(
        ...     content="## Recon\\nnmap scan...\\n```bash\\nnmap -sV\\n```",
        ...     metadata={"os": "linux", "difficulty": "medium"},
        ...     chunking_strategy="by_markdown_headers",
        ...     extract_code_blocks=True,
        ...     source="kobold-writeup.md"
        ... )
        >>> len(chunks) >= 2  # Section chunk + code block chunk
        True
    """
    # Validate metadata
    if metadata is None:
        metadata = {}
    elif not _is_json_serializable(metadata):
        raise ValueError(
            "Metadata must be JSON-serializable (only dicts, lists, str, "
            f"int, float, bool, None). Got: {type(metadata)}"
        )
    
    # Add auto-generated fields
    metadata["chunking_strategy"] = chunking_strategy
    metadata["indexed_at"] = datetime.now().isoformat()
    metadata["extract_code_blocks"] = extract_code_blocks
    
    # Chunk the content
    chunks = chunk_content(
        content,
        strategy=chunking_strategy,
        max_chunk_size=max_chunk_size,
        **metadata
    )
    
    # Extract code blocks if requested
    if extract_code_blocks:
        chunks = extract_code_from_chunks(chunks, content)
    
    # Add to index
    _index.add(chunks, source=source)
    
    return chunks


def search(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    deduplicate: bool = True
) -> List[Chunk]:
    """Search the index with optional metadata filtering.
    
    Args:
        query: Search query string
        filters: Metadata key-value pairs to filter results
        limit: Maximum number of results to return
        deduplicate: Remove duplicate/similar chunks
        
    Returns:
        List of Chunk objects matching the query and filters
        
    Example:
        >>> # Search with filters
        >>> results = search("privilege escalation", filters={"os": "linux"})
        >>> all("linux" in chunk.metadata.get("os", "") for chunk in results)
        True
        
        >>> # Search with nested filter
        >>> results = search("exploit", filters={"difficulty": "medium"})
        
        >>> # Code blocks only
        >>> results = search("nmap", filters={"code_block": True})
        >>> all(chunk.chunk_type == "code" for chunk in results)
        True
    """
    results = _index.search(query, filters=filters, limit=limit)
    
    # Simple deduplication: first 100 chars hash
    if deduplicate and len(results) > 1:
        seen = set()
        unique = []
        for chunk in results:
            key = chunk.content[:100].strip()
            if key not in seen:
                seen.add(key)
                unique.append(chunk)
        return unique[:limit]
    
    return results


def clear_index():
    """Clear all data from the in-memory index."""
    _index.clear()


def _is_json_serializable(obj: Any) -> bool:
    """Check if an object is JSON-serializable.
    
    Args:
        obj: Object to check
        
    Returns:
        True if object can be serialized to JSON
    """
    try:
        json.dumps(obj)
        return True
    except (TypeError, ValueError):
        return False
