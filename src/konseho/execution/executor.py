"""Async execution engine for councils."""

import asyncio
from typing import List, Dict, Any, Optional, Callable, Union, TYPE_CHECKING
from collections import Counter
import logging

from ..core.context import Context
from ..core.steps import Step
from .events import EventType, CouncilEvent, EventEmitter

if TYPE_CHECKING:
    from ..core.council import Council

logger = logging.getLogger(__name__)


class StepExecutor:
    """Executes individual steps with parallelization and error handling."""
    
    def __init__(
        self,
        error_strategy: str = "halt",
        retry_attempts: int = 2,
        event_handler: Optional[Callable] = None
    ):
        """Initialize step executor.
        
        Args:
            error_strategy: "halt", "continue", or "retry"
            retry_attempts: Number of retry attempts for retry strategy
            event_handler: Optional event handler for emitting events
        """
        self.error_strategy = error_strategy
        self.retry_attempts = retry_attempts
        self.event_handler = event_handler or (lambda e, d: None)
    
    async def execute_parallel(
        self,
        agents: List[Any],
        task: str,
        context: Context
    ) -> List[Any]:
        """Execute agents in parallel with error handling."""
        self.event_handler("parallel:start", {
            "agent_count": len(agents),
            "task": task
        })
        
        # Prepare tasks with context injection
        agent_tasks = []
        for i, agent in enumerate(agents):
            agent_name = getattr(agent, 'name', f'agent_{i}')
            
            # Inject context into task
            task_with_context = self._inject_context(task, context)
            
            self.event_handler("agent:start", {
                "agent": agent_name,
                "task": task_with_context
            })
            
            agent_tasks.append(self._execute_agent_with_retry(
                agent, task_with_context, agent_name
            ))
        
        # Execute all agents in parallel
        results = await asyncio.gather(*agent_tasks, return_exceptions=True)
        
        # Handle results based on error strategy
        processed_results = []
        for i, result in enumerate(results):
            agent_name = getattr(agents[i], 'name', f'agent_{i}')
            
            if isinstance(result, Exception):
                self.event_handler("agent:error", {
                    "agent": agent_name,
                    "error": str(result)
                })
                
                if self.error_strategy == "halt":
                    raise result
                elif self.error_strategy == "continue":
                    processed_results.append(result)
                else:  # retry handled in _execute_agent_with_retry
                    processed_results.append(result)
            else:
                self.event_handler("agent:complete", {
                    "agent": agent_name,
                    "result": result
                })
                processed_results.append(result)
        
        self.event_handler("parallel:complete", {
            "results_count": len(processed_results),
            "success_count": len([r for r in processed_results if not isinstance(r, Exception)])
        })
        
        return processed_results
    
    async def _execute_agent_with_retry(
        self,
        agent: Any,
        task: str,
        agent_name: str
    ) -> Any:
        """Execute agent with retry logic."""
        last_exception = None
        
        for attempt in range(self.retry_attempts + 1):
            try:
                if hasattr(agent, 'work_on'):
                    # Use our AgentWrapper interface
                    result = await agent.work_on(task)
                else:
                    # Direct agent call - convert to async
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, agent, task)
                
                return result
                
            except Exception as e:
                last_exception = e
                if attempt < self.retry_attempts and self.error_strategy == "retry":
                    self.event_handler("agent:retry", {
                        "agent": agent_name,
                        "attempt": attempt + 1,
                        "error": str(e)
                    })
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff
                else:
                    break
        
        raise last_exception
    
    def _inject_context(self, task: str, context: Context) -> str:
        """Inject context and current time into task prompt."""
        from datetime import datetime
        
        # Always include current time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_info = f"Current date and time: {current_time}"
        
        # Add context if available
        if context and (context._data or context._results):
            context_str = context.to_prompt_context(max_length=1000)
            return f"{time_info}\n\n{context_str}\n\nTask: {task}"
        else:
            return f"{time_info}\n\nTask: {task}"


class AsyncExecutor:
    """Manages async execution of councils and steps."""
    
    def __init__(self, max_concurrent: int = 5):
        """Initialize executor.
        
        Args:
            max_concurrent: Maximum concurrent executions
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active_tasks: Dict[str, asyncio.Task] = {}
    
    async def execute_council(self, council: "Council", task: str) -> Dict[str, Any]:
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
    
    async def execute_steps(
        self,
        steps: List[Step],
        task: str,
        context: Context
    ) -> List[Dict[str, Any]]:
        """Execute multiple steps with concurrency control."""
        async with self._semaphore:
            step_tasks = []
            for i, step in enumerate(steps):
                step_task = step.execute(task, context)
                step_tasks.append(step_task)
            
            results = await asyncio.gather(*step_tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Step {i} failed: {result}")
                    processed_results.append(result)
                else:
                    processed_results.append(result)
            
            return processed_results
    
    async def execute_many(
        self,
        councils: List["Council"],
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


class DecisionProtocol:
    """Implements various decision-making protocols for debates."""
    
    def __init__(
        self,
        strategy: str = "majority",
        threshold: float = 0.5,
        moderator: Optional[Any] = None
    ):
        """Initialize decision protocol.
        
        Args:
            strategy: "majority", "consensus", "moderator", or "weighted"
            threshold: Threshold for consensus (0.0-1.0)
            moderator: Agent to make moderator decisions
        """
        self.strategy = strategy
        self.threshold = threshold
        self.moderator = moderator
    
    async def decide(self, proposals: Dict[str, str]) -> Dict[str, Any]:
        """Make a decision based on proposals."""
        if self.strategy == "majority":
            return await self._majority_vote(proposals)
        elif self.strategy == "consensus":
            return await self._consensus_decision(proposals)
        elif self.strategy == "moderator":
            return await self._moderator_decision(proposals)
        else:
            raise ValueError(f"Unknown decision strategy: {self.strategy}")
    
    async def _majority_vote(self, proposals: Dict[str, str]) -> Dict[str, Any]:
        """Simple majority voting."""
        # Count identical proposals
        proposal_counts = Counter(proposals.values())
        winner_option = proposal_counts.most_common(1)[0][0]
        winner_votes = proposal_counts.most_common(1)[0][1]
        
        return {
            "option": winner_option,
            "votes": winner_votes,
            "total": len(proposals),
            "strategy": "majority"
        }
    
    async def _consensus_decision(self, proposals: Dict[str, str]) -> Dict[str, Any]:
        """Consensus-based decision with threshold."""
        proposal_counts = Counter(proposals.values())
        total_proposals = len(proposals)
        
        for option, count in proposal_counts.most_common():
            consensus_ratio = count / total_proposals
            if consensus_ratio >= self.threshold:
                return {
                    "option": option,
                    "consensus": consensus_ratio,
                    "votes": count,
                    "total": total_proposals,
                    "strategy": "consensus"
                }
        
        # No consensus reached
        winner_option = proposal_counts.most_common(1)[0][0]
        return {
            "option": winner_option,
            "consensus": proposal_counts.most_common(1)[0][1] / total_proposals,
            "votes": proposal_counts.most_common(1)[0][1],
            "total": total_proposals,
            "strategy": "consensus",
            "consensus_reached": False
        }
    
    async def _moderator_decision(self, proposals: Dict[str, str]) -> Dict[str, Any]:
        """Moderator makes the final decision."""
        if not self.moderator:
            raise ValueError("Moderator required for moderator strategy")
        
        # Format proposals for moderator
        proposal_summary = "\n".join([
            f"- {agent}: {proposal}"
            for agent, proposal in proposals.items()
        ])
        
        moderator_task = f"""
        Review these proposals and choose the best one:
        
        {proposal_summary}
        
        Provide your decision and reasoning.
        """
        
        if hasattr(self.moderator, 'work_on'):
            decision = await self.moderator.work_on(moderator_task)
        else:
            # Direct agent call
            loop = asyncio.get_event_loop()
            decision = await loop.run_in_executor(None, self.moderator, moderator_task)
        
        return {
            "decision": decision,
            "proposals": proposals,
            "strategy": "moderator"
        }