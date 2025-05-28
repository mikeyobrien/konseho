"""Parallel execution utilities for tools."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypeVar
from konseho.protocols import JSON

T = TypeVar('T')


class ParallelExecutor:
    """Execute tools in parallel with deduplication."""

    def __init__(self, max_workers: int=10):
        """Initialize the parallel executor.

        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self._cache: dict[str, object] = {}

    def execute_parallel(self, tool: object, args_list: list[dict[str, JSON]]
        ) ->list[object]:
        """Execute tool with different arguments in parallel.

        Args:
            tool: The tool function to execute
            args_list: List of argument dictionaries for each execution

        Returns:
            List of results in the same order as arguments
        """
        if not args_list:
            return []
        results: dict[int, object] = {}
        unique_work: dict[str, tuple[dict[str, JSON], list[int]]] = {}
        for i, args in enumerate(args_list):
            tool_name = getattr(tool, '__name__', 'unnamed_tool')
            cache_key = self._get_cache_key(tool_name, args)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                if cache_key not in unique_work:
                    unique_work[cache_key] = args, []
                unique_work[cache_key][1].append(i)
        if unique_work:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Execute tools with type: ignore for dynamic callable
                from concurrent.futures import Future
                futures: dict[Future[object], tuple[str, list[int]]] = {}
                for cache_key, (args_dict, indices) in unique_work.items():
                    future: Future[object] = executor.submit(tool, **args_dict)  # type: ignore[arg-type]
                    futures[future] = (cache_key, indices)
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

    def _get_cache_key(self, tool_name: str, args: dict[str, JSON]) ->str:
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
