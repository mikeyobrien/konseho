"""Async execution engine for councils."""

import asyncio
from typing import List, Dict, Any, Optional
import logging

from ..core.council import Council

logger = logging.getLogger(__name__)


class AsyncExecutor:
    """Manages async execution of councils."""
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize executor.
        
        Args:
            max_concurrent: Maximum concurrent council executions
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_council(self, council: Council, task: str) -> Dict[str, Any]:
        """Execute a council with concurrency control."""
        async with self._semaphore:
            logger.info(f"Executing council: {council.name}")
            try:
                result = await council.execute(task)
                logger.info(f"Council {council.name} completed successfully")
                return result
            except Exception as e:
                logger.error(f"Council {council.name} failed: {e}")
                raise
    
    async def execute_many(
        self,
        councils: List[Council],
        tasks: List[str]
    ) -> List[Dict[str, Any]]:
        """Execute multiple councils in parallel."""
        if len(councils) != len(tasks):
            raise ValueError("Number of councils must match number of tasks")
        
        execution_tasks = []
        for council, task in zip(councils, tasks):
            execution_task = self.execute_council(council, task)
            execution_tasks.append(execution_task)
        
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        
        # Process results and handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Council {councils[i].name} failed: {result}")
                processed_results.append({
                    "error": str(result),
                    "council": councils[i].name
                })
            else:
                processed_results.append(result)
        
        return processed_results