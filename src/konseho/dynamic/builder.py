"""Builder for creating dynamic councils based on user queries."""

from typing import Any

from ..core.context import Context
from ..core.council import Council
from .analyzer import TaskType
from .model_agent_factory import ModelAgentFactory
from .model_analyzer import ModelAnalyzer
from .model_step_planner import ModelStepPlanner


class DynamicCouncilBuilder:
    """Builds councils dynamically based on query analysis."""

    def __init__(
        self,
        verbose: bool = False,
        analyzer_model: str | None = None,
        analyzer_temperature: float = 0.3,
    ):
        """Initialize the builder.

        Args:
            verbose: Whether to print verbose output
            analyzer_model: Model to use for query analysis (defaults to Claude Sonnet 4 if not specified)
            analyzer_temperature: Temperature for analysis (lower = more consistent)
        """
        self.verbose = verbose

        # Model-based components only (no fallback)
        # ModelAnalyzer now defaults to Sonnet 4 internally
        self.analyzer = ModelAnalyzer(
            model=analyzer_model, temperature=analyzer_temperature
        )
        self.model_factory = ModelAgentFactory()
        self.model_planner = ModelStepPlanner()

    async def build(
        self,
        query: str,
        context: Context | None = None,
        save_outputs: bool = False,
        output_dir: str | None = None,
    ) -> Council:
        """Build a council optimized for the given query."""
        # Model-based analysis is always async
        analysis = await self.analyzer.analyze(query)

        if self.verbose:
            print(f"\nAnalyzing query: {query[:50]}...")

            # Debug: show what keys are in analysis
            print(f"Analysis keys: {list(analysis.keys())}")

            task_type = analysis.get("task_type", TaskType.GENERAL)
            if hasattr(task_type, "value"):
                print(f"Task type: {task_type.value}")
            else:
                print(f"Task type: {task_type}")

            domains = analysis.get("domains", [])
            if domains:
                print(f"Domains: {', '.join(domains)}")

            complexity = analysis.get("complexity", "medium")
            print(f"Complexity: {complexity}")

            # Show model reasoning if available
            if "reasoning" in analysis:
                print(f"Reasoning: {analysis['reasoning']}")

        # Create agents from model analysis
        if "suggested_agents" not in analysis:
            raise RuntimeError(
                "Model analysis did not provide suggested agents. "
                "This is required for council generation."
            )
        agents = self.model_factory.create_agents_from_spec(
            analysis["suggested_agents"]
        )

        if self.verbose:
            print(f"\nCreated {len(agents)} specialized agents:")
            for agent in agents:
                spec = next(
                    (
                        s
                        for s in analysis["suggested_agents"]
                        if s["name"] == agent.name
                    ),
                    {},
                )
                print(f"  - {agent.name}: {spec.get('role', 'No role specified')}")

        # Plan steps from model analysis
        if "workflow_steps" not in analysis:
            raise RuntimeError(
                "Model analysis did not provide workflow steps. "
                "This is required for council generation."
            )
        steps = self.model_planner.create_steps_from_spec(
            analysis["workflow_steps"], agents
        )

        if self.verbose:
            print(f"\nPlanned {len(steps)} steps:")
            for i, step in enumerate(steps):
                desc = getattr(step, "_description", f"Step {i+1}")
                print(f"  {i+1}. {desc} ({step.__class__.__name__})")

        # Create context if not provided
        if context is None:
            context = Context()

        # Store analysis in context for steps to use
        context.add("query_analysis", analysis)
        context.add("original_query", query)

        # Import factory for creating council
        from ..factories import CouncilFactory

        # Create and configure council using factory
        factory = CouncilFactory()
        council = factory.create_council(
            name="DynamicCouncil",
            steps=steps,  # Pass steps directly
            save_outputs=save_outputs,
            output_dir=output_dir,
        )

        # Update council's context with analysis data
        council.context.add("query_analysis", analysis)
        council.context.add("original_query", query)

        return council

    def build_from_config(self, config: dict[str, Any]) -> Council:
        """Build a council from explicit configuration.

        This method requires async execution for model-based analysis.
        Use the async build() method instead.
        """
        raise NotImplementedError(
            "build_from_config requires async execution for model-based analysis. "
            "Use the async build() method instead."
        )


# Convenience function for quick council creation
async def create_dynamic_council(
    query: str,
    verbose: bool = False,
    analyzer_model: str | None = None,
    save_outputs: bool = False,
    output_dir: str | None = None,
) -> Council:
    """Create a council dynamically based on a query.

    This is the main entry point for dynamic council creation.

    Args:
        query: The task or question to address
        verbose: Whether to print analysis details
        analyzer_model: Model to use for query analysis (defaults to Claude Sonnet 4)

    Returns:
        A configured Council ready to execute

    Example:
        >>> council = await create_dynamic_council("Review this Python code for security issues")
        >>> result = await council.run("def login(username, password): ...")
    """
    builder = DynamicCouncilBuilder(verbose=verbose, analyzer_model=analyzer_model)
    return await builder.build(query, save_outputs=save_outputs, output_dir=output_dir)
