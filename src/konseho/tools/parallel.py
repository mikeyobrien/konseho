"""Parallel execution utilities for tools."""

from typing import List, Dict, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib


class ParallelExecutor:
    """Execute tools in parallel with deduplication."""
    
    def __init__(self, max_workers: int = 10):
        """Initialize the parallel executor.
        
        Args:
            max_workers: Maximum number of concurrent workers
        """
        self.max_workers = max_workers
        self._cache = {}  # Simple cache for deduplication
    
    def execute_parallel(self, tool: Callable, args_list: List[Dict[str, Any]]) -> List[Any]:
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
        
        # Check cache and prepare work items
        unique_work = {}  # Track unique work by cache key
        
        for i, args in enumerate(args_list):
            cache_key = self._get_cache_key(tool.__name__, args)
            if cache_key in self._cache:
                results[i] = self._cache[cache_key]
            else:
                if cache_key not in unique_work:
                    unique_work[cache_key] = (args, [])
                unique_work[cache_key][1].append(i)
        
        # Execute unique work items in parallel
        if unique_work:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {
                    executor.submit(tool, **args_dict): (cache_key, indices)
                    for cache_key, (args_dict, indices) in unique_work.items()
                }
                
                for future in as_completed(futures):
                    cache_key, indices = futures[future]
                    try:
                        result = future.result()
                        self._cache[cache_key] = result
                        # Assign result to all indices that need it
                        for idx in indices:
                            results[idx] = result
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        # Assign error to all indices
                        for idx in indices:
                            results[idx] = error_msg
                        # Don't cache errors
        
        # Return results in original order
        return [results[i] for i in range(len(args_list))]
    
    def _get_cache_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Generate cache key for deduplication.
        
        Args:
            tool_name: Name of the tool
            args: Arguments dictionary
            
        Returns:
            Hash key for caching
        """
        # Sort items to ensure consistent keys regardless of order
        sorted_args = sorted(args.items())
        content = f"{tool_name}:{sorted_args}"
        return hashlib.md5(content.encode()).hexdigest()