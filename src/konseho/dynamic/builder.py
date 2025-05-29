"""Builder for creating dynamic councils based on user queries."""
from __future__ import annotations

from typing import cast
from konseho.protocols import JSON
from ..core.context import Context
from ..core.council import Council
from .analyzer import TaskType
from .model_agent_factory import ModelAgentFactory
from .model_analyzer import ModelAnalyzer
from .model_step_planner import ModelStepPlanner


class DynamicCouncilBuilder:
    """Builds councils dynamically based on query analysis."""

    def __init__(self, verbose: bool=False, analyzer_model: (str | None)=
        None, analyzer_temperature: float=0.3):
        """Initialize the builder.

        Args:
            verbose: Whether to print verbose output
            analyzer_model: Model to use for query analysis (defaults to Claude Sonnet 4 if not specified)
            analyzer_temperature: Temperature for analysis (lower = more consistent)
        """
        self.verbose = verbose
        self.analyzer = ModelAnalyzer(model=analyzer_model, temperature=
            analyzer_temperature)
        self.model_factory = ModelAgentFactory()
        self.model_planner = ModelStepPlanner()

    async def build(self, query: str, context: (Context | None)=None,
        save_outputs: bool=False, output_dir: (str | None)=None) ->Council:
        """Build a council optimized for the given query."""
        analysis = await self.analyzer.analyze(query)
        if self.verbose:
            print(f'\nAnalyzing query: {query[:50]}...')
            print(f'Analysis keys: {list(analysis.keys())}')
            task_type_val = analysis.get('task_type', 'general')
            print(f'Task type: {task_type_val}')
            domains_val = analysis.get('domains', [])
            if isinstance(domains_val, list):
                domain_strs = [str(d) for d in domains_val]
                print(f"Domains: {', '.join(domain_strs)}")
            complexity = analysis.get('complexity', 'medium')
            print(f'Complexity: {complexity}')
            if 'reasoning' in analysis:
                print(f"Reasoning: {analysis['reasoning']}")
        if 'suggested_agents' not in analysis:
            raise RuntimeError(
                'Model analysis did not provide suggested agents. This is required for council generation.'
                )
        suggested_agents_val = analysis.get('suggested_agents', [])
        if not isinstance(suggested_agents_val, list):
            raise RuntimeError('suggested_agents must be a list')
        # Convert to proper type for model factory
        from typing import cast
        suggested_agents = cast(list[dict[str, object]], suggested_agents_val)
        agents = self.model_factory.create_agents_from_spec(suggested_agents)
        if self.verbose:
            print(f'\nCreated {len(agents)} specialized agents:')
            for agent in agents:
                # Find matching spec
                spec = None
                for s in suggested_agents:
                    if isinstance(s, dict):
                        if s.get('name') == agent.name:
                            spec = s
                            break
                if spec:
                    role = spec.get('role', 'No role specified')
                    print(f"  - {agent.name}: {role}")
        if 'workflow_steps' not in analysis:
            raise RuntimeError(
                'Model analysis did not provide workflow steps. This is required for council generation.'
                )
        workflow_steps_val = analysis.get('workflow_steps', [])
        if not isinstance(workflow_steps_val, list):
            raise RuntimeError('workflow_steps must be a list')
        # Convert to proper type for step planner
        workflow_steps = cast(list[dict[str, JSON]], workflow_steps_val)
        steps = self.model_planner.create_steps_from_spec(workflow_steps, agents)
        if self.verbose:
            print(f'\nPlanned {len(steps)} steps:')
            for i, step in enumerate(steps):
                desc = getattr(step, '_description', f'Step {i + 1}')
                print(f'  {i + 1}. {desc} ({step.__class__.__name__})')
        if context is None:
            context = Context()
        context.add('query_analysis', analysis)
        context.add('original_query', query)
        from ..factories import CouncilFactory
        factory = CouncilFactory()
        # Convert steps to IStep for factory
        from konseho.protocols import IStep
        isteps = cast(list[IStep], steps)
        council = factory.create_council(name='DynamicCouncil', steps=isteps,
            save_outputs=save_outputs, output_dir=output_dir)
        council.context.add('query_analysis', analysis)
        council.context.add('original_query', query)
        return council

    def build_from_config(self, config: dict[str, object]) ->Council:
        """Build a council from explicit configuration.

        This method requires async execution for model-based analysis.
        Use the async build() method instead.
        """
        raise NotImplementedError(
            'build_from_config requires async execution for model-based analysis. Use the async build() method instead.'
            )


async def create_dynamic_council(query: str, verbose: bool=False,
    analyzer_model: (str | None)=None, save_outputs: bool=False, output_dir:
    (str | None)=None) ->Council:
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
    builder = DynamicCouncilBuilder(verbose=verbose, analyzer_model=
        analyzer_model)
    return await builder.build(query, save_outputs=save_outputs, output_dir
        =output_dir)
