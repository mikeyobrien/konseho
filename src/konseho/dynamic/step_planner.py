"""Plans optimal step sequences based on task requirements."""
from __future__ import annotations

from typing import Any
from ..core.steps import DebateStep, ParallelStep, SplitStep, Step
from ..dynamic.analyzer import TaskType


class StepPlanner:
    """Plans and creates step sequences for councils."""

    def __init__(self):
        self.step_templates = {TaskType.RESEARCH: [{'type': ParallelStep,
            'config': {'description':
            'Initial research across different aspects', 'task_template':
            'Research {domain} aspects of: {query}'}}, {'type': DebateStep,
            'config': {'description':
            'Synthesize findings and resolve conflicts', 'moderator_index':
            0}}], TaskType.CODE_REVIEW: [{'type': ParallelStep, 'config': {
            'description': 'Parallel review from different perspectives',
            'task_template':
            'Review the code focusing on your specialty area'}}, {'type':
            DebateStep, 'config': {'description':
            'Discuss findings and prioritize issues', 'rounds': 2}}],
            TaskType.DESIGN: [{'type': DebateStep, 'config': {'description':
            'Initial design proposals', 'rounds': 1}}, {'type':
            ParallelStep, 'config': {'description':
            'Detailed design for chosen approach', 'task_template':
            'Elaborate on the chosen design focusing on {aspect}'}}, {
            'type': DebateStep, 'config': {'description':
            'Final design review and refinement', 'rounds': 1}}], TaskType.
            ANALYSIS: [{'type': ParallelStep, 'config': {'description':
            'Analyze from multiple perspectives', 'task_template':
            'Analyze the following from your perspective: {query}'}}, {
            'type': DebateStep, 'config': {'description':
            'Synthesize analyses and draw conclusions', 'rounds': 2}}],
            TaskType.PLANNING: [{'type': DebateStep, 'config': {
            'description': 'Brainstorm and propose strategies', 'rounds': 1
            }}, {'type': ParallelStep, 'config': {'description':
            'Develop detailed plans for each aspect', 'task_template':
            'Create detailed plan for: {aspect}'}}, {'type': DebateStep,
            'config': {'description':
            'Integrate plans and resolve conflicts', 'rounds': 1}}],
            TaskType.DEBATE: [{'type': DebateStep, 'config': {'description':
            'Main debate', 'rounds': 3, 'moderator_index': 0}}], TaskType.
            IMPLEMENTATION: [{'type': DebateStep, 'config': {'description':
            'Design discussion', 'rounds': 1}}, {'type': SplitStep,
            'config': {'description':
            'Parallel implementation of components', 'max_splits': 4}}, {
            'type': DebateStep, 'config': {'description':
            'Integration and review', 'rounds': 1}}]}

    def plan_steps(self, analysis: dict[str, Any], agents_count: int) ->list[
        Step]:
        """Plan optimal steps based on analysis."""
        task_type = analysis['task_type']
        complexity = analysis['complexity']
        needs_parallel = analysis['needs_parallel']
        needs_debate = analysis['needs_debate']
        template = self.step_templates.get(task_type, self.
            _get_default_template())
        adjusted_template = self._adjust_template(template, complexity,
            needs_parallel, needs_debate, agents_count)
        steps = self._create_steps(adjusted_template, analysis)
        return steps

    def _get_default_template(self) ->list[dict[str, Any]]:
        """Get default template for general tasks."""
        return [{'type': DebateStep, 'config': {'description':
            'Initial discussion and approach', 'rounds': 1}}, {'type':
            ParallelStep, 'config': {'description':
            'Work on different aspects', 'task_template':
            'Address your assigned aspect of: {query}'}}, {'type':
            DebateStep, 'config': {'description': 'Final synthesis',
            'rounds': 1}}]

    def _adjust_template(self, template: list[dict[str, Any]], complexity:
        str, needs_parallel: bool, needs_debate: bool, agents_count: int
        ) ->list[dict[str, Any]]:
        """Adjust template based on specific requirements."""
        adjusted = []
        for step_config in template:
            config = step_config.copy()
            if config['type'] == DebateStep and 'rounds' in config['config']:
                if complexity == 'high':
                    config['config']['rounds'] = min(config['config'][
                        'rounds'] + 1, 3)
                elif complexity == 'low':
                    config['config']['rounds'] = max(config['config'][
                        'rounds'] - 1, 1)
            if config['type'] == ParallelStep and not needs_parallel:
                continue
            if config['type'] == DebateStep and not needs_debate and len(
                adjusted) > 0:
                continue
            if config['type'] == SplitStep:
                config['config']['max_splits'] = min(agents_count - 1, 4)
            adjusted.append(config)
        if not adjusted:
            adjusted = [{'type': DebateStep, 'config': {'description':
                'Collaborative problem solving', 'rounds': 2}}]
        return adjusted

    def _create_steps(self, template: list[dict[str, Any]], analysis: dict[
        str, Any]) ->list[Step]:
        """Create step instances from template."""
        steps = []
        query = analysis['query']
        domains = analysis['domains']
        for i, step_config in enumerate(template):
            step_type = step_config['type']
            config = step_config['config'].copy()
            if 'task_template' in config:
                config['task_template'] = config['task_template'].replace(
                    '{query}', query)
                if '{domain}' in config['task_template']:
                    pass
                if '{aspect}' in config['task_template']:
                    pass
            if step_type == DebateStep:
                step = DebateStep(rounds=config.get('rounds', 2),
                    moderator_index=config.get('moderator_index', None))
            elif step_type == ParallelStep:
                step = ParallelStep()
                step._task_template = config.get('task_template', query)
            elif step_type == SplitStep:
                step = SplitStep(max_splits=config.get('max_splits', 3))
            else:
                step = DebateStep()
            step._description = config.get('description', f'Step {i + 1}')
            steps.append(step)
        return steps
