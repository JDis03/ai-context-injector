"""Integration tests with real-world scenarios.

These tests simulate actual usage patterns to verify the entire pipeline works correctly.
"""

import pytest
from datetime import datetime
from ai_context_injector import (
    ContextInjector,
    ContextItem,
    IContextProvider,
    inject_context,
)


class InMemoryProvider(IContextProvider):
    """Real provider implementation using in-memory storage."""
    
    def __init__(self, data=None):
        """
        Initialize with optional data dictionary.
        
        Args:
            data: Dict mapping project names to lists of (content, score) tuples
        """
        self.data = data or {}
    
    @property
    def name(self) -> str:
        return "InMemoryProvider"
    
    @property
    def source_type(self) -> str:
        return "memory"
    
    def is_available(self) -> bool:
        return True
    
    def retrieve(self, request):
        """Retrieve items using simple substring matching."""
        project_data = self.data.get(request.project, [])
        
        if request.include_cross_project:
            # Include all projects
            all_data = []
            for proj, items in self.data.items():
                all_data.extend([(content, score, proj) for content, score in items])
            project_data = all_data
        else:
            # Add project name to tuples
            project_data = [(content, score, request.project) for content, score in project_data]
        
        # Simple substring matching (case-insensitive)
        query_lower = request.query.lower()
        results = []
        
        for content, score, proj in project_data:
            # Match if ANY query word appears as substring in content
            content_lower = content.lower()
            matches = False
            
            # If query is empty, return all
            if not query_lower.strip():
                matches = True
            else:
                for word in query_lower.split():
                    if word in content_lower:
                        matches = True
                        break
            
            if matches and score >= request.min_relevance:
                results.append(
                    ContextItem(
                        content=content,
                        source="memory",
                        project=proj,
                        metadata={"query": request.query},
                        relevance_score=score,
                        timestamp=datetime.now()
                    )
                )
        
        # Limit results
        return results[:request.max_items]


class TestRealWorldIntegration:
    """Test real-world integration scenarios."""
    
    def test_single_project_retrieval(self):
        """Test retrieving context from single project."""
        # Setup provider with data
        data = {
            "my-project": [
                ("Decision: Use SQLite for local storage", 0.95),
                ("Learning: WAL mode improves performance", 0.90),
                ("TODO: Add database migration system", 0.85),
            ]
        }
        
        provider = InMemoryProvider(data)
        
        # Create injector
        injector = ContextInjector(current_project="my-project")
        injector.register_provider("@memory", provider)
        
        # Inject context
        result = injector.inject("@memory SQLite database")
        
        # Verify result
        assert result is not None
        assert "=== BEGIN CONTEXT ===" in result
        assert "Decision: Use SQLite" in result or "TODO" in result
        # Should match items containing query words
        assert "database" in result.lower()
        assert "CRITICAL RULES" in result  # Anti-hallucination rules
    
    def test_cross_project_retrieval(self):
        """Test cross-project retrieval with :all modifier."""
        data = {
            "project-a": [
                ("Implemented JWT authentication", 0.90),
            ],
            "project-b": [
                ("Used Passport.js for auth", 0.85),
            ],
            "project-c": [
                ("Built custom auth system", 0.80),
            ]
        }
        
        provider = InMemoryProvider(data)
        
        injector = ContextInjector(current_project="project-a")
        injector.register_provider("@memory", provider)
        
        # Use :all modifier for cross-project (query "auth" matches all)
        result = injector.inject("@memory:all auth")
        
        assert result is not None
        assert "JWT" in result or "Passport" in result or "custom" in result
        # Should have at least 2 projects
        assert result.count("Project:") >= 2
        # Should have cross-project warning
        assert "WARNING" in result or "project-b" in result or "project-c" in result
    
    def test_multiple_tags_aggregation(self):
        """Test aggregating results from multiple tags."""
        memory_data = {
            "my-app": [
                ("Architecture decision: Use microservices", 0.90),
            ]
        }
        
        code_data = {
            "my-app": [
                ("Code example: UserService class", 0.85),
            ]
        }
        
        memory_provider = InMemoryProvider(memory_data)
        code_provider = InMemoryProvider(code_data)
        
        injector = ContextInjector(current_project="my-app")
        injector.register_provider("@memory", memory_provider)
        injector.register_provider("@code", code_provider)
        
        # Multiple tags in one query
        result = injector.inject("@memory architecture and @code UserService")
        
        assert result is not None
        assert "microservices" in result
        assert "UserService" in result
        # Should have both items
        assert "Context Item 1/" in result
        assert "Context Item 2/" in result
    
    def test_relevance_filtering(self):
        """Test min_relevance filtering."""
        data = {
            "project": [
                ("High relevance content", 0.95),
                ("Medium relevance content", 0.75),
                ("Low relevance content", 0.50),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        # Set min_relevance to 0.80 (should filter out medium and low)
        result = injector.inject("@memory content", min_relevance=0.80)
        
        assert result is not None
        assert "High relevance" in result
        assert "Medium relevance" not in result
        assert "Low relevance" not in result
    
    def test_max_items_limit(self):
        """Test max_items limiting."""
        data = {
            "project": [
                (f"Item {i}", 0.90) for i in range(20)
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        # Limit to 3 items
        result = injector.inject("@memory Item", max_items=3)
        
        assert result is not None
        assert result.count("--- Context Item") == 3
    
    def test_no_matching_results(self):
        """Test handling when no results match query."""
        data = {
            "project": [
                ("Something about databases", 0.90),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        # Query that won't match
        result = injector.inject("@memory authentication system")
        
        assert result is None  # No context to inject
    
    def test_inject_with_metrics(self):
        """Test inject_with_metrics returns full response."""
        data = {
            "project": [
                ("Content 1", 0.95),
                ("Content 2", 0.90),
                ("Content 3", 0.85),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        response = injector.inject_with_metrics("@memory Content", max_items=2)
        
        assert response.formatted_context
        assert len(response.items) == 2
        # Provider returns max_items, so total_found will be <= 3
        assert response.total_found >= 2
        assert response.filtered_count == 2
        assert response.filter_ratio >= 0
        assert response.performance_ms is not None
    
    def test_convenience_function(self):
        """Test inject_context convenience function."""
        data = {
            "project": [
                ("Quick test content", 0.90),
            ]
        }
        
        providers = {
            "@memory": InMemoryProvider(data)
        }
        
        result = inject_context("@memory test", providers, project="project")
        
        assert result is not None
        assert "Quick test content" in result


class TestComplexScenarios:
    """Test complex real-world scenarios."""
    
    def test_duplicate_content_deduplication(self):
        """Test that duplicate content is deduplicated."""
        data = {
            "project": [
                ("Same content repeated", 0.95),
                ("Same content repeated", 0.90),
                ("Different content here", 0.85),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        result = injector.inject("@memory content")
        
        assert result is not None
        # Should only have 2 unique items
        assert result.count("--- Context Item") == 2
    
    def test_relevance_sorting(self):
        """Test items are sorted by relevance."""
        data = {
            "project": [
                ("Low priority item", 0.70),
                ("High priority item", 0.95),
                ("Medium priority item", 0.80),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        result = injector.inject("@memory item")
        
        assert result is not None
        # High should come before Medium, Medium before Low
        high_pos = result.index("High priority")
        medium_pos = result.index("Medium priority")
        low_pos = result.index("Low priority")
        
        assert high_pos < medium_pos < low_pos
    
    def test_unicode_content(self):
        """Test handling Unicode content."""
        data = {
            "project": [
                ("Decisión: Usar configuración en español con ñ", 0.90),
                ("Learning: 中文内容也可以 (Chinese works too)", 0.85),
                ("TODO: Add emoji support 🎉😀", 0.80),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        result = injector.inject("@memory español")  # Match first item
        
        assert result is not None
        assert "ñ" in result or "español" in result
    
    def test_very_long_content(self):
        """Test handling very long content."""
        long_content = "A" * 10000
        data = {
            "project": [
                (long_content, 0.90),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        result = injector.inject("@memory AAAA")
        
        assert result is not None
        assert long_content in result
    
    def test_empty_query_handling(self):
        """Test that empty/whitespace queries are handled."""
        data = {
            "project": [
                ("Some content", 0.90),
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        # Empty query after tag
        result = injector.inject("@memory   ")
        
        # Should not crash, may return None or empty
        assert result is None or isinstance(result, str)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    def test_full_development_workflow(self):
        """Simulate a complete development workflow."""
        # Setup: Multiple projects with different types of data
        memory_data = {
            "frontend": [
                ("Decision: Use React with TypeScript", 0.95),
                ("Learning: Zustand is simpler than Redux", 0.90),
            ],
            "backend": [
                ("Decision: Use FastAPI for REST API", 0.95),
                ("Learning: Pydantic models improve type safety", 0.90),
            ]
        }
        
        code_data = {
            "frontend": [
                ("Component: UserProfile with hooks", 0.85),
            ],
            "backend": [
                ("Endpoint: POST /api/users with validation", 0.85),
            ]
        }
        
        # Create injector for frontend work
        injector = ContextInjector(current_project="frontend")
        injector.register_provider("@memory", InMemoryProvider(memory_data))
        injector.register_provider("@code", InMemoryProvider(code_data))
        
        # Scenario 1: Ask about frontend architecture
        result = injector.inject("@memory React TypeScript architecture")
        assert result is not None
        assert "React with TypeScript" in result
        assert "backend" not in result.lower()  # Project isolation!
        
        # Scenario 2: Look for code examples
        result = injector.inject("@code UserProfile component")
        assert result is not None
        assert "UserProfile" in result
        
        # Scenario 3: Cross-project learning (with :all)
        result = injector.inject("@memory:all Decision")  # Query that matches content
        assert result is not None
        assert "React" in result or "FastAPI" in result
        assert "WARNING" in result or result.count("Project:") >= 2  # Cross-project warning!
        
        # Scenario 4: Multiple tags at once
        result = injector.inject("@memory React and @code UserProfile")
        assert result is not None
        assert "React" in result
        assert "UserProfile" in result
    
    def test_performance_tracking(self):
        """Test that performance tracking works correctly."""
        data = {
            "project": [
                (f"Item {i}", 0.90) for i in range(100)
            ]
        }
        
        provider = InMemoryProvider(data)
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", provider)
        
        response = injector.inject_with_metrics("@memory Item")
        
        # Verify performance metrics
        assert response.performance_ms is not None
        assert response.performance_ms >= 0
        assert response.performance_ms < 1000  # Should be fast (<1s)
        
        # Verify counts
        assert response.total_found > 0
        assert response.filtered_count > 0
        assert response.filter_ratio > 0
    
    def test_multiple_providers_same_tag_type(self):
        """Test that only one provider per tag works correctly."""
        data1 = {
            "project": [("Data from provider 1", 0.90)]
        }
        data2 = {
            "project": [("Data from provider 2", 0.85)]
        }
        
        injector = ContextInjector(current_project="project")
        injector.register_provider("@memory", InMemoryProvider(data1))
        # Re-registering should replace the first provider
        injector.register_provider("@memory", InMemoryProvider(data2))
        
        result = injector.inject("@memory Data")
        
        assert result is not None
        # Should only have data from second provider
        assert "provider 2" in result
        assert "provider 1" not in result


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_provider_unavailable(self):
        """Test handling when provider becomes unavailable."""
        class UnavailableProvider(IContextProvider):
            @property
            def name(self) -> str:
                return "Unavailable"
            
            @property
            def source_type(self) -> str:
                return "test"
            
            def is_available(self) -> bool:
                return False  # Always unavailable
            
            def retrieve(self, request):
                raise Exception("Should not be called")
        
        injector = ContextInjector(current_project="project")
        injector.register_provider("@test", UnavailableProvider())
        
        result = injector.inject("@test query")
        
        # Should return None gracefully
        assert result is None
    
    def test_provider_returns_empty_list(self):
        """Test handling when provider returns empty list."""
        class EmptyProvider(IContextProvider):
            @property
            def name(self) -> str:
                return "Empty"
            
            @property
            def source_type(self) -> str:
                return "test"
            
            def is_available(self) -> bool:
                return True
            
            def retrieve(self, request):
                return []  # Always empty
        
        injector = ContextInjector(current_project="project")
        injector.register_provider("@test", EmptyProvider())
        
        result = injector.inject("@test query")
        
        assert result is None
    
    def test_unregistered_tag(self):
        """Test using tag without registered provider."""
        injector = ContextInjector(current_project="project")
        
        result = injector.inject("@nonexistent query")
        
        assert result is None  # Should handle gracefully


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])
