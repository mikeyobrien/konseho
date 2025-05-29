"""Demo of ParallelStep with LLM-powered result combination."""

import asyncio
from konseho.core.council import Council
from konseho.core.steps import ParallelStep
from konseho.agents.base import AgentWrapper
from konseho.factories import create_agents


async def main():
    """Demonstrate parallel execution with LLM synthesis."""
    
    # Create specialized agents for different domains
    agents = create_agents({
        "security_expert": "You are a security expert. Focus on security implications and vulnerabilities.",
        "performance_expert": "You are a performance expert. Focus on efficiency, speed, and optimization.",
        "ux_expert": "You are a UX expert. Focus on user experience, usability, and design.",
    })
    
    # Create a synthesizer agent to combine results
    synthesizer = create_agents({
        "synthesizer": "You are an expert at synthesizing multiple perspectives into coherent insights."
    })["synthesizer"]
    
    # Example 1: Without combiner (default concatenation)
    print("=== Example 1: Parallel without combiner ===")
    council1 = Council(
        name="ReviewCouncil_NoCombiner",
        steps=[
            ParallelStep(
                agents=list(agents.values()),
                # No result_combiner specified
            )
        ]
    )
    
    result1 = await council1.run("Review this new feature: real-time collaborative editing")
    print(f"\nOutput (concatenated):\n{result1.output}")
    
    # Example 2: With LLM combiner
    print("\n\n=== Example 2: Parallel with LLM combiner ===")
    council2 = Council(
        name="ReviewCouncil_WithCombiner",
        steps=[
            ParallelStep(
                agents=list(agents.values()),
                result_combiner=synthesizer  # LLM will synthesize results
            )
        ]
    )
    
    result2 = await council2.run("Review this new feature: real-time collaborative editing")
    print(f"\nOutput (synthesized):\n{result2.output}")
    print(f"\nCombined by: {result2.metadata['combined_by']}")
    
    # Example 3: Task splitting with combiner
    print("\n\n=== Example 3: Task splitting with synthesis ===")
    
    def split_review_tasks(task: str, num_agents: int) -> list[str]:
        """Split review task by focus area."""
        base_task = task.split(":")[-1].strip() if ":" in task else task
        return [
            f"Review security aspects of: {base_task}",
            f"Review performance implications of: {base_task}",
            f"Review user experience of: {base_task}",
        ][:num_agents]
    
    council3 = Council(
        name="FocusedReviewCouncil",
        steps=[
            ParallelStep(
                agents=list(agents.values()),
                task_splitter=split_review_tasks,
                result_combiner=synthesizer
            )
        ]
    )
    
    result3 = await council3.run("Review this new feature: real-time collaborative editing")
    print(f"\nOutput (focused & synthesized):\n{result3.output}")


if __name__ == "__main__":
    asyncio.run(main())