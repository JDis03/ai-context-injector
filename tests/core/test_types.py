"""Tests for core data types."""

import pytest
from datetime import datetime
from ai_context_injector.core import ContextItem, ContextRequest, ContextResponse, ParsedTag


class TestContextItem:
    """Tests for ContextItem dataclass."""
    
    def test_basic_creation(self):
        """Test basic ContextItem creation."""
        item = ContextItem(
            content="Test content",
            source="memory",
            project="test-project",
            metadata={"type": "decision"},
            relevance_score=0.95,
            timestamp=datetime(2026, 5, 29)
        )
        
        assert item.content == "Test content"
        assert item.source == "memory"
        assert item.project == "test-project"
        assert item.relevance_score == 0.95
        assert item.metadata == {"type": "decision"}
    
    def test_citation_memory(self):
        """Test citation generation for memory source."""
        item = ContextItem(
            content="Decision: Use SQLite",
            source="memory",
            project="DarkKeyboard",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2026, 5, 29)
        )
        
        assert item.citation() == "[memory:DarkKeyboard:2026-05-29]"
    
    def test_citation_code_with_lines(self):
        """Test citation for code with file and line range."""
        item = ContextItem(
            content="def parse(): ...",
            source="codebase",
            project="ai-context-injector",
            metadata={},
            relevance_score=0.85,
            timestamp=datetime(2026, 5, 29),
            file_path="parser.py",
            line_range=(10, 25)
        )
        
        assert item.citation() == "[code:parser.py:10-25]"
    
    def test_citation_code_file_only(self):
        """Test citation for code with file but no lines."""
        item = ContextItem(
            content="File content",
            source="codebase",
            project="test",
            metadata={},
            relevance_score=0.8,
            timestamp=datetime(2026, 5, 29),
            file_path="test.py"
        )
        
        assert item.citation() == "[code:test.py]"
    
    def test_citation_code_no_file(self):
        """Test citation for code without file path."""
        item = ContextItem(
            content="Code snippet",
            source="codebase",
            project="test",
            metadata={},
            relevance_score=0.8,
            timestamp=datetime(2026, 5, 29)
        )
        
        assert item.citation() == "[code:test:2026-05-29]"
    
    def test_citation_session_with_id(self):
        """Test citation for session with session ID."""
        item = ContextItem(
            content="Session summary",
            source="session",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2026, 5, 29),
            session_id="abc123"
        )
        
        assert item.citation() == "[session:abc123:2026-05-29]"
    
    def test_citation_session_no_id(self):
        """Test citation for session without ID."""
        item = ContextItem(
            content="Session summary",
            source="session",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2026, 5, 29)
        )
        
        assert item.citation() == "[session:test:2026-05-29]"
    
    def test_citation_custom_source(self):
        """Test citation for custom source type."""
        item = ContextItem(
            content="Custom content",
            source="docs",
            project="test",
            metadata={},
            relevance_score=0.85,
            timestamp=datetime(2026, 5, 29)
        )
        
        assert item.citation() == "[docs:test:2026-05-29]"
    
    def test_repr(self):
        """Test string representation."""
        item = ContextItem(
            content="Short content",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.95,
            timestamp=datetime.now()
        )
        
        repr_str = repr(item)
        assert "ContextItem" in repr_str
        assert "memory" in repr_str
        assert "test" in repr_str
        assert "0.95" in repr_str
    
    def test_repr_long_content(self):
        """Test repr truncates long content."""
        item = ContextItem(
            content="A" * 100,
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        repr_str = repr(item)
        assert "..." in repr_str


class TestContextRequest:
    """Tests for ContextRequest dataclass."""
    
    def test_basic_creation(self):
        """Test basic ContextRequest creation."""
        request = ContextRequest(
            tag="@memory",
            query="test query",
            project="test-project"
        )
        
        assert request.tag == "@memory"
        assert request.query == "test query"
        assert request.project == "test-project"
        assert request.max_items == 10  # default
        assert request.min_relevance == 0.70  # default
        assert request.include_cross_project is False
        assert request.prefer_recent is True
    
    def test_custom_limits(self):
        """Test custom max_items and min_relevance."""
        request = ContextRequest(
            tag="@code",
            query="function",
            project="test",
            max_items=5,
            min_relevance=0.80
        )
        
        assert request.max_items == 5
        assert request.min_relevance == 0.80
    
    def test_cross_project(self):
        """Test cross-project flag."""
        request = ContextRequest(
            tag="@memory",
            query="query",
            project="test",
            include_cross_project=True
        )
        
        assert request.include_cross_project is True
    
    def test_repr(self):
        """Test string representation."""
        request = ContextRequest(
            tag="@memory",
            query="test",
            project="proj"
        )
        
        repr_str = repr(request)
        assert "ContextRequest" in repr_str
        assert "@memory" in repr_str
        assert "test" in repr_str


class TestContextResponse:
    """Tests for ContextResponse dataclass."""
    
    def test_basic_creation(self):
        """Test basic ContextResponse creation."""
        item = ContextItem(
            content="test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = ContextResponse(
            formatted_context="=== BEGIN CONTEXT ===\n...",
            items=[item],
            total_found=5,
            filtered_count=1
        )
        
        assert response.formatted_context.startswith("=== BEGIN")
        assert len(response.items) == 1
        assert response.total_found == 5
        assert response.filtered_count == 1
    
    def test_has_context_true(self):
        """Test has_context property when items exist."""
        item = ContextItem(
            content="test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = ContextResponse(
            formatted_context="...",
            items=[item],
            total_found=1,
            filtered_count=1
        )
        
        assert response.has_context is True
    
    def test_has_context_false(self):
        """Test has_context property when no items."""
        response = ContextResponse(
            formatted_context="",
            items=[],
            total_found=0,
            filtered_count=0
        )
        
        assert response.has_context is False
    
    def test_filter_ratio(self):
        """Test filter_ratio calculation."""
        response = ContextResponse(
            formatted_context="...",
            items=[],
            total_found=10,
            filtered_count=7
        )
        
        assert response.filter_ratio == 0.7
    
    def test_filter_ratio_zero_total(self):
        """Test filter_ratio when total_found is 0."""
        response = ContextResponse(
            formatted_context="",
            items=[],
            total_found=0,
            filtered_count=0
        )
        
        assert response.filter_ratio == 0.0
    
    def test_filter_ratio_perfect(self):
        """Test filter_ratio when all items pass."""
        response = ContextResponse(
            formatted_context="...",
            items=[],
            total_found=5,
            filtered_count=5
        )
        
        assert response.filter_ratio == 1.0
    
    def test_cross_project_warning(self):
        """Test cross_project_warning field."""
        response = ContextResponse(
            formatted_context="...",
            items=[],
            total_found=1,
            filtered_count=1,
            cross_project_warning="Results from other projects: DarkSSH"
        )
        
        assert response.cross_project_warning is not None
        assert "DarkSSH" in response.cross_project_warning
    
    def test_performance_ms(self):
        """Test performance_ms field."""
        response = ContextResponse(
            formatted_context="...",
            items=[],
            total_found=1,
            filtered_count=1,
            performance_ms=17.5
        )
        
        assert response.performance_ms == 17.5
    
    def test_repr(self):
        """Test string representation."""
        response = ContextResponse(
            formatted_context="...",
            items=[],
            total_found=10,
            filtered_count=7
        )
        
        repr_str = repr(response)
        assert "ContextResponse" in repr_str
        assert "70.00%" in repr_str  # filter_ratio


class TestParsedTag:
    """Tests for ParsedTag dataclass."""
    
    def test_basic_creation(self):
        """Test basic ParsedTag creation."""
        tag = ParsedTag(
            tag="@memory",
            modifier=None,
            query="dark keyboard",
            full_match="@memory dark keyboard",
            start_pos=0,
            end_pos=21
        )
        
        assert tag.tag == "@memory"
        assert tag.modifier is None
        assert tag.query == "dark keyboard"
        assert tag.full_match == "@memory dark keyboard"
        assert tag.start_pos == 0
        assert tag.end_pos == 21
    
    def test_with_modifier(self):
        """Test ParsedTag with modifier."""
        tag = ParsedTag(
            tag="@memory",
            modifier="all",
            query="query",
            full_match="@memory:all query",
            start_pos=0,
            end_pos=17
        )
        
        assert tag.modifier == "all"
    
    def test_tag_with_modifier_none(self):
        """Test tag_with_modifier when no modifier."""
        tag = ParsedTag(
            tag="@memory",
            modifier=None,
            query="query",
            full_match="@memory query",
            start_pos=0,
            end_pos=13
        )
        
        assert tag.tag_with_modifier == "@memory"
    
    def test_tag_with_modifier_present(self):
        """Test tag_with_modifier when modifier exists."""
        tag = ParsedTag(
            tag="@memory",
            modifier="all",
            query="query",
            full_match="@memory:all query",
            start_pos=0,
            end_pos=17
        )
        
        assert tag.tag_with_modifier == "@memory:all"
    
    def test_repr(self):
        """Test string representation."""
        tag = ParsedTag(
            tag="@memory",
            modifier="all",
            query="test query",
            full_match="@memory:all test query",
            start_pos=0,
            end_pos=22
        )
        
        repr_str = repr(tag)
        assert "ParsedTag" in repr_str
        assert "@memory:all" in repr_str
        assert "test query" in repr_str
