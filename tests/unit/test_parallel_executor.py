"""Tests for parallel tool execution."""

import time

from konseho.tools.parallel import ParallelExecutor


class TestParallelExecutor:
    """Test the ParallelExecutor class."""

    def test_execute_single_tool(self):
        """Test executing a tool with single argument set."""
        executor = ParallelExecutor()

        def mock_tool(value: str) -> str:
            return f"processed: {value}"

        results = executor.execute_parallel(mock_tool, [{"value": "test"}])

        assert len(results) == 1
        assert results[0] == "processed: test"

    def test_execute_multiple_parallel(self):
        """Test executing a tool with multiple arguments in parallel."""
        executor = ParallelExecutor(max_workers=3)

        def slow_tool(value: str) -> str:
            time.sleep(0.1)  # Simulate work
            return f"processed: {value}"

        start = time.time()
        results = executor.execute_parallel(
            slow_tool, [{"value": f"item{i}"} for i in range(3)]
        )
        duration = time.time() - start

        assert len(results) == 3
        assert results[0] == "processed: item0"
        assert results[1] == "processed: item1"
        assert results[2] == "processed: item2"
        # Should be faster than sequential (0.3s)
        assert duration < 0.2

    def test_deduplication(self):
        """Test that duplicate work is not repeated."""
        executor = ParallelExecutor()
        call_count = 0

        def counting_tool(value: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"processed: {value}"

        args_list = [
            {"value": "a"},
            {"value": "b"},
            {"value": "a"},  # duplicate
            {"value": "c"},
            {"value": "b"},  # duplicate
        ]

        results = executor.execute_parallel(counting_tool, args_list)

        assert len(results) == 5
        assert call_count == 3  # Only unique values processed
        assert results[0] == results[2]  # Same result for duplicates
        assert results[1] == results[4]

    def test_maintains_order(self):
        """Test that results are returned in the same order as inputs."""
        executor = ParallelExecutor()

        def reverse_tool(text: str) -> str:
            return text[::-1]

        args_list = [
            {"text": "hello"},
            {"text": "world"},
            {"text": "test"},
        ]

        results = executor.execute_parallel(reverse_tool, args_list)

        assert results == ["olleh", "dlrow", "tset"]

    def test_error_handling(self):
        """Test that errors are handled gracefully."""
        executor = ParallelExecutor()

        def faulty_tool(value: str) -> str:
            if value == "error":
                raise ValueError("Test error")
            return f"processed: {value}"

        args_list = [
            {"value": "ok1"},
            {"value": "error"},
            {"value": "ok2"},
        ]

        results = executor.execute_parallel(faulty_tool, args_list)

        assert len(results) == 3
        assert results[0] == "processed: ok1"
        assert "Error:" in results[1]
        assert results[2] == "processed: ok2"

    def test_max_workers_limit(self):
        """Test that max_workers limits concurrent execution."""
        executor = ParallelExecutor(max_workers=2)
        current_workers = 0
        max_concurrent = 0

        def tracking_tool(value: str) -> str:
            nonlocal current_workers, max_concurrent
            current_workers += 1
            max_concurrent = max(max_concurrent, current_workers)
            time.sleep(0.1)
            current_workers -= 1
            return f"processed: {value}"

        # Execute 5 items with max 2 workers
        executor.execute_parallel(
            tracking_tool, [{"value": f"item{i}"} for i in range(5)]
        )

        assert max_concurrent <= 2

    def test_cache_key_generation(self):
        """Test that cache keys are consistent for same arguments."""
        executor = ParallelExecutor()

        # Same arguments in different order should produce same cache key
        key1 = executor._get_cache_key("test_tool", {"a": 1, "b": 2})
        key2 = executor._get_cache_key("test_tool", {"b": 2, "a": 1})
        key3 = executor._get_cache_key("test_tool", {"a": 1, "b": 3})

        assert key1 == key2  # Same args, different order
        assert key1 != key3  # Different args

    def test_empty_args_list(self):
        """Test handling of empty arguments list."""
        executor = ParallelExecutor()

        def mock_tool(value: str) -> str:
            return f"processed: {value}"

        results = executor.execute_parallel(mock_tool, [])

        assert results == []
