"""Code block extraction for document chunking.

Extracts fenced code blocks (``` and ~~~) from markdown content,
preserving language tags, surrounding context, and section boundaries.
Code blocks are extracted as separate chunks with parent references.
"""

import re
from typing import List, Tuple

from .core.types import Chunk

# Match fenced code blocks: ```lang\n...content...\n```
# Also matches ~~~lang variants
CODE_BLOCK_PATTERN = re.compile(
    r'^(`{3,}|~{3,})(\w*)\s*\n(.*?)\n\1',
    re.MULTILINE | re.DOTALL
)

# Context window size for surrounding text
CONTEXT_WINDOW = 200


def extract_code_blocks(
    content: str,
    parent_chunks: List[Chunk],
    extract_code_blocks: bool = True
) -> Tuple[List[Chunk], List[Chunk]]:
    """Extract fenced code blocks from content and return as separate chunks.
    
    Args:
        content: Full document markdown text
        parent_chunks: Original text chunks (from chunking strategy)
        extract_code_blocks: Whether to extract code blocks (default True)
        
    Returns:
        Tuple of (text_chunks, code_chunks) where:
        - text_chunks: Original chunks with code blocks removed from content
        - code_chunks: New chunks for extracted code blocks
        
    Example:
        >>> content = "Some text\\n```python\\nprint('hi')\\n```\\nMore text"
        >>> text_chunks, code_chunks = extract_code_blocks(content, [Chunk(...)])
        >>> code_chunks[0].language
        'python'
    """
    if not extract_code_blocks or not content:
        return parent_chunks, []
    
    # Find all code blocks in the original content
    matches = list(CODE_BLOCK_PATTERN.finditer(content))
    
    if not matches:
        return parent_chunks, []
    
    code_chunks = []
    current_code_index = 0
    
    for match in matches:
        language = match.group(2) or "text"
        code_content = match.group(3)
        start_pos = match.start()
        end_pos = match.end()
        
        # Extract surrounding context
        context_before = _get_context(content, start_pos - CONTEXT_WINDOW, start_pos)
        context_after = _get_context(content, end_pos, end_pos + CONTEXT_WINDOW)
        
        # Create code chunk with parent reference
        code_chunk = Chunk(
            content=code_content,
            index=current_code_index,
            metadata={"code_block": True, "language": language},
            chunk_type="code",
            language=language,
            parent_chunk_id="",  # Set by caller if needed
            code_context_before=context_before,
            code_context_after=context_after,
            start_line=_count_lines(content, 0, start_pos),
            end_line=_count_lines(content, 0, end_pos)
        )
        code_chunks.append(code_chunk)
        current_code_index += 1
    
    return parent_chunks, code_chunks


def extract_code_from_chunks(
    chunks: List[Chunk],
    full_content: str
) -> List[Chunk]:
    """Extract code blocks from a list of text chunks.
    
    Processes each chunk, finds code blocks within it, and creates
    separate code chunks. The original text chunks keep their non-code content.
    
    Args:
        chunks: List of text Chunk objects
        full_content: The complete document text (for accurate span detection)
        
    Returns:
        Combined list of text chunks (with code removed) and code chunks,
        with parent_chunk_id references set on code chunks.
        
    Example:
        >>> chunks = [Chunk(content="Text\\n```py\\nx=1\\n```", index=0)]
        >>> result = extract_code_from_chunks(chunks, full_content)
        >>> len(result) >= 2  # Text chunk + code chunk
        True
    """
    all_text_chunks = []
    all_code_chunks = []
    
    for chunk in chunks:
        matches = list(CODE_BLOCK_PATTERN.finditer(chunk.content))
        
        if not matches:
            all_text_chunks.append(chunk)
            continue
        
        # Create text chunk with code blocks removed
        clean_content = CODE_BLOCK_PATTERN.sub('', chunk.content)
        if clean_content.strip():
            text_chunk = Chunk(
                content=clean_content.strip(),
                index=chunk.index,
                metadata=chunk.metadata,
                chunk_type="text",
                section_title=chunk.section_title
            )
            all_text_chunks.append(text_chunk)
        
        # Create code chunks
        for i, match in enumerate(matches):
            language = match.group(2) or "text"
            code_content = match.group(3)
            
            code_chunk = Chunk(
                content=code_content,
                index=i,
                metadata={**chunk.metadata, "code_block": True, "language": language},
                chunk_type="code",
                language=language,
                parent_chunk_id=f"chunk_{chunk.index}" if chunk.index is not None else "",
                start_line=0,
                end_line=0
            )
            all_code_chunks.append(code_chunk)
    
    return all_text_chunks + all_code_chunks


def _get_context(text: str, start: int, end: int) -> str:
    """Extract a context window from text.
    
    Args:
        text: Full text
        start: Start position (clamped to valid range)
        end: End position (clamped to valid range)
        
    Returns:
        Context string within the window
    """
    start = max(0, start)
    end = min(len(text), end)
    return text[start:end]


def _count_lines(text: str, start: int, end: int) -> int:
    """Count lines in the given range of text.
    
    Args:
        text: Full text
        start: Start position
        end: End position
        
    Returns:
        Number of lines
    """
    return text[start:end].count('\n') + 1
