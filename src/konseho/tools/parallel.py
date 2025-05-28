"""Parallel execution utilities for tools."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any


class ParallelExecutor:
    """Execute tools in parallel with deduplication."""

    def __init__(self, max_workers: int=10):
        """Initialize the parallel executor.

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self._cache = {}

    def execute_parallel(self, tool: Callable, args_list: list[dict[str, Any]]
        ) ->list[Any]:
        """Execute tool with different arguments in parallel.

        Args:
            tool: The tool function to execute
            args_list: List of argument dictionaries for each execution

        Returns:
            List of results in the same order as arguments
        """
        if not args_list:
            return []
        results = {}
        unique_work = {}
        for i, args in enumerate(args_list):
            cache_key = self._get_cache_key(tool.__name__, args)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                if cache_key not in unique_work:
                    unique_work[cache_key] = args, []
                unique_work[cache_key][1].append(i)
        if unique_work:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(tool, **args_dict): (cache_key,
                    indices) for cache_key, (args_dict, indices) in
                    unique_work.items()}
                for future in as_completed(futures):
                    cache_key, indices = futures[future]
                    try:
                        result = future.result()
                        self._cache[cache_key] = result
                        for idx in indices:
                            results[idx] = result
                    except Exception as e:
                        error_msg = f'Error: {str(e)}'
                        for idx in indices:
                            results[idx] = error_msg
        return [results[i] for i in range(len(args_list))]

    def _get_cache_key(self, tool_name: str, args: dict[str, Any]) ->str:
        """Generate cache key for deduplication.

        Args:
            tool_name: Name of the tool
            args: Arguments dictionary

        Returns:
            Hash key for caching
        """
        sorted_args = sorted(args.items())
        content = f'{tool_name}:{sorted_args}'
        return hashlib.md5(content.encode()).hexdigest()
