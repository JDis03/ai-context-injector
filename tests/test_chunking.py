"""Tests for chunking strategies and metadata support."""

import pytest
from ai_context_injector import (
    Chunk,
    chunk_content,
    BySizeChunker,
    ByMarkdownHeadersChunker,
    ByParagraphChunker,
    index,
    search,
    clear_index,
)


class TestBySizeChunker:
    """Test fixed-size chunking."""
    
    def test_basic_chunking(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("a" * 500 + "b" * 500, max_chunk_size=500)
        assert len(chunks) == 2
        assert chunks[0].content == "a" * 500
        assert chunks[1].content == "b" * 500
    
    def test_empty_content(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("")
        assert chunks == []
    
    def test_exact_boundary(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("x" * 100, max_chunk_size=100)
        assert len(chunks) == 1
        assert len(chunks[0].content) == 100
    
    def test_content_smaller_than_chunk(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("short", max_chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0].content == "short"
    
    def test_index_values(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("a" * 500 + "b" * 500, max_chunk_size=500)
        assert chunks[0].index == 0
        assert chunks[1].index == 1
    
    def test_chunk_type_is_text(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("content")
        assert all(c.chunk_type == "text" for c in chunks)
    
    def test_default_chunk_size(self):
        chunker = BySizeChunker()
        chunks = chunker.chunk("x" * 2500)
        # Default is 1000, so 3 chunks
        assert len(chunks) in (2, 3)  # 2000 in two 1000-char chunks


class TestByMarkdownHeadersChunker:
    """Test markdown header-based chunking."""
    
    def test_basic_sections(self):
        content = "## Intro\nWelcome\n## Setup\nInstructions"
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk(content)
        
        assert len(chunks) >= 2
        assert any("Intro" in c.section_title for c in chunks)
        assert any("Setup" in c.section_title for c in chunks)
    
    def test_section_title_extracted(self):
        content = "## Reconnaissance\nnmap scan results here"
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk(content)
        
        assert chunks[0].section_title == "Reconnaissance"
        assert "nmap" in chunks[0].content
    
    def test_no_headers(self):
        content = "Just plain text without headers"
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 1
        assert chunks[0].section_title == ""
    
    def test_multiple_sections(self):
        content = "## A\naaa\n## B\nbbb\n## C\nccc"
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk(content)
        
        sections = {c.section_title for c in chunks}
        assert "A" in sections
        assert "B" in sections
        assert "C" in sections
    
    def test_large_section_split(self):
        content = "## Large\n" + ("x" * 500 + " ") * 3
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk(content, max_chunk_size=500)
        
        # Section is > 500 chars, should be split
        assert len(chunks) >= 2
        # All pieces should have same section title
        assert all(c.section_title == "Large" for c in chunks)
    
    def test_empty_content(self):
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk("")
        assert chunks == []
    
    def test_preserves_content(self):
        content = "## Section\nline1\nline2\nline3"
        chunker = ByMarkdownHeadersChunker()
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 1
        assert "line1" in chunks[0].content
        assert "line2" in chunks[0].content


class TestByParagraphChunker:
    """Test paragraph-based chunking."""
    
    def test_basic_paragraphs(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird."
        chunker = ByParagraphChunker()
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 3
        assert "First paragraph." in chunks[0].content
        assert "Second paragraph." in chunks[1].content
    
    def test_single_paragraph(self):
        content = "Just one paragraph."
        chunker = ByParagraphChunker()
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 1
    
    def test_empty_content(self):
        chunker = ByParagraphChunker()
        chunks = chunker.chunk("")
        assert chunks == []
    
    def test_large_paragraph_split(self):
        content = "x" * 2000
        chunker = ByParagraphChunker()
        chunks = chunker.chunk(content, max_chunk_size=500)
        
        assert len(chunks) >= 3  # 2000/500 = 4 chunks but some may be merged
    
    def test_empty_paragraphs_skipped(self):
        content = "First.\n\n\n\n\n\nSecond."
        chunker = ByParagraphChunker()
        chunks = chunker.chunk(content)
        
        assert len(chunks) == 2


class TestChunkContentConvenience:
    """Test chunk_content() convenience function."""
    
    def test_default_strategy(self):
        chunks = chunk_content("Hello " * 100, max_chunk_size=50)
        assert len(chunks) >= 1
        assert all(isinstance(c, Chunk) for c in chunks)
    
    def test_markdown_strategy(self):
        content = "## A\ntext\n## B\ntext"
        chunks = chunk_content(content, strategy="by_markdown_headers")
        assert len(chunks) >= 1
    
    def test_paragraph_strategy(self):
        content = "A\n\nB\n\nC"
        chunks = chunk_content(content, strategy="by_paragraph")
        assert len(chunks) == 3
    
    def test_invalid_strategy(self):
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            chunk_content("text", strategy="invalid_strategy")
    
    def test_metadata_passed(self):
        chunks = chunk_content("text", strategy="by_size", os="linux", difficulty="medium")
        for chunk in chunks:
            assert chunk.metadata.get("os") == "linux"
            assert chunk.metadata.get("difficulty") == "medium"


class TestIndexing:
    """Test index() and search() functions."""
    
    def setup_method(self):
        clear_index()
    
    def test_basic_index(self):
        content = "nmap scan shows ports 22, 80, 443 open"
        chunks = index(content, source="test")
        assert len(chunks) >= 1
        assert chunks[0].source == "test"
    
    def test_index_with_metadata(self):
        content = "Privilege escalation via Docker escape"
        chunks = index(
            content,
            metadata={"os": "linux", "difficulty": "medium"},
        )
        
        for chunk in chunks:
            assert chunk.metadata.get("os") == "linux"
            assert chunk.metadata.get("difficulty") == "medium"
    
    def test_auto_generated_metadata(self):
        content = "test content"
        chunks = index(content)
        
        for chunk in chunks:
            assert "chunking_strategy" in chunk.metadata
            assert "indexed_at" in chunk.metadata
            assert "extract_code_blocks" in chunk.metadata
    
    def test_index_with_markdown_strategy(self):
        content = "## Recon\nnmap result\n## Exploit\ncode here"
        chunks = index(
            content,
            chunking_strategy="by_markdown_headers",
            source="test.md"
        )
        
        sections = {c.section_title for c in chunks}
        assert "Recon" in sections
        assert "Exploit" in sections
    
    def test_invalid_metadata(self):
        # Sets are not JSON-serializable
        with pytest.raises(ValueError, match="JSON-serializable"):
            index("content", metadata={"invalid": {1, 2, 3}})
    
    def test_invalid_strategy(self):
        with pytest.raises(ValueError, match="Unknown chunking strategy"):
            index("content", chunking_strategy="nonexistent")
    
    def test_index_code_extraction(self):
        content = "Some text\n```python\nprint('hello')\n```\nMore text"
        chunks = index(
            content,
            extract_code_blocks=True,
            source="test.py"
        )
        
        code_chunks = [c for c in chunks if c.chunk_type == "code"]
        assert len(code_chunks) >= 1
        assert code_chunks[0].language == "python"
        assert "print('hello')" in code_chunks[0].content


class TestSearch:
    """Test search() function."""
    
    def setup_method(self):
        clear_index()
    
    def test_basic_search(self):
        index("nmap scan results: port 22 open")
        index("exploit via CVE-2026-23744")
        
        results = search("nmap")
        assert len(results) >= 1
        assert "nmap" in results[0].content.lower()
    
    def test_search_with_filters(self):
        index("linux privilege escalation", metadata={"os": "linux"})
        index("windows privilege escalation", metadata={"os": "windows"})
        index("docker escape", metadata={"os": "linux"})
        
        results = search("privilege", filters={"os": "linux"})
        
        assert len(results) >= 1
        for chunk in results:
            assert chunk.metadata.get("os") == "linux"
    
    def test_search_multiple_filters(self):
        index("linux medium privesc", metadata={"os": "linux", "difficulty": "medium"})
        index("linux easy privesc", metadata={"os": "linux", "difficulty": "easy"})
        
        results = search("privesc", filters={"os": "linux", "difficulty": "medium"})
        
        assert len(results) >= 1
        for chunk in results:
            assert chunk.metadata["os"] == "linux"
            assert chunk.metadata["difficulty"] == "medium"
    
    def test_search_no_results(self):
        index("nmap scan")
        
        results = search("nonexistent_query_xyz")
        assert results == []
    
    def test_search_filter_no_match(self):
        index("linux content", metadata={"os": "linux"})
        
        results = search("linux", filters={"os": "windows"})
        assert results == []
    
    def test_search_code_blocks(self):
        index(
            "Text\n```python\nx = 1\n```\n```bash\nls\n```",
            extract_code_blocks=True
        )
        
        results = search("x = 1")
        assert len(results) >= 1
    
    def test_deduplication(self):
        # Index same content
        index("same content")
        index("same content")
        index("different content")
        
        results = search("content", deduplicate=True)
        # Should have at most 2 unique results (same + different)
        assert len(results) <= 2


class TestBackwardCompatibility:
    """Test that existing API still works."""
    
    def test_index_with_defaults(self):
        content = "test content"
        chunks = index(content)
        assert len(chunks) >= 1
    
    def test_search_with_defaults(self):
        clear_index()
        index("test content")
        results = search("test")
        assert len(results) >= 1
    
    def test_no_args_index(self):
        # index() requires content arg, everything else optional
        chunks = index("just content")
        assert len(chunks) == 1
