"""Tests for context formatter."""

import pytest
from datetime import datetime

from ai_context_injector.core import ContextFormatter, ContextItem, format_context


class TestContextFormatterBasic:
    """Tests for basic formatting functionality."""
    
    def test_format_with_delimiters(self):
        """Test that formatted output includes BEGIN/END delimiters."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test content",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2026, 5, 30)
        )
        
        response = formatter.format([item], "test")
        
        assert response.formatted_context.startswith("=== BEGIN CONTEXT ===")
        assert response.formatted_context.endswith("=== END CONTEXT ===")
    
    def test_format_empty_items(self):
        """Test formatting empty list returns empty response."""
        formatter = ContextFormatter()
        response = formatter.format([], "test")
        
        assert response.formatted_context == ""
        assert len(response.items) == 0
        assert response.total_found == 0
        assert response.filtered_count == 0
    
    def test_format_single_item(self):
        """Test formatting single item."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Single item",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.85,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert "Single item" in response.formatted_context
        assert len(response.items) == 1
    
    def test_format_multiple_items(self):
        """Test formatting multiple items."""
        formatter = ContextFormatter()
        items = [
            ContextItem(
                content=f"Item {i}",
                source="memory",
                project="test",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime.now()
            )
            for i in range(3)
        ]
        
        response = formatter.format(items, "test")
        
        assert "Item 0" in response.formatted_context
        assert "Item 1" in response.formatted_context
        assert "Item 2" in response.formatted_context
        assert "Found 3 relevant item(s)" in response.formatted_context


class TestAntiHallucinationRules:
    """Tests for anti-hallucination rules (CRITICAL feature)."""
    
    def test_rules_included_by_default(self):
        """Test that 5 critical rules are included by default."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert "CRITICAL RULES FOR USING THIS CONTEXT:" in response.formatted_context
        assert "1. ONLY cite information that appears" in response.formatted_context
        assert "2. If context is from a different project" in response.formatted_context
        assert "3. Include source citations" in response.formatted_context
        assert "4. If unsure or context missing" in response.formatted_context
        assert "5. NEVER mix information from different projects" in response.formatted_context
    
    def test_rules_can_be_disabled(self):
        """Test that rules can be disabled for compact mode."""
        formatter = ContextFormatter(include_anti_hallucination_rules=False)
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert "CRITICAL RULES" not in response.formatted_context
    
    def test_rules_mention_citations(self):
        """Test that rules explicitly mention citation format."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert "[memory:project:date]" in response.formatted_context
        assert "[code:file:line]" in response.formatted_context


class TestMetadataFormatting:
    """Tests for metadata inclusion."""
    
    def test_metadata_included_by_default(self):
        """Test that metadata is included by default."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="TestProject",
            metadata={},
            relevance_score=0.95,
            timestamp=datetime(2026, 5, 30)
        )
        
        response = formatter.format([item], "test")
        
        assert "Source: memory" in response.formatted_context
        assert "Project: TestProject" in response.formatted_context
        assert "Relevance: 0.95" in response.formatted_context
        assert "Date: 2026-05-30" in response.formatted_context
    
    def test_metadata_can_be_disabled(self):
        """Test that metadata can be disabled."""
        formatter = ContextFormatter(include_metadata=False)
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert "Source:" not in response.formatted_context
        assert "Project:" not in response.formatted_context
        assert "Relevance:" not in response.formatted_context
    
    def test_optional_file_metadata(self):
        """Test that file path is included when present."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Code snippet",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="parser.py"
        )
        
        response = formatter.format([item], "test")
        
        assert "File: parser.py" in response.formatted_context
    
    def test_optional_line_range_metadata(self):
        """Test that line range is included when present."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Code snippet",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="parser.py",
            line_range=(10, 25)
        )
        
        response = formatter.format([item], "test")
        
        assert "Lines: 10-25" in response.formatted_context


class TestCitationGeneration:
    """Tests for citation inclusion."""
    
    def test_citations_included_by_default(self):
        """Test that citations are included by default."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="TestProject",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2026, 5, 30)
        )
        
        response = formatter.format([item], "test")
        
        assert "Citation: [memory:TestProject:2026-05-30]" in response.formatted_context
    
    def test_citations_can_be_disabled(self):
        """Test that citations can be disabled."""
        formatter = ContextFormatter(include_citations=False)
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert "Citation:" not in response.formatted_context
    
    def test_code_citation_with_file(self):
        """Test code citation includes file and lines."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Code",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="parser.py",
            line_range=(10, 25)
        )
        
        response = formatter.format([item], "test")
        
        assert "[code:parser.py:10-25]" in response.formatted_context


class TestCrossProjectWarnings:
    """Tests for cross-project warning detection."""
    
    def test_no_warning_single_project(self):
        """Test no warning when all items from current project."""
        formatter = ContextFormatter()
        items = [
            ContextItem(
                content=f"Item {i}",
                source="memory",
                project="current",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime.now()
            )
            for i in range(3)
        ]
        
        response = formatter.format(items, "current")
        
        assert "WARNING" not in response.formatted_context
        assert response.cross_project_warning is None
    
    def test_warning_with_cross_project(self):
        """Test warning appears when items from different project."""
        formatter = ContextFormatter()
        items = [
            ContextItem(
                content="Item 1",
                source="memory",
                project="current",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime.now()
            ),
            ContextItem(
                content="Item 2",
                source="memory",
                project="other",
                metadata={},
                relevance_score=0.85,
                timestamp=datetime.now()
            )
        ]
        
        response = formatter.format(items, "current")
        
        assert "⚠️  WARNING:" in response.formatted_context
        assert "other" in response.formatted_context
        assert response.cross_project_warning is not None
    
    def test_warning_lists_all_cross_projects(self):
        """Test warning lists all cross-project sources."""
        warning = ContextFormatter.check_cross_project([
            ContextItem("", "memory", "proj-a", {}, 0.9, datetime.now()),
            ContextItem("", "memory", "proj-b", {}, 0.9, datetime.now()),
            ContextItem("", "memory", "proj-c", {}, 0.9, datetime.now()),
        ], "current")
        
        assert warning is not None
        assert "proj-a" in warning
        assert "proj-b" in warning
        assert "proj-c" in warning
    
    def test_warning_sorted_alphabetically(self):
        """Test cross-projects are sorted alphabetically."""
        warning = ContextFormatter.check_cross_project([
            ContextItem("", "memory", "zebra", {}, 0.9, datetime.now()),
            ContextItem("", "memory", "alpha", {}, 0.9, datetime.now()),
        ], "current")
        
        # Should be "alpha, zebra" not "zebra, alpha"
        assert warning is not None
        assert warning.index("alpha") < warning.index("zebra")
    
    def test_warning_includes_instructions(self):
        """Test warning includes clear instructions."""
        warning = ContextFormatter.check_cross_project([
            ContextItem("", "memory", "other", {}, 0.9, datetime.now()),
        ], "current")
        
        assert warning is not None
        assert "DO NOT confuse information between projects" in warning


class TestCompactFormat:
    """Tests for compact formatting mode."""
    
    def test_compact_format_structure(self):
        """Test compact format has minimal structure."""
        formatter = ContextFormatter()
        items = [
            ContextItem(
                content="Item 1",
                source="memory",
                project="test",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime(2026, 5, 30)
            ),
            ContextItem(
                content="Item 2",
                source="memory",
                project="test",
                metadata={},
                relevance_score=0.85,
                timestamp=datetime(2026, 5, 30)
            )
        ]
        
        compact = formatter.format_compact(items)
        
        assert "=== BEGIN CONTEXT ===" in compact
        assert "=== END CONTEXT ===" in compact
        assert "[1]" in compact
        assert "[2]" in compact
    
    def test_compact_no_metadata(self):
        """Test compact format excludes metadata."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        compact = formatter.format_compact([item])
        
        assert "Source:" not in compact
        assert "Project:" not in compact
        assert "Relevance:" not in compact
    
    def test_compact_no_rules(self):
        """Test compact format excludes anti-hallucination rules."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        compact = formatter.format_compact([item])
        
        assert "CRITICAL RULES" not in compact
    
    def test_compact_includes_citations(self):
        """Test compact format includes citations."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2026, 5, 30)
        )
        
        compact = formatter.format_compact([item])
        
        assert "[memory:test:2026-05-30]" in compact
    
    def test_compact_empty_items(self):
        """Test compact format with empty list."""
        formatter = ContextFormatter()
        compact = formatter.format_compact([])
        
        assert compact == ""


class TestFormatSingle:
    """Tests for formatting single items."""
    
    def test_format_single_without_delimiters(self):
        """Test single item without delimiters."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test content",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        formatted = formatter.format_single(item, include_delimiters=False)
        
        assert "Test content" in formatted
        assert "=== BEGIN" not in formatted
        assert "=== END" not in formatted
    
    def test_format_single_with_delimiters(self):
        """Test single item with delimiters."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test content",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        formatted = formatter.format_single(item, include_delimiters=True)
        
        assert formatted.startswith("=== BEGIN CONTEXT ===")
        assert formatted.endswith("=== END CONTEXT ===")
        assert "Test content" in formatted
    
    def test_format_single_respects_metadata_setting(self):
        """Test format_single respects include_metadata setting."""
        formatter_with = ContextFormatter(include_metadata=True)
        formatter_without = ContextFormatter(include_metadata=False)
        
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        with_metadata = formatter_with.format_single(item)
        without_metadata = formatter_without.format_single(item)
        
        assert "Source:" in with_metadata
        assert "Source:" not in without_metadata


class TestConvenienceFunction:
    """Tests for format_context convenience function."""
    
    def test_format_context_basic(self):
        """Test format_context convenience function."""
        items = [
            ContextItem(
                content="Test",
                source="memory",
                project="test",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime.now()
            )
        ]
        
        response = format_context(items, "test")
        
        assert isinstance(response.formatted_context, str)
        assert len(response.items) == 1
    
    def test_format_context_detects_cross_project(self):
        """Test format_context auto-detects cross-project."""
        items = [
            ContextItem("", "memory", "other", {}, 0.9, datetime.now())
        ]
        
        response = format_context(items, "current")
        
        assert response.cross_project_warning is not None
        assert "WARNING" in response.formatted_context


class TestNumbering:
    """Tests for item numbering."""
    
    def test_items_are_numbered(self):
        """Test that items are numbered sequentially."""
        formatter = ContextFormatter()
        items = [
            ContextItem(f"Item {i}", "memory", "test", {}, 0.9, datetime.now())
            for i in range(5)
        ]
        
        response = formatter.format(items, "test")
        
        assert "--- Context Item 1/5 ---" in response.formatted_context
        assert "--- Context Item 2/5 ---" in response.formatted_context
        assert "--- Context Item 5/5 ---" in response.formatted_context
    
    def test_summary_shows_count(self):
        """Test that summary shows item count."""
        formatter = ContextFormatter()
        items = [
            ContextItem(f"Item {i}", "memory", "test", {}, 0.9, datetime.now())
            for i in range(3)
        ]
        
        response = formatter.format(items, "test")
        
        assert "Found 3 relevant item(s)" in response.formatted_context


class TestContentHandling:
    """Tests for content handling edge cases."""
    
    def test_content_whitespace_stripped(self):
        """Test that leading/trailing whitespace is stripped."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="  \n  Test content  \n  ",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        # Content should be stripped
        assert "Test content\n\n===" in response.formatted_context or "Test content\n===" in response.formatted_context
    
    def test_long_content_preserved(self):
        """Test that very long content is not truncated."""
        formatter = ContextFormatter()
        long_content = "A" * 10000
        item = ContextItem(
            content=long_content,
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert long_content in response.formatted_context
    
    def test_special_characters_preserved(self):
        """Test that special characters are preserved."""
        formatter = ContextFormatter()
        special = "Code: `function test() { return 'hello'; }`"
        item = ContextItem(
            content=special,
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        
        assert special in response.formatted_context
