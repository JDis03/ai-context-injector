"""Tests for IContextProvider base interface."""

import pytest
from datetime import datetime
from typing import List

from ai_context_injector.providers import IContextProvider
from ai_context_injector.core import ContextItem, ContextRequest


class MockProvider(IContextProvider):
    """Mock provider for testing.
    
    Returns predefined items based on configuration.
    """
    
    def __init__(self, items: List[ContextItem] | None = None, available: bool = True):
        """Initialize mock provider.
        
        Args:
            items: Predefined items to return
            available: Whether provider is available
        """
        self._items = items or []
        self._available = available
        self._retrieve_called = False
        self._last_request = None
    
    @property
    def name(self) -> str:
        return "Mock Provider"
    
    @property
    def source_type(self) -> str:
        return "mock"
    
    def is_available(self) -> bool:
        return self._available
    
    def retrieve(self, request: ContextRequest) -> List[ContextItem]:
        self._retrieve_called = True
        self._last_request = request
        
        # Simple filtering by query
        results = []
        for item in self._items:
            if request.query.lower() in item.content.lower():
                results.append(item)
        
        # Filter by relevance
        results = [r for r in results if r.relevance_score >= request.min_relevance]
        
        # Sort by relevance
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit results
        return results[:request.max_items]


class TestIContextProvider:
    """Tests for IContextProvider interface."""
    
    def test_provider_has_required_methods(self):
        """Test that IContextProvider defines required methods."""
        assert hasattr(IContextProvider, 'retrieve')
        assert hasattr(IContextProvider, 'is_available')
        assert hasattr(IContextProvider, 'name')
        assert hasattr(IContextProvider, 'source_type')
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that IContextProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            IContextProvider()  # type: ignore
    
    def test_mock_provider_implements_interface(self):
        """Test that MockProvider implements all required methods."""
        provider = MockProvider()
        
        assert isinstance(provider, IContextProvider)
        assert hasattr(provider, 'retrieve')
        assert hasattr(provider, 'is_available')
        assert hasattr(provider, 'name')
        assert hasattr(provider, 'source_type')


class TestMockProvider:
    """Tests for MockProvider implementation."""
    
    def test_name_property(self):
        """Test provider name."""
        provider = MockProvider()
        assert provider.name == "Mock Provider"
    
    def test_source_type_property(self):
        """Test source type."""
        provider = MockProvider()
        assert provider.source_type == "mock"
    
    def test_is_available_true(self):
        """Test is_available returns True when configured."""
        provider = MockProvider(available=True)
        assert provider.is_available() is True
    
    def test_is_available_false(self):
        """Test is_available returns False when configured."""
        provider = MockProvider(available=False)
        assert provider.is_available() is False
    
    def test_retrieve_empty_items(self):
        """Test retrieve with no items."""
        provider = MockProvider(items=[])
        request = ContextRequest(
            tag="@mock",
            query="test",
            project="test-project"
        )
        
        results = provider.retrieve(request)
        assert len(results) == 0
    
    def test_retrieve_matching_items(self):
        """Test retrieve returns matching items."""
        item1 = ContextItem(
            content="Decision: Use SQLite",
            source="mock",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        item2 = ContextItem(
            content="Learning: WAL mode is faster",
            source="mock",
            project="test",
            metadata={},
            relevance_score=0.85,
            timestamp=datetime.now()
        )
        
        provider = MockProvider(items=[item1, item2])
        request = ContextRequest(
            tag="@mock",
            query="SQLite",
            project="test"
        )
        
        results = provider.retrieve(request)
        assert len(results) == 1
        assert results[0].content == "Decision: Use SQLite"
    
    def test_retrieve_filters_by_relevance(self):
        """Test retrieve filters by min_relevance."""
        item_high = ContextItem(
            content="High relevance item",
            source="mock",
            project="test",
            metadata={},
            relevance_score=0.90,
            timestamp=datetime.now()
        )
        item_low = ContextItem(
            content="Low relevance item",
            source="mock",
            project="test",
            metadata={},
            relevance_score=0.60,
            timestamp=datetime.now()
        )
        
        provider = MockProvider(items=[item_high, item_low])
        request = ContextRequest(
            tag="@mock",
            query="item",
            project="test",
            min_relevance=0.70
        )
        
        results = provider.retrieve(request)
        assert len(results) == 1
        assert results[0].relevance_score >= 0.70
    
    def test_retrieve_respects_max_items(self):
        """Test retrieve respects max_items limit."""
        items = [
            ContextItem(
                content=f"Item {i}",
                source="mock",
                project="test",
                metadata={},
                relevance_score=0.9,
                timestamp=datetime.now()
            )
            for i in range(20)
        ]
        
        provider = MockProvider(items=items)
        request = ContextRequest(
            tag="@mock",
            query="Item",
            project="test",
            max_items=5
        )
        
        results = provider.retrieve(request)
        assert len(results) == 5
    
    def test_retrieve_sorts_by_relevance(self):
        """Test retrieve sorts results by relevance (descending)."""
        items = [
            ContextItem(
                content="Low",
                source="mock",
                project="test",
                metadata={},
                relevance_score=0.75,
                timestamp=datetime.now()
            ),
            ContextItem(
                content="High",
                source="mock",
                project="test",
                metadata={},
                relevance_score=0.95,
                timestamp=datetime.now()
            ),
            ContextItem(
                content="Medium",
                source="mock",
                project="test",
                metadata={},
                relevance_score=0.85,
                timestamp=datetime.now()
            ),
        ]
        
        provider = MockProvider(items=items)
        request = ContextRequest(
            tag="@mock",
            query="",  # Match all
            project="test"
        )
        
        # Hack: make query match all by modifying items
        for item in items:
            item.content += " match"
        request.query = "match"
        
        results = provider.retrieve(request)
        assert len(results) == 3
        assert results[0].relevance_score == 0.95
        assert results[1].relevance_score == 0.85
        assert results[2].relevance_score == 0.75
    
    def test_retrieve_tracks_calls(self):
        """Test that retrieve tracks if it was called."""
        provider = MockProvider()
        assert provider._retrieve_called is False
        
        request = ContextRequest(
            tag="@mock",
            query="test",
            project="test"
        )
        provider.retrieve(request)
        
        assert provider._retrieve_called is True
        assert provider._last_request == request


class TestProviderContract:
    """Tests to verify provider contract expectations."""
    
    def test_retrieve_returns_list(self):
        """Test that retrieve returns a list."""
        provider = MockProvider()
        request = ContextRequest(
            tag="@mock",
            query="test",
            project="test"
        )
        
        result = provider.retrieve(request)
        assert isinstance(result, list)
    
    def test_retrieve_returns_context_items(self):
        """Test that retrieve returns ContextItem objects."""
        item = ContextItem(
            content="test",
            source="mock",
            project="test",
            metadata={},
            relevance_score=0.9,
            timestamp=datetime.now()
        )
        
        provider = MockProvider(items=[item])
        request = ContextRequest(
            tag="@mock",
            query="test",
            project="test"
        )
        
        results = provider.retrieve(request)
        assert all(isinstance(r, ContextItem) for r in results)
    
    def test_is_available_returns_bool(self):
        """Test that is_available returns boolean."""
        provider = MockProvider()
        result = provider.is_available()
        
        assert isinstance(result, bool)
    
    def test_name_returns_string(self):
        """Test that name returns string."""
        provider = MockProvider()
        assert isinstance(provider.name, str)
    
    def test_source_type_returns_string(self):
        """Test that source_type returns string."""
        provider = MockProvider()
        assert isinstance(provider.source_type, str)
