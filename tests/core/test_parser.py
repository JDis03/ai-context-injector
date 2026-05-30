"""Tests for tag parser."""

import pytest
from ai_context_injector.core import TagParser, parse_tags


class TestTagParserBasic:
    """Tests for basic tag parsing functionality."""
    
    def test_parse_memory_tag(self):
        """Test parsing basic @memory tag."""
        parser = TagParser()
        tags = parser.parse("@memory dark keyboard layout")
        
        assert len(tags) == 1
        assert tags[0].tag == "@memory"
        assert tags[0].query == "dark keyboard layout"
        assert tags[0].modifier is None
    
    def test_parse_code_tag(self):
        """Test parsing @code tag."""
        parser = TagParser()
        tags = parser.parse("@code ContextItem class")
        
        assert len(tags) == 1
        assert tags[0].tag == "@code"
        assert tags[0].query == "ContextItem class"
    
    def test_parse_session_tag(self):
        """Test parsing @session tag."""
        parser = TagParser()
        tags = parser.parse("@session what did we implement")
        
        assert len(tags) == 1
        assert tags[0].tag == "@session"
        assert tags[0].query == "what did we implement"
    
    def test_case_insensitive(self):
        """Test that tags are case insensitive."""
        parser = TagParser()
        tags = parser.parse("@MEMORY query text")
        
        assert len(tags) == 1
        assert tags[0].tag == "@memory"
        assert tags[0].query == "query text"
    
    def test_multiple_tags(self):
        """Test parsing multiple tags in one input."""
        parser = TagParser()
        tags = parser.parse("@memory first query and @code second query")
        
        assert len(tags) == 2
        assert tags[0].tag == "@memory"
        assert tags[0].query == "first query and"
        assert tags[1].tag == "@code"
        assert tags[1].query == "second query"
    
    def test_no_tags(self):
        """Test input with no tags returns empty list."""
        parser = TagParser()
        tags = parser.parse("This is plain text without tags")
        
        assert len(tags) == 0
    
    def test_invalid_tag(self):
        """Test that invalid tags are not parsed."""
        parser = TagParser()
        tags = parser.parse("@invalid query")
        
        assert len(tags) == 0


class TestTagParserModifiers:
    """Tests for tag modifier parsing."""
    
    def test_modifier_all(self):
        """Test parsing :all modifier."""
        parser = TagParser()
        tags = parser.parse("@memory:all emoji implementation")
        
        assert len(tags) == 1
        assert tags[0].tag == "@memory"
        assert tags[0].modifier == "all"
        assert tags[0].query == "emoji implementation"
    
    def test_modifier_recent(self):
        """Test parsing :recent modifier."""
        parser = TagParser()
        tags = parser.parse("@session:recent last hour")
        
        assert len(tags) == 1
        assert tags[0].modifier == "recent"
    
    def test_no_modifier(self):
        """Test tag without modifier."""
        parser = TagParser()
        tags = parser.parse("@memory query")
        
        assert len(tags) == 1
        assert tags[0].modifier is None
    
    def test_tag_with_modifier_property(self):
        """Test tag_with_modifier property."""
        parser = TagParser()
        
        tags_without = parser.parse("@memory query")
        assert tags_without[0].tag_with_modifier == "@memory"
        
        tags_with = parser.parse("@memory:all query")
        assert tags_with[0].tag_with_modifier == "@memory:all"


class TestTagParserEmbedded:
    """Tests for tags embedded in natural text."""
    
    def test_tag_at_beginning(self):
        """Test tag at beginning of text."""
        parser = TagParser()
        tags = parser.parse("@memory keyboard layout for mobile")
        
        assert len(tags) == 1
        assert tags[0].tag == "@memory"
    
    def test_tag_in_middle(self):
        """Test tag in middle of text."""
        parser = TagParser()
        tags = parser.parse("Can you check @memory keyboard and tell me")
        
        assert len(tags) == 1
        assert tags[0].tag == "@memory"
        assert tags[0].query == "keyboard and tell me"
    
    def test_tag_at_end(self):
        """Test tag at end of text."""
        parser = TagParser()
        tags = parser.parse("Please search @memory recent decisions")
        
        assert len(tags) == 1
        assert tags[0].query == "recent decisions"
    
    def test_position_tracking(self):
        """Test that start_pos and end_pos are correct."""
        parser = TagParser()
        text = "Hello @memory test world"
        tags = parser.parse(text)
        
        assert len(tags) == 1
        assert tags[0].start_pos == 6
        assert tags[0].full_match == "@memory test world"


class TestTagParserEdgeCases:
    """Tests for edge cases."""
    
    def test_tag_without_query(self):
        """Test tag without following query text."""
        parser = TagParser()
        tags = parser.parse("@memory")
        
        # Should not match because regex requires query after tag
        assert len(tags) == 0
    
    def test_query_until_newline(self):
        """Test query stops at newline."""
        parser = TagParser()
        tags = parser.parse("@memory query text\nmore text")
        
        assert len(tags) == 1
        assert tags[0].query == "query text"
        assert "more text" not in tags[0].query
    
    def test_query_until_next_tag(self):
        """Test query stops before next tag."""
        parser = TagParser()
        tags = parser.parse("@memory first query @code second query")
        
        assert len(tags) == 2
        assert "@code" not in tags[0].query
    
    def test_trailing_whitespace(self):
        """Test that trailing whitespace is stripped from query."""
        parser = TagParser()
        tags = parser.parse("@memory query text   ")
        
        assert len(tags) == 1
        assert tags[0].query == "query text"
    
    def test_empty_string(self):
        """Test parsing empty string."""
        parser = TagParser()
        tags = parser.parse("")
        
        assert len(tags) == 0
    
    def test_whitespace_only(self):
        """Test parsing whitespace-only string."""
        parser = TagParser()
        tags = parser.parse("   \n\t  ")
        
        assert len(tags) == 0


class TestTagParserUtilities:
    """Tests for utility methods."""
    
    def test_has_tags_true(self):
        """Test has_tags returns True when tags present."""
        parser = TagParser()
        assert parser.has_tags("@memory query") is True
    
    def test_has_tags_false(self):
        """Test has_tags returns False when no tags."""
        parser = TagParser()
        assert parser.has_tags("plain text") is False
    
    def test_remove_tags(self):
        """Test removing tags from text."""
        parser = TagParser()
        result = parser.remove_tags("Tell me @memory query about this")
        
        assert result == "Tell me  about this"
    
    def test_remove_multiple_tags(self):
        """Test removing multiple tags."""
        parser = TagParser()
        result = parser.remove_tags("@memory query1 and @code query2")
        
        assert "@memory" not in result
        assert "@code" not in result
    
    def test_extract_tag_text(self):
        """Test extracting only tag portions."""
        parser = TagParser()
        result = parser.extract_tag_text("Hello @memory query world")
        
        assert result == "@memory query world"
    
    def test_extract_tag_text_multiple(self):
        """Test extracting multiple tags."""
        parser = TagParser()
        result = parser.extract_tag_text("@memory q1 and @code q2")
        
        assert "@memory" in result
        assert "@code" in result
    
    def test_extract_tag_text_no_tags(self):
        """Test extracting from text with no tags."""
        parser = TagParser()
        result = parser.extract_tag_text("plain text")
        
        assert result == ""
    
    def test_validate_tag_valid(self):
        """Test validate_tag with valid tags."""
        parser = TagParser()
        assert parser.validate_tag("@memory") is True
        assert parser.validate_tag("@code") is True
        assert parser.validate_tag("@session") is True
    
    def test_validate_tag_invalid(self):
        """Test validate_tag with invalid tag."""
        parser = TagParser()
        assert parser.validate_tag("@invalid") is False
    
    def test_validate_tag_case_insensitive(self):
        """Test validate_tag is case insensitive."""
        parser = TagParser()
        assert parser.validate_tag("@MEMORY") is True


class TestTagParserNormalization:
    """Tests for query normalization."""
    
    def test_normalize_lowercase(self):
        """Test normalization converts to lowercase."""
        result = TagParser.normalize_query("Dark Keyboard")
        assert result == "dark keyboard"
    
    def test_normalize_whitespace(self):
        """Test normalization removes extra whitespace."""
        result = TagParser.normalize_query("query   with    spaces")
        assert result == "query with spaces"
    
    def test_normalize_punctuation(self):
        """Test normalization strips trailing punctuation."""
        result = TagParser.normalize_query("query text...")
        assert result == "query text"
        
        result = TagParser.normalize_query("query?")
        assert result == "query"
    
    def test_normalize_combined(self):
        """Test normalization with multiple transformations."""
        result = TagParser.normalize_query("Dark   Keyboard!!!")
        assert result == "dark keyboard"


class TestTagParserCustomTags:
    """Tests for custom tag registration."""
    
    def test_register_custom_tag(self):
        """Test registering a custom tag."""
        parser = TagParser()
        parser.register_tag("@docs")
        
        tags = parser.parse("@docs api authentication")
        
        assert len(tags) == 1
        assert tags[0].tag == "@docs"
        assert tags[0].query == "api authentication"
    
    def test_register_tag_without_at(self):
        """Test registering tag without @ symbol."""
        parser = TagParser()
        parser.register_tag("docs")
        
        tags = parser.parse("@docs query")
        
        assert len(tags) == 1
        assert tags[0].tag == "@docs"
    
    def test_custom_tag_with_modifier(self):
        """Test custom tag with modifier."""
        parser = TagParser()
        parser.register_tag("@docs")
        
        tags = parser.parse("@docs:api authentication")
        
        assert len(tags) == 1
        assert tags[0].tag == "@docs"
        assert tags[0].modifier == "api"
    
    def test_init_with_custom_tags(self):
        """Test initializing parser with custom tags."""
        parser = TagParser(custom_tags={"@docs", "@tickets"})
        
        tags = parser.parse("@docs query")
        assert len(tags) == 1
        
        tags = parser.parse("@tickets PROJ-123")
        assert len(tags) == 1
    
    def test_default_tags_still_work(self):
        """Test that default tags still work with custom tags."""
        parser = TagParser(custom_tags={"@docs"})
        
        tags = parser.parse("@memory query")
        assert len(tags) == 1
        assert tags[0].tag == "@memory"


class TestTagParserWithContext:
    """Tests for parse_with_context method."""
    
    def test_parse_with_context_basic(self):
        """Test parsing with surrounding context."""
        parser = TagParser()
        result = parser.parse_with_context("Can you check @memory dark keyboard what we decided?")
        
        assert len(result) == 1
        assert result[0]['tag'] == "@memory"
        assert result[0]['query'] == "dark keyboard what we decided?"
        assert result[0]['before'] == "Can you check"
        assert result[0]['after'] == ""
    
    def test_parse_with_context_multiple(self):
        """Test parse_with_context with multiple tags."""
        parser = TagParser()
        result = parser.parse_with_context("First @memory q1 then @code q2 done")
        
        assert len(result) == 2
        assert result[0]['before'] == "First"
        assert result[0]['after'] == "then @code q2 done"
        assert result[1]['before'] == "First @memory q1 then"
        assert result[1]['after'] == "done"
    
    def test_parse_with_context_modifier(self):
        """Test that modifier is included in result."""
        parser = TagParser()
        result = parser.parse_with_context("@memory:all query")
        
        assert len(result) == 1
        assert result[0]['modifier'] == "all"


class TestConvenienceFunction:
    """Tests for parse_tags convenience function."""
    
    def test_parse_tags_basic(self):
        """Test parse_tags function."""
        tags = parse_tags("@memory dark keyboard")
        
        assert len(tags) == 1
        assert tags[0].tag == "@memory"
        assert tags[0].query == "dark keyboard"
    
    def test_parse_tags_with_custom(self):
        """Test parse_tags with custom tags."""
        tags = parse_tags("@docs api", custom_tags={"@docs"})
        
        assert len(tags) == 1
        assert tags[0].tag == "@docs"
