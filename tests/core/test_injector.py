"""Tests for ContextInjector orchestrator."""

import pytest
from datetime import datetime
from ai_context_injector.core.types import ContextItem, ContextRequest
from ai_context_injector.core.injector import ContextInjector, inject_context
from ai_context_injector.providers.base import IContextProvider


class MockProvider(IContextProvider):
    """Mock provider for testing."""
    
    def __init__(self, items=None, available=True):
        self.items = items or []
        self.available = available
        self.last_request = None
    
    @property
    def name(self) -> str:
        return "MockProvider"
    
    @property
    def source_type(self) -> str:
        return "mock"
    
    def is_available(self) -> bool:
        return self.available
    
    def retrieve(self, request: ContextRequest):
        self.last_request = request
        return self.items


class TestContextInjectorBasics:
    """Test basic injector functionality."""
    
    def test_init_with_project(self):
        """Test initialization with explicit project."""
        injector = ContextInjector(current_project="test-project")
        assert injector.current_project == "test-project"
    
    def test_init_auto_detect_project(self):
        """Test auto-detection of project from cwd."""
        injector = ContextInjector()
        assert injector.current_project  # Should detect from cwd
        assert isinstance(injector.current_project, str)
    
    def test_providers_empty_by_default(self):
        """Test providers dict is empty by default."""
        injector = ContextInjector()
        assert injector.providers == {}
    
    def test_parser_created_by_default(self):
        """Test parser is created if not provided."""
        injector = ContextInjector()
        assert injector.parser is not None
    
    def test_formatter_created_by_default(self):
        """Test formatter is created if not provided."""
        injector = ContextInjector()
        assert injector.formatter is not None


class TestProviderRegistration:
    """Test provider registration."""
    
    def test_register_provider(self):
        """Test registering a provider."""
        injector = ContextInjector()
        provider = MockProvider()
        
        injector.register_provider("@memory", provider)
        
        assert "@memory" in injector.providers
        assert injector.providers["@memory"] == provider
    
    def test_register_provider_without_at_symbol(self):
        """Test registering provider without @ symbol."""
        injector = ContextInjector()
        provider = MockProvider()
        
        injector.register_provider("memory", provider)
        
        assert "@memory" in injector.providers
    
    def test_register_provider_auto_registers_tag(self):
        """Test provider registration auto-registers tag in parser."""
        injector = ContextInjector()
        provider = MockProvider()
        
        injector.register_provider("@custom", provider)
        
        assert "@custom" in injector.parser.valid_tags
    
    def test_register_multiple_providers(self):
        """Test registering multiple providers."""
        injector = ContextInjector()
        
        injector.register_provider("@memory", MockProvider())
        injector.register_provider("@code", MockProvider())
        
        assert len(injector.providers) == 2


class TestBasicInjection:
    """Test basic context injection."""
    
    def test_inject_with_no_tags(self):
        """Test inject returns None when no tags found."""
        injector = ContextInjector()
        result = injector.inject("plain text without tags")
        
        assert result is None
    
    def test_inject_with_tag_but_no_provider(self):
        """Test inject returns None when tag has no provider."""
        injector = ContextInjector()
        result = injector.inject("@memory query")
        
        assert result is None
    
    def test_inject_with_unavailable_provider(self):
        """Test inject returns None when provider unavailable."""
        injector = ContextInjector()
        injector.register_provider("@memory", MockProvider(available=False))
        
        result = injector.inject("@memory query")
        
        assert result is None
    
    def test_inject_with_single_tag(self):
        """Test inject with single tag."""
        items = [
            ContextItem(
                content="Test content",
                source="memory",
                project="test",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime.now()
            )
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        result = injector.inject("@memory query")
        
        assert result is not None
        assert "Test content" in result
        assert "=== BEGIN CONTEXT ===" in result
    
    def test_inject_passes_correct_request(self):
        """Test inject passes correct request to provider."""
        provider = MockProvider()
        injector = ContextInjector(current_project="my-project")
        injector.register_provider("@memory", provider)
        
        injector.inject("@memory test query", max_items=5, min_relevance=0.8)
        
        assert provider.last_request is not None
        assert provider.last_request.tag == "@memory"
        assert provider.last_request.query == "test query"
        assert provider.last_request.project == "my-project"
        assert provider.last_request.max_items == 5
        assert provider.last_request.min_relevance == 0.8


class TestMultipleTags:
    """Test handling multiple tags."""
    
    def test_inject_with_multiple_tags(self):
        """Test inject aggregates results from multiple tags."""
        items1 = [
            ContextItem("Memory content", "memory", "test", {}, 0.9, datetime.now())
        ]
        items2 = [
            ContextItem("Code content", "code", "test", {}, 0.8, datetime.now())
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items1))
        injector.register_provider("@code", MockProvider(items=items2))
        
        result = injector.inject("@memory q1 and @code q2")
        
        assert result is not None
        assert "Memory content" in result
        assert "Code content" in result
    
    def test_inject_with_same_tag_multiple_times(self):
        """Test inject handles same tag appearing multiple times."""
        items = [
            ContextItem("Content 1", "memory", "test", {}, 0.9, datetime.now()),
            ContextItem("Content 2", "memory", "test", {}, 0.8, datetime.now())
        ]
        
        provider = MockProvider(items=items)
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", provider)
        
        result = injector.inject("@memory q1 and @memory q2")
        
        assert result is not None
        # Should have called provider twice
        assert "Content" in result


class TestDeduplication:
    """Test deduplication logic."""
    
    def test_deduplicate_identical_content(self):
        """Test deduplication removes identical content."""
        items = [
            ContextItem("Same content here", "memory", "test", {}, 0.9, datetime.now()),
            ContextItem("Same content here", "memory", "test", {}, 0.8, datetime.now()),
            ContextItem("Different content", "memory", "test", {}, 0.7, datetime.now())
        ]
        
        injector = ContextInjector()
        deduplicated = injector._deduplicate_items(items)
        
        assert len(deduplicated) == 2
    
    def test_deduplicate_uses_first_100_chars(self):
        """Test deduplication uses first 100 chars as hash."""
        # Same first 100 chars, different after
        long_text_1 = "A" * 100 + "X"
        long_text_2 = "A" * 100 + "Y"
        
        items = [
            ContextItem(long_text_1, "memory", "test", {}, 0.9, datetime.now()),
            ContextItem(long_text_2, "memory", "test", {}, 0.8, datetime.now())
        ]
        
        injector = ContextInjector()
        deduplicated = injector._deduplicate_items(items)
        
        # Should be treated as duplicates
        assert len(deduplicated) == 1


class TestSortingAndLimiting:
    """Test sorting and limiting items."""
    
    def test_items_sorted_by_relevance(self):
        """Test items are sorted by relevance score."""
        items = [
            ContextItem("Low", "memory", "test", {}, 0.5, datetime.now()),
            ContextItem("High", "memory", "test", {}, 0.9, datetime.now()),
            ContextItem("Medium", "memory", "test", {}, 0.7, datetime.now())
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        result = injector.inject("@memory query")
        
        assert result is not None
        # Should have High first (0.9), then Medium (0.7), then Low (0.5)
        assert result.index("High") < result.index("Medium")
        assert result.index("Medium") < result.index("Low")
    
    def test_max_items_limit(self):
        """Test max_items limits total results."""
        items = [
            ContextItem(f"Content {i}", "memory", "test", {}, 0.9, datetime.now())
            for i in range(20)
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        result = injector.inject("@memory query", max_items=5)
        
        assert result is not None
        # Should only have 5 items
        assert result.count("--- Context Item") == 5


class TestCrossProjectHandling:
    """Test cross-project detection and warnings."""
    
    def test_cross_project_warning_generated(self):
        """Test cross-project warning is generated."""
        items = [
            ContextItem("Content", "memory", "other-project", {}, 0.9, datetime.now())
        ]
        
        injector = ContextInjector(current_project="my-project")
        injector.register_provider("@memory", MockProvider(items=items))
        
        result = injector.inject("@memory query")
        
        assert result is not None
        assert "WARNING" in result or "other-project" in result
    
    def test_modifier_all_sets_cross_project_flag(self):
        """Test :all modifier sets include_cross_project flag."""
        provider = MockProvider()
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", provider)
        
        injector.inject("@memory:all query")
        
        assert provider.last_request is not None
        assert provider.last_request.include_cross_project is True


class TestInjectWithMetrics:
    """Test inject_with_metrics method."""
    
    def test_inject_with_metrics_returns_response(self):
        """Test inject_with_metrics returns ContextResponse."""
        items = [
            ContextItem("Content", "memory", "test", {}, 0.9, datetime.now())
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        response = injector.inject_with_metrics("@memory query")
        
        assert response.formatted_context
        assert len(response.items) == 1
        assert response.total_found >= 1
        assert response.filtered_count == 1
    
    def test_inject_with_metrics_calculates_performance(self):
        """Test performance_ms is calculated."""
        items = [
            ContextItem("Content", "memory", "test", {}, 0.9, datetime.now())
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        response = injector.inject_with_metrics("@memory query")
        
        assert response.performance_ms is not None
        assert response.performance_ms >= 0
    
    def test_inject_with_metrics_no_tags(self):
        """Test inject_with_metrics with no tags."""
        injector = ContextInjector()
        response = injector.inject_with_metrics("plain text")
        
        assert response.formatted_context == ""
        assert len(response.items) == 0
        assert response.total_found == 0
    
    def test_inject_with_metrics_tracks_total_vs_filtered(self):
        """Test total_found vs filtered_count tracking."""
        items = [
            ContextItem(f"Item {i}", "memory", "test", {}, 0.9, datetime.now())
            for i in range(20)
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        response = injector.inject_with_metrics("@memory query", max_items=5)
        
        assert response.total_found == 20
        assert response.filtered_count == 5
        assert response.filter_ratio == 5 / 20


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_has_tags_true(self):
        """Test has_tags returns True when tags present."""
        injector = ContextInjector()
        injector.register_provider("@memory", MockProvider())
        
        assert injector.has_tags("@memory query") is True
    
    def test_has_tags_false(self):
        """Test has_tags returns False when no tags."""
        injector = ContextInjector()
        
        assert injector.has_tags("plain text") is False
    
    def test_extract_query_only(self):
        """Test extract_query_only removes tags."""
        injector = ContextInjector()
        
        result = injector.extract_query_only("Tell me @memory query about this")
        
        assert "@memory" not in result
        assert "Tell me" in result


class TestConvenienceFunction:
    """Test inject_context convenience function."""
    
    def test_inject_context_function(self):
        """Test inject_context convenience function."""
        items = [
            ContextItem("Content", "memory", "test", {}, 0.9, datetime.now())
        ]
        
        providers = {
            "@memory": MockProvider(items=items)
        }
        
        result = inject_context("@memory query", providers, project="test")
        
        assert result is not None
        assert "Content" in result
    
    def test_inject_context_with_kwargs(self):
        """Test inject_context passes kwargs."""
        providers = {
            "@memory": MockProvider()
        }
        
        result = inject_context(
            "@memory query",
            providers,
            project="test",
            max_items=3,
            min_relevance=0.9
        )
        
        # Should not crash with kwargs
        assert result is None  # No items


class TestEdgeCases:
    """Test edge cases in injection."""
    
    def test_inject_with_empty_items_from_provider(self):
        """Test inject handles empty results from provider."""
        injector = ContextInjector()
        injector.register_provider("@memory", MockProvider(items=[]))
        
        result = injector.inject("@memory query")
        
        assert result is None
    
    def test_inject_preserves_item_order_within_same_relevance(self):
        """Test items with same relevance preserve order."""
        items = [
            ContextItem("First", "memory", "test", {}, 0.9, datetime.now()),
            ContextItem("Second", "memory", "test", {}, 0.9, datetime.now()),
            ContextItem("Third", "memory", "test", {}, 0.9, datetime.now())
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        result = injector.inject("@memory query")
        
        assert result is not None
        # Order should be preserved
        assert result.index("First") < result.index("Second")
        assert result.index("Second") < result.index("Third")
    
    def test_inject_with_very_long_content(self):
        """Test inject handles very long content."""
        huge_content = "X" * 100000
        items = [
            ContextItem(huge_content, "memory", "test", {}, 0.9, datetime.now())
        ]
        
        injector = ContextInjector(current_project="test")
        injector.register_provider("@memory", MockProvider(items=items))
        
        result = injector.inject("@memory query")
        
        assert result is not None
        assert huge_content in result
