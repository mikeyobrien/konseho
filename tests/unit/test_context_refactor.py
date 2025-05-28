"""Test-driven development for Context refactoring to use list-based results."""

import pytest

from konseho.core.context import Context
from konseho.core.steps import StepResult


class TestContextListBasedResults:
    """Tests for the new list-based results API."""
    
    def test_results_initialized_as_empty_list(self):
        """Test that results are initialized as an empty list."""
        context = Context()
        assert context.results == []
        assert isinstance(context.results, list)
    
    def test_add_result_appends_to_list(self):
        """Test that add_result appends to the results list."""
        context = Context()
        result1 = StepResult(output="Result 1", metadata={"step": 0})
        result2 = StepResult(output="Result 2", metadata={"step": 1})
        
        context.add_result(result1)
        assert len(context.results) == 1
        assert context.results[0] == result1
        
        context.add_result(result2)
        assert len(context.results) == 2
        assert context.results[1] == result2
    
    def test_results_maintain_order(self):
        """Test that results maintain insertion order."""
        context = Context()
        results = [
            StepResult(output=f"Result {i}", metadata={"index": i})
            for i in range(5)
        ]
        
        for result in results:
            context.add_result(result)
        
        assert context.results == results
        for i, result in enumerate(context.results):
            assert result.metadata["index"] == i
    
    def test_get_results_returns_copy(self):
        """Test that get_results returns a copy to prevent external modification."""
        context = Context()
        result = StepResult(output="Test", metadata={})
        context.add_result(result)
        
        results_copy = context.get_results()
        results_copy.append(StepResult(output="Bad", metadata={}))
        
        assert len(context.results) == 1  # Original unchanged
        assert len(results_copy) == 2
    
    def test_results_accessible_by_index(self):
        """Test that results can be accessed by index."""
        context = Context()
        results = [
            StepResult(output=f"Result {i}", metadata={})
            for i in range(3)
        ]
        
        for result in results:
            context.add_result(result)
        
        assert context.results[0].output == "Result 0"
        assert context.results[1].output == "Result 1"
        assert context.results[2].output == "Result 2"
    
    def test_can_iterate_over_results(self):
        """Test that results can be iterated over."""
        context = Context()
        expected_outputs = ["First", "Second", "Third"]
        
        for output in expected_outputs:
            context.add_result(StepResult(output=output, metadata={}))
        
        actual_outputs = [result.output for result in context.results]
        assert actual_outputs == expected_outputs
    
    def test_get_summary_includes_results_list(self):
        """Test that get_summary includes the results list."""
        context = Context()
        result = StepResult(output="Test", metadata={})
        context.add_result(result)
        
        summary = context.get_summary()
        assert "results" in summary
        assert isinstance(summary["results"], list)
        assert len(summary["results"]) == 1
        assert summary["results"][0] == result
    
