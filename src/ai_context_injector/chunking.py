"""Pluggable chunking strategies for document indexing.

Provides three built-in strategies:
- BySizeChunker: Fixed-size chunks (default, backward compatible)
- ByMarkdownHeadersChunker: Splits on ## headers, preserving section structure
- ByParagraphChunker: Splits on double newlines (paragraphs)

All strategies enforce max_chunk_size as a hard limit.
"""

import re
from typing import List, Protocol

from .core.types import Chunk


class ChunkingStrategy(Protocol):
    """Protocol for pluggable chunking strategies.
    
    Implementations must accept content string and optional keyword args,
    returning a list of Chunk objects.
    """
    
    def chunk(self, content: str, **kwargs) -> List[Chunk]:
        """Split content into chunks according to this strategy.
        
        Args:
            content: The full document text to chunk
            **kwargs: Strategy-specific options
            
        Returns:
            List of Chunk objects in document order
        """
        ...


class BySizeChunker:
    """Fixed-size chunking strategy.
    
    Splits content into chunks of exactly max_chunk_size characters.
    This is the default strategy and maintains backward compatibility.
    Overlapping is not used — boundaries are strict character counts.
    
    Example:
        >>> chunker = BySizeChunker()
        >>> chunks = chunker.chunk("Hello world! " * 100, max_chunk_size=50)
        >>> len(chunks[0].content) <= 50
        True
    """
    
    DEFAULT_MAX_CHUNK_SIZE = 1000
    
    def chunk(self, content: str, max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE, **kwargs) -> List[Chunk]:
        """Split content into fixed-size chunks.
        
        Args:
            content: Full document text
            max_chunk_size: Maximum characters per chunk (default 1000)
            **kwargs: Additional metadata passed to each chunk
            
        Returns:
            List of Chunk objects
        """
        if not content:
            return []
        
        chunks = []
        for i in range(0, len(content), max_chunk_size):
            chunk_content = content[i:i + max_chunk_size]
            chunks.append(Chunk(
                content=chunk_content,
                index=len(chunks),
                metadata=dict(kwargs),
                chunk_type="text"
            ))
        
        return chunks


class ByMarkdownHeadersChunker:
    """Chunking strategy that respects markdown header structure.
    
    Splits content on ## (H2) headers, keeping each section together.
    If a section exceeds max_chunk_size, it is further split with
    subsection markers preserving the section context.
    
    Only H2 (##) headers are used as primary section boundaries.
    H3 and below are kept within their parent section.
    
    Example:
        >>> chunker = ByMarkdownHeadersChunker()
        >>> content = "## Recon\\nnmap scan...\\n## Exploit\\ncode..."
        >>> chunks = chunker.chunk(content)
        >>> chunks[0].section_title
        'Recon'
    """
    
    DEFAULT_MAX_CHUNK_SIZE = 1000
    
    def chunk(self, content: str, max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE, **kwargs) -> List[Chunk]:
        """Split content by markdown headers.
        
        Args:
            content: Markdown document text
            max_chunk_size: Maximum characters per chunk
            **kwargs: Additional metadata passed to each chunk
            
        Returns:
            List of Chunk objects
        """
        if not content:
            return []
        
        # Split on H2 headers: ## Title
        # Pattern captures title and section content
        sections = re.split(r'^(##\s+.+)$', content, flags=re.MULTILINE)
        
        chunks = []
        current_title = ""
        current_content = ""
        
        for part in sections:
            part = part.strip()
            if not part:
                continue
            
            if part.startswith("## "):
                # Save previous section if any
                if current_content.strip():
                    chunks.extend(self._split_section(
                        current_content,
                        current_title,
                        max_chunk_size,
                        len(chunks),
                        kwargs
                    ))
                
                # Start new section
                current_title = part[3:].strip()  # Remove "## "
                current_content = ""
            else:
                current_content = part
        
        # Don't forget the last section
        if current_content.strip():
            chunks.extend(self._split_section(
                current_content,
                current_title,
                max_chunk_size,
                len(chunks),
                kwargs
            ))
        
        # If no sections found, treat as single section
        if not chunks and content.strip():
            chunks.extend(self._split_section(
                content.strip(),
                "",
                max_chunk_size,
                0,
                kwargs
            ))
        
        return chunks
    
    def _split_section(
        self,
        content: str,
        title: str,
        max_chunk_size: int,
        start_index: int,
        metadata: dict
    ) -> List[Chunk]:
        """Split a single section into chunks if it exceeds max_chunk_size.
        
        Args:
            content: Section content
            title: Section title (from ## header)
            max_chunk_size: Maximum chunk size
            start_index: Starting chunk index
            metadata: Extra metadata dict
            
        Returns:
            List of Chunk objects
        """
        chunks = []
        
        if len(content) <= max_chunk_size:
            chunks.append(Chunk(
                content=content,
                index=start_index,
                metadata=dict(metadata),
                chunk_type="text",
                section_title=title
            ))
        else:
            # Split oversized section with subsection markers
            for i in range(0, len(content), max_chunk_size):
                chunk_content = content[i:i + max_chunk_size]
                chunks.append(Chunk(
                    content=chunk_content,
                    index=start_index + len(chunks),
                    metadata=dict(metadata),
                    chunk_type="text",
                    section_title=title
                ))
        
        return chunks


class ByParagraphChunker:
    """Chunking strategy that splits on paragraph boundaries.
    
    Splits content on double newlines (\\n\\n), keeping paragraphs together.
    If a paragraph exceeds max_chunk_size, it is further split.
    
    Example:
        >>> chunker = ByParagraphChunker()
        >>> content = "First paragraph.\\n\\nSecond paragraph."
        >>> chunks = chunker.chunk(content)
        >>> len(chunks)
        2
    """
    
    DEFAULT_MAX_CHUNK_SIZE = 1000
    
    def chunk(self, content: str, max_chunk_size: int = DEFAULT_MAX_CHUNK_SIZE, **kwargs) -> List[Chunk]:
        """Split content by paragraphs.
        
        Args:
            content: Document text
            max_chunk_size: Maximum characters per chunk
            **kwargs: Additional metadata passed to each chunk
            
        Returns:
            List of Chunk objects
        """
        if not content:
            return []
        
        # Split on double newlines (paragraphs)
        paragraphs = re.split(r'\n\s*\n', content)
        
        chunks = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            if len(para) <= max_chunk_size:
                chunks.append(Chunk(
                    content=para,
                    index=len(chunks),
                    metadata=dict(kwargs),
                    chunk_type="text"
                ))
            else:
                # Split oversized paragraph
                for i in range(0, len(para), max_chunk_size):
                    chunks.append(Chunk(
                        content=para[i:i + max_chunk_size],
                        index=len(chunks),
                        metadata=dict(kwargs),
                        chunk_type="text"
                    ))
        
        return chunks


# Convenience function
def chunk_content(
    content: str,
    strategy: str = "by_size",
    max_chunk_size: int = 1000,
    **metadata
) -> List[Chunk]:
    """Chunk content using the specified strategy.
    
    Args:
        content: Document text to chunk
        strategy: Chunking strategy name ("by_size", "by_markdown_headers", "by_paragraph")
        max_chunk_size: Maximum characters per chunk
        **metadata: Extra metadata to attach to each chunk
        
    Returns:
        List of Chunk objects
        
    Raises:
        ValueError: If strategy name is invalid
        
    Example:
        >>> chunks = chunk_content("## Intro\\nHello", strategy="by_markdown_headers")
        >>> chunks[0].section_title
        'Intro'
    """
    strategies = {
        "by_size": BySizeChunker(),
        "by_markdown_headers": ByMarkdownHeadersChunker(),
        "by_paragraph": ByParagraphChunker(),
    }
    
    if strategy not in strategies:
        raise ValueError(
            f"Unknown chunking strategy: '{strategy}'. "
            f"Valid options: {list(strategies.keys())}"
        )
    
    chunker = strategies[strategy]
    return chunker.chunk(content, max_chunk_size=max_chunk_size, **metadata)
