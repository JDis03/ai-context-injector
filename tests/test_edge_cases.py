"""Advanced edge case tests to prevent future bugs.

These tests cover scenarios that might not be obvious but could cause
production issues if not handled correctly.
"""

import pytest
from datetime import datetime
from ai_context_injector.core import (
    ContextItem,
    ContextRequest,
    ContextResponse,
    ParsedTag,
    TagParser,
    ContextFormatter,
)


class TestUnicodeAndEncoding:
    """Test Unicode and encoding edge cases."""
    
    def test_unicode_in_query(self):
        """Test Unicode characters in query."""
        parser = TagParser()
        tags = parser.parse("@memory búsqueda con ñ y acentós")
        
        assert len(tags) == 1
        assert "búsqueda" in tags[0].query
        assert "ñ" in tags[0].query
    
    def test_emoji_in_query(self):
        """Test emoji in query."""
        parser = TagParser()
        tags = parser.parse("@memory keyboard layout 🎹 emoji 😀")
        
        assert len(tags) == 1
        assert "🎹" in tags[0].query
        assert "😀" in tags[0].query
    
    def test_unicode_in_content(self):
        """Test Unicode in context content."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Decisión: Usar SQLite con configuración específica ñ",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        assert "ñ" in response.formatted_context
    
    def test_mixed_scripts(self):
        """Test mixed scripts (Latin, Cyrillic, etc)."""
        parser = TagParser()
        tags = parser.parse("@memory Hello Привет 你好")
        
        assert len(tags) == 1
        assert "Привет" in tags[0].query
        assert "你好" in tags[0].query


class TestVeryLongInputs:
    """Test handling of very long inputs."""
    
    def test_very_long_query(self):
        """Test query with 10000+ characters."""
        parser = TagParser()
        long_query = "a" * 10000
        tags = parser.parse(f"@memory {long_query}")
        
        assert len(tags) == 1
        assert len(tags[0].query) == 10000
    
    def test_very_long_content(self):
        """Test formatting very long content (100KB+)."""
        formatter = ContextFormatter()
        huge_content = "X" * 100000
        item = ContextItem(
            content=huge_content,
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        assert huge_content in response.formatted_context
    
    def test_many_items(self):
        """Test formatting 1000+ items."""
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
            for i in range(1000)
        ]
        
        response = formatter.format(items, "test")
        assert "Found 1000 relevant item(s)" in response.formatted_context


class TestSpecialCharactersInPaths:
    """Test special characters that might break parsing."""
    
    def test_spaces_in_project_name(self):
        """Test project names with spaces."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Test",
            source="memory",
            project="My Project Name",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "My Project Name")
        assert "My Project Name" in response.formatted_context
    
    def test_special_chars_in_file_path(self):
        """Test file paths with special characters."""
        item = ContextItem(
            content="Test",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="src/my-file (copy).py"
        )
        
        citation = item.citation()
        assert "my-file (copy).py" in citation
    
    def test_backslashes_in_path(self):
        """Test Windows-style paths with backslashes."""
        item = ContextItem(
            content="Test",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="C:\\Users\\test\\file.py"
        )
        
        citation = item.citation()
        assert "C:\\Users\\test\\file.py" in citation


class TestMalformedInput:
    """Test handling of malformed/unexpected input."""
    
    def test_tag_without_space(self):
        """Test tag without space before query."""
        parser = TagParser()
        tags = parser.parse("@memoryquery")  # No space!
        
        # Should not match because pattern requires space
        assert len(tags) == 0
    
    def test_multiple_colons_in_tag(self):
        """Test tag with multiple colons."""
        parser = TagParser()
        tags = parser.parse("@memory:all:recent query")
        
        # Should NOT match - malformed (no space after modifier)
        # This is correct behavior to reject invalid input
        assert len(tags) == 0
    
    def test_tag_at_end_without_query(self):
        """Test tag at end of text without query."""
        parser = TagParser()
        tags = parser.parse("Some text @memory")
        
        # Should not match - no query after tag
        assert len(tags) == 0
    
    def test_nested_delimiters_in_content(self):
        """Test content that contains delimiter strings."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="Code example:\n=== BEGIN CONTEXT ===\nSome code\n=== END CONTEXT ===",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        # Should still work, just with nested delimiters
        assert response.formatted_context.count("=== BEGIN CONTEXT ===") == 2


class TestBoundaryConditions:
    """Test boundary conditions and limits."""
    
    def test_zero_relevance_score(self):
        """Test item with 0.0 relevance score."""
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.0,
            timestamp=datetime.now()
        )
        
        assert item.relevance_score == 0.0
        citation = item.citation()
        assert citation  # Should still generate citation
    
    def test_max_relevance_score(self):
        """Test item with 1.0 relevance score."""
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=1.0,
            timestamp=datetime.now()
        )
        
        assert item.relevance_score == 1.0
    
    def test_empty_string_content(self):
        """Test item with empty string content."""
        formatter = ContextFormatter()
        item = ContextItem(
            content="",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        response = formatter.format([item], "test")
        # Should handle gracefully
        assert "=== BEGIN CONTEXT ===" in response.formatted_context
    
    def test_very_old_timestamp(self):
        """Test item with very old timestamp."""
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(1900, 1, 1)
        )
        
        citation = item.citation()
        assert "1900-01-01" in citation
    
    def test_future_timestamp(self):
        """Test item with future timestamp."""
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime(2099, 12, 31)
        )
        
        citation = item.citation()
        assert "2099-12-31" in citation


class TestConcurrencyScenarios:
    """Test scenarios that might cause issues in concurrent usage."""
    
    def test_parser_is_stateless(self):
        """Test that parser can be safely reused."""
        parser = TagParser()
        
        # Parse multiple different inputs
        tags1 = parser.parse("@memory query 1")
        tags2 = parser.parse("@code query 2")
        tags3 = parser.parse("@session query 3")
        
        # Should not interfere with each other
        assert tags1[0].tag == "@memory"
        assert tags2[0].tag == "@code"
        assert tags3[0].tag == "@session"
    
    def test_formatter_is_stateless(self):
        """Test that formatter can be safely reused."""
        formatter = ContextFormatter()
        
        item1 = ContextItem("Content 1", "memory", "proj1", {}, 0.9, datetime.now())
        item2 = ContextItem("Content 2", "code", "proj2", {}, 0.8, datetime.now())
        
        response1 = formatter.format([item1], "proj1")
        response2 = formatter.format([item2], "proj2")
        
        # Should be independent
        assert "Content 1" in response1.formatted_context
        assert "Content 2" in response2.formatted_context
        assert "Content 1" not in response2.formatted_context


class TestMetadataEdgeCases:
    """Test edge cases in metadata handling."""
    
    def test_empty_metadata_dict(self):
        """Test item with empty metadata."""
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        # Should work fine with empty dict
        assert item.metadata == {}
    
    def test_large_metadata_dict(self):
        """Test item with very large metadata."""
        huge_metadata = {f"key_{i}": f"value_{i}" for i in range(1000)}
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata=huge_metadata,
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        assert len(item.metadata) == 1000
    
    def test_metadata_with_special_values(self):
        """Test metadata with None, empty strings, etc."""
        item = ContextItem(
            content="Test",
            source="memory",
            project="test",
            metadata={
                "null_value": None,
                "empty_string": "",
                "zero": 0,
                "false": False,
                "list": [1, 2, 3],
                "nested": {"a": "b"}
            },
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        assert item.metadata["null_value"] is None
        assert item.metadata["empty_string"] == ""


class TestLineRangeEdgeCases:
    """Test line range edge cases."""
    
    def test_single_line_range(self):
        """Test line range where start == end."""
        item = ContextItem(
            content="Test",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="test.py",
            line_range=(42, 42)
        )
        
        citation = item.citation()
        assert "42-42" in citation
    
    def test_zero_line_number(self):
        """Test line range starting at 0."""
        item = ContextItem(
            content="Test",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="test.py",
            line_range=(0, 10)
        )
        
        citation = item.citation()
        assert "0-10" in citation
    
    def test_very_large_line_numbers(self):
        """Test very large line numbers."""
        item = ContextItem(
            content="Test",
            source="code",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now(),
            file_path="huge.py",
            line_range=(999999, 1000000)
        )
        
        citation = item.citation()
        assert "999999-1000000" in citation


class TestCrossProjectWarningEdgeCases:
    """Test cross-project warning edge cases."""
    
    def test_warning_with_same_project_name_different_case(self):
        """Test if case-sensitive project comparison works."""
        items = [
            ContextItem("", "memory", "Project", {}, 0.9, datetime.now()),
            ContextItem("", "memory", "project", {}, 0.9, datetime.now()),
        ]
        
        warning = ContextFormatter.check_cross_project(items, "Project")
        
        # "project" (lowercase) should be detected as different
        assert warning is not None
        assert "project" in warning
    
    def test_warning_with_many_projects(self):
        """Test warning with 100+ different projects."""
        items = [
            ContextItem("", "memory", f"project-{i}", {}, 0.9, datetime.now())
            for i in range(100)
        ]
        
        warning = ContextFormatter.check_cross_project(items, "current")
        
        assert warning is not None
        # Should list all projects
        assert "project-0" in warning
        assert "project-99" in warning


class TestNormalizationEdgeCases:
    """Test query normalization edge cases."""
    
    def test_normalize_only_punctuation(self):
        """Test normalizing string of only punctuation."""
        result = TagParser.normalize_query("...")
        assert result == ""
    
    def test_normalize_only_whitespace(self):
        """Test normalizing string of only whitespace."""
        result = TagParser.normalize_query("   \n\t   ")
        assert result == ""
    
    def test_normalize_mixed_whitespace(self):
        """Test normalizing with tabs, newlines, etc."""
        result = TagParser.normalize_query("query\t\twith\nmixed\r\nspaces")
        assert "\t" not in result
        assert "\n" not in result
        assert "\r" not in result


class TestFilterRatioCalculation:
    """Test ContextResponse filter_ratio calculation."""
    
    def test_filter_ratio_zero_total(self):
        """Test filter_ratio when total_found is 0."""
        response = ContextResponse(
            formatted_context="",
            items=[],
            total_found=0,
            filtered_count=0
        )
        
        assert response.filter_ratio == 0.0
    
    def test_filter_ratio_all_filtered(self):
        """Test filter_ratio when everything filtered out."""
        response = ContextResponse(
            formatted_context="",
            items=[],
            total_found=100,
            filtered_count=0
        )
        
        assert response.filter_ratio == 0.0
    
    def test_filter_ratio_none_filtered(self):
        """Test filter_ratio when nothing filtered."""
        response = ContextResponse(
            formatted_context="",
            items=[],
            total_found=50,
            filtered_count=50
        )
        
        assert response.filter_ratio == 1.0
    
    def test_filter_ratio_fractional(self):
        """Test filter_ratio with fractional result."""
        response = ContextResponse(
            formatted_context="",
            items=[],
            total_found=3,
            filtered_count=2
        )
        
        # 2/3 = 0.666...
        assert 0.666 <= response.filter_ratio <= 0.667


class TestCustomTagRegistration:
    """Test custom tag registration edge cases."""
    
    def test_register_tag_with_special_chars(self):
        """Test registering tag with special characters."""
        parser = TagParser()
        # Should handle tags with hyphens, underscores
        parser.register_tag("@my-custom_tag")
        
        tags = parser.parse("@my-custom_tag query")
        assert len(tags) == 1
    
    def test_register_duplicate_tag(self):
        """Test registering same tag twice."""
        parser = TagParser()
        parser.register_tag("@custom")
        parser.register_tag("@custom")  # Register again
        
        # Should not cause error
        tags = parser.parse("@custom query")
        assert len(tags) == 1
    
    def test_register_tag_conflicts_with_builtin(self):
        """Test registering tag that conflicts with built-in."""
        parser = TagParser()
        parser.register_tag("@memory")  # Already exists
        
        # Should still work (re-registration)
        tags = parser.parse("@memory query")
        assert len(tags) == 1


class TestReprMethods:
    """Test __repr__ methods don't crash."""
    
    def test_context_item_repr_with_special_chars(self):
        """Test ContextItem repr with special characters."""
        item = ContextItem(
            content="Content with 'quotes' and \"double quotes\" and \n newlines",
            source="memory",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        repr_str = repr(item)
        assert "ContextItem" in repr_str
    
    def test_parsed_tag_repr_with_unicode(self):
        """Test ParsedTag repr with Unicode."""
        tag = ParsedTag(
            tag="@memory",
            modifier=None,
            query="búsqueda con ñ",
            full_match="@memory búsqueda con ñ",
            start_pos=0,
            end_pos=20
        )
        
        repr_str = repr(tag)
        assert "ParsedTag" in repr_str
