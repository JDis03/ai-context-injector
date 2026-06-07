"""Tests for embeddings and semantic search."""

import math
import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from ai_context_injector import (
    Chunk,
    cosine_similarity,
    search_semantic,
    index,
    clear_index,
    pair_distance,
)


class TestCosineSimilarity:
    """Test pure math cosine similarity (no model needed)."""
    
    def test_identical_vectors(self):
        assert cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]) == pytest.approx(1.0)
    
    def test_orthogonal_vectors(self):
        assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)
    
    def test_opposite_vectors(self):
        assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)
    
    def test_random_vectors(self):
        result = cosine_similarity([0.6, 0.8], [0.8, 0.6])
        # cos = (0.6*0.8 + 0.8*0.6) / (1.0 * 1.0) = 0.96
        assert result == pytest.approx(0.96)
    
    def test_different_dimensions(self):
        with pytest.raises(ValueError, match="dimensions must match"):
            cosine_similarity([1.0, 0.0], [1.0, 0.0, 0.0])
    
    def test_zero_norm(self):
        # Zero vector should return 0
        result = cosine_similarity([0.0, 0.0], [1.0, 0.0])
        assert result == 0.0
    
    def test_empty_vectors(self):
        # Two zero vectors
        result = cosine_similarity([0.0], [0.0])
        assert result == 0.0
    
    def test_high_dimensional(self):
        # 384-dim vectors (MiniLM dimension)
        a = [1.0 / math.sqrt(384)] * 384
        b = [1.0 / math.sqrt(384)] * 384
        assert cosine_similarity(a, b) == pytest.approx(1.0)


class TestPairDistance:
    """Test distance metrics."""
    
    def test_cosine_metric(self):
        result = pair_distance([1.0, 0.0], [1.0, 0.0], metric="cosine")
        assert result == pytest.approx(1.0)
    
    def test_euclidean_metric(self):
        result = pair_distance([1.0, 0.0], [1.0, 0.0], metric="euclidean")
        assert result == pytest.approx(1.0)  # 1/(1+0) = 1.0
    
    def test_dot_metric(self):
        result = pair_distance([2.0, 3.0], [4.0, 5.0], metric="dot")
        assert result == pytest.approx(23.0)  # 2*4 + 3*5 = 23
    
    def test_invalid_metric(self):
        with pytest.raises(ValueError, match="Unknown metric"):
            pair_distance([1.0], [1.0], metric="invalid")


class TestSearchSemanticKeywordFallback:
    """Test semantic search falls back to keyword when no model."""
    
    def setup_method(self):
        clear_index()
    
    def test_keyword_fallback_works(self):
        """When embeddings unavailable, falls back to keyword search."""
        chunks = index(
            "docker container escape via bind mount",
            source="writeup-1"
        )
        index("linux kernel exploit", source="writeup-2")
        
        results = search_semantic("docker escape", chunks)
        
        # Should find the docker chunk via keyword fallback
        assert len(results) >= 1
        assert "docker" in results[0][0].content.lower()
    
    def test_keyword_fallback_no_results(self):
        chunks = index("nmap scan results")
        
        results = search_semantic("xyz_nonexistent_123", chunks)
        assert results == []
    
    def test_keyword_fallback_with_filters(self):
        index("linux privesc content", metadata={"os": "linux"})
        index("windows privesc content", metadata={"os": "windows"})
        
        # Search all chunks (not just the first index call)
        clear_index()
        chunks1 = index("linux privesc content", metadata={"os": "linux"})
        chunks2 = index("windows privesc content", metadata={"os": "windows"})
        all_chunks = chunks1 + chunks2
        
        results = search_semantic(
            "privesc",
            all_chunks,
            filters={"os": "linux"}
        )
        
        assert len(results) >= 1
        for chunk, _ in results:
            assert chunk.metadata.get("os") == "linux"
    
    def test_empty_chunks(self):
        results = search_semantic("query", [])
        assert results == []
    
    def test_min_similarity_ignored_in_keyword(self):
        """min_similarity doesn't apply to keyword fallback scores."""
        chunks = index("unique content here")
        
        # Keyword pseudo-scores are always < 1.0, so high threshold
        # would filter everything in cosine mode but keyword ignores it
        results = search_semantic("unique", chunks, min_similarity=0.99)
        # Keyword fallback with 1/1 word match = 1.0 pseudo-score
        assert len(results) >= 1


class TestSearchSemanticWithMockedModel:
    """Test semantic search with mocked embedding model."""
    
    def test_with_mock_embeddings(self):
        """Test that pre-computed embeddings produce correct ranking."""
        chunks = [
            Chunk(content="docker escape", index=0, metadata={"os": "linux"}),
            Chunk(content="windows privesc", index=1, metadata={"os": "windows"}),
            Chunk(content="linux exploit", index=2, metadata={"os": "linux"}),
        ]
        
        # Mock embeddings: docker_escape_emd similar to query_emd
        query_emd = [1.0, 0.0, 0.0]
        chunk_emds = [
            [0.9, 0.1, 0.0],  # Similar to query
            [0.0, 1.0, 0.0],  # Orthogonal
            [0.3, 0.0, 0.1],  # Somewhat similar
        ]
        
        with patch('ai_context_injector.embeddings.embed', return_value=query_emd):
            results = search_semantic(
                "docker",
                chunks,
                embeddings=chunk_emds
            )
        
        # Should rank by similarity
        assert len(results) >= 2
        # First result should be docker_escape (most similar)
        assert "docker" in results[0][0].content.lower()
        assert results[0][1] > 0.5  # High similarity
    
    def test_with_filters_and_embeddings(self):
        """Filters combine with semantic search."""
        chunks = [
            Chunk(content="docker linux", index=0, metadata={"os": "linux"}),
            Chunk(content="docker windows", index=1, metadata={"os": "windows"}),
        ]
        
        query_emd = [1.0, 0.0]
        chunk_emds = [
            [1.0, 0.0],  # Perfect match
            [1.0, 0.0],  # Perfect match
        ]
        
        with patch('ai_context_injector.embeddings.embed', return_value=query_emd):
            results = search_semantic(
                "docker",
                chunks,
                embeddings=chunk_emds,
                filters={"os": "linux"}
            )
        
        # Only linux results
        assert len(results) == 1
        assert results[0][0].metadata["os"] == "linux"
    
    def test_embed_model_none_fallback(self):
        """When embed() returns None, falls back to keyword."""
        chunks = [
            Chunk(content="docker content", index=0)
        ]
        
        with patch('ai_context_injector.embeddings.embed', return_value=None):
            results = search_semantic("docker", chunks)
        
        # Should fall back to keyword search
        assert len(results) >= 1
        assert "docker" in results[0][0].content
    
    def test_top_k_limit(self):
        chunks = [
            Chunk(content=f"item_{i}", index=i) for i in range(20)
        ]
        query_emd = [1.0, 0.0]
        chunk_emds = [[float(i % 10) / 10, 0.0] for i in range(20)]
        
        with patch('ai_context_injector.embeddings.embed', return_value=query_emd):
            results = search_semantic(
                "query",
                chunks,
                embeddings=chunk_emds,
                top_k=5
            )
        
        assert len(results) == 5
