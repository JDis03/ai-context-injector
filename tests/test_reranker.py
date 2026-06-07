"""Tests for cross-encoder reranker."""

import pytest
from unittest.mock import patch, MagicMock

from ai_context_injector import Reranker, rerank


class TestRerankerInit:
    """Test reranker initialization."""
    
    def test_default_model(self):
        reranker = Reranker()
        assert "ms-marco" in reranker.model_name.lower()
    
    def test_custom_model(self):
        reranker = Reranker(model="custom-model")
        assert reranker.model_name == "custom-model"
    
    def test_model_not_loaded_on_init(self):
        """Model should NOT load on init (lazy)."""
        reranker = Reranker()
        assert reranker.model is None
    
    def test_default_cache_size(self):
        reranker = Reranker()
        assert reranker.cache.max_size == 1000


class TestRerankerCache:
    """Test LRU prediction cache."""
    
    def test_cache_miss_then_hit(self):
        reranker = Reranker()
        key = Reranker._make_cache_key("query", "content")
        
        # First access = miss
        assert reranker.cache.get(key) is None
        
        # Set and verify
        reranker.cache.set(key, 0.95)
        assert reranker.cache.get(key) == 0.95
    
    def test_cache_stats(self):
        reranker = Reranker()
        key1 = Reranker._make_cache_key("q", "c1")
        key2 = Reranker._make_cache_key("q", "c2")
        
        reranker.cache.get(key1)  # miss
        reranker.cache.set(key1, 0.8)
        reranker.cache.get(key1)  # hit
        
        stats = reranker.cache_stats()
        assert stats["hits"] >= 1
        assert stats["misses"] >= 1
    
    def test_cache_clear(self):
        reranker = Reranker()
        key = Reranker._make_cache_key("q", "c")
        reranker.cache.set(key, 0.9)
        
        reranker.clear_cache()
        assert reranker.cache.get(key) is None
    
    def test_cache_key_stable(self):
        """Same inputs produce same key."""
        k1 = Reranker._make_cache_key("docker", "escape")
        k2 = Reranker._make_cache_key("docker", "escape")
        assert k1 == k2
    
    def test_cache_key_different(self):
        """Different inputs produce different keys."""
        k1 = Reranker._make_cache_key("query1", "content1")
        k2 = Reranker._make_cache_key("query2", "content2")
        assert k1 != k2


class TestRerankerFallback:
    """Test graceful fallback when model unavailable."""
    
    def test_fallback_on_import_error(self):
        """When sentence-transformers not installed, fallback gracefully."""
        reranker = Reranker()
        
        with patch.object(reranker, '_load_model', return_value=False):
            reranker._fallback_reason = "not installed"
            results = reranker.rerank(
                "query",
                [("content_a", 0.9), ("content_b", 0.5)],
                top_k=2
            )
        
        # Should return in original order
        assert len(results) == 2
        assert results[0][0] == "content_a"  # First by original score
        assert not results[0][2]["reranked"]
        assert "fallback_reason" in results[0][2]
    
    def test_fallback_preserves_top_k(self):
        reranker = Reranker()
        candidates = [(f"item_{i}", 1.0 - i * 0.1) for i in range(10)]
        
        with patch.object(reranker, '_load_model', return_value=False):
            reranker._fallback_reason = "test"
            results = reranker.rerank("query", candidates, top_k=3)
        
        assert len(results) == 3
    
    def test_fallback_empty_candidates(self):
        reranker = Reranker()
        results = reranker.rerank("query", [])
        assert results == []


class TestRerankerWithModelMock:
    """Test reranker with mocked cross-encoder model."""
    
    def test_rerank_uses_cross_encoder(self):
        """Verify model.predict is called with correct pairs."""
        mock_model = MagicMock()
        # Predict: query+content1 > query+content2
        mock_model.predict.return_value = [0.95, 0.3]
        
        reranker = Reranker()
        reranker.model = mock_model
        
        candidates = [
            ("irrelevant content", 0.8),   # Will get low cross-encoder score
            ("highly relevant", 0.75),     # Will get high cross-encoder score
        ]
        
        results = reranker.rerank(
            "important query",
            candidates,
            top_k=2
        )
        
        # Verify model.predict was called
        mock_model.predict.assert_called_once()
        
        # Verify pairs format: (query, content) for each candidate
        call_args = mock_model.predict.call_args[0][0]
        assert len(call_args) == 2
        assert call_args[0] == ("important query", "irrelevant content")
        
        # First result should be the one with highest cross-encoder score (0.95)
        assert results[0][0] == "irrelevant content"
        assert results[0][2]["reranked"]
    
    def test_rerank_returns_top_k(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9, 0.8, 0.7, 0.6, 0.5]
        
        reranker = Reranker()
        reranker.model = mock_model
        
        candidates = [
            ("a", 0.5), ("b", 0.5), ("c", 0.5),
            ("d", 0.5), ("e", 0.5)
        ]
        
        results = reranker.rerank("query", candidates, top_k=2)
        assert len(results) == 2
    
    def test_rerank_limits_max_candidates(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9] * 5
        
        reranker = Reranker()
        reranker.model = mock_model
        
        candidates = [(f"item_{i}", 0.5) for i in range(100)]
        
        results = reranker.rerank("query", candidates, top_k=5, max_candidates=5)
        
        # Should only have predicted 5 pairs
        call_args = mock_model.predict.call_args[0][0]
        assert len(call_args) == 5
    
    def test_prediction_error_fallback(self):
        mock_model = MagicMock()
        mock_model.predict.side_effect = RuntimeError("model crashed")
        
        reranker = Reranker()
        reranker.model = mock_model
        
        candidates = [("content", 0.9)]
        
        results = reranker.rerank("query", candidates, top_k=1)
        
        # Should fallback gracefully
        assert len(results) == 1
        assert not results[0][2]["reranked"]
        assert "fallback_reason" in results[0][2]
    
    def test_metadata_in_results(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.85]
        
        reranker = Reranker()
        reranker.model = mock_model
        
        results = reranker.rerank("query", [("content", 0.7)], top_k=1)
        
        metadata = results[0][2]
        assert metadata["reranked"]
        assert "rerank_time_ms" in metadata
        assert metadata["original_score"] == 0.7


class TestConvenienceFunction:
    """Test rerank() convenience function."""
    
    def test_rerank_function_works(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.9]
        
        with patch('ai_context_injector.reranker.Reranker._load_model', return_value=True):
            with patch('ai_context_injector.reranker._reranker', None):
                # Reset singleton
                import ai_context_injector.reranker as rm
                rm._reranker = None
                
                # Create reranker with mocked model
                rm._reranker = Reranker()
                rm._reranker.model = mock_model
                
                results = rerank(
                    "query",
                    [("content", 0.5)],
                    top_k=1
                )
                
                assert len(results) == 1
                assert results[0][0] == "content"
