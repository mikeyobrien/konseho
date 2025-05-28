"""Step implementations for different agent coordination patterns."""
from __future__ import annotations

import asyncio
import logging
import re
from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Callable
from typing import Any
from konseho.protocols import JSON
from strands import Agent
from ..agents.base import AgentWrapper
from .context import Context
from ..protocols import StepMetadata, IStepResult
logger = logging.getLogger(__name__)


class StepResult:
    """Result from a step execution."""

    def __init__(self, output: str, metadata: (StepMetadata | None)=None):
        """Initialize step result.

        Args:
            output: The main output from the step
            metadata: Additional metadata about the execution
        """
        self.output = output
        self.metadata: StepMetadata = metadata or {}
        self.success = True


class Step(ABC):
    """Base class for all execution steps."""
    
    def __init__(self) -> None:
        """Initialize step with metadata storage."""
        self.metadata: dict[str, object] = {}

    @property
    def name(self) ->str:
        """Return the step name based on class name."""
        return self.__class__.__name__

    @abstractmethod
    async def execute(self, task: str, context: Context) ->StepResult:
        """Execute the step with given task and context."""
        pass

    def validate(self) ->list[str]:
        """Validate step configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        return []

    def _build_prompt_with_time(self, task: str, context: Context | None = None) ->str:
        """Build a prompt that includes current time and context."""
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        time_info = f'Current date and time: {current_time}'
        parts = [time_info]
        if context is not None and context.to_prompt_context():
            parts.append(context.to_prompt_context())
        parts.append(f'Task: {task}')
        return '\n\n'.join(parts)


class DebateStep(Step):
    """Agents propose competing solutions and vote on the best one."""

    def __init__(self, agents: list[AgentWrapper], moderator: (AgentWrapper |
        None)=None, rounds: int=2, voting_strategy: str='majority'):
        """Initialize debate step.

        Args:
            agents: List of agents participating in the debate
            moderator: Optional moderator agent
            rounds: Number of debate rounds
            voting_strategy: How to determine winner (majority, consensus, moderator)
        """
        super().__init__()
        self.agents = agents
        self.moderator = moderator
        self.rounds = rounds
        self.voting_strategy = voting_strategy

    def validate(self) ->list[str]:
        """Validate debate step configuration."""
        errors = []
        if not self.agents:
            errors.append('DebateStep requires at least one agent')
        if self.rounds < 1:
            errors.append('DebateStep requires at least 1 round')
        valid_strategies = ['majority', 'consensus', 'moderator', 'weighted']
        if self.voting_strategy not in valid_strategies:
            errors.append(
                f'Invalid voting strategy: {self.voting_strategy}. Must be one of {valid_strategies}'
                )
        if self.voting_strategy == 'moderator' and not self.moderator:
            errors.append(
                'Moderator voting strategy requires a moderator agent')
        return errors

    async def _collect_votes(self, proposals: dict[str, str]) ->tuple[dict[
        str, str], int]:
        """Collect votes from all agents."""
        from datetime import datetime
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        voting_prompt = f"""Current date and time: {current_time}

Vote for the best proposal. Reply with 'I vote for: [proposal name]' or 'I abstain from voting'

"""
        for name, proposal in proposals.items():
            if len(proposal) > 200:
                voting_prompt += f'{name}: {proposal[:200]}...\n\n'
            else:
                voting_prompt += f'{name}: {proposal}\n\n'
        vote_tasks = []
        for agent in self.agents:
            vote_tasks.append(agent.work_on(voting_prompt))
        vote_responses = await asyncio.gather(*vote_tasks)
        votes = {}
        abstentions = 0
        for agent, response in zip(self.agents, vote_responses, strict=False):
            vote = self._extract_vote(response, proposals)
            if vote == 'ABSTAIN':
                abstentions += 1
            elif vote:
                votes[agent.name] = vote
        return votes, abstentions

    def _extract_vote(self, response: str, proposals: dict[str, str]) ->(str |
        None):
        """Extract vote from agent response."""
        response = str(response)
        if 'abstain' in response.lower():
            return 'ABSTAIN'
        vote_match = re.search('I vote for:\\s*(.+?)(?:\\n|$)', response,
            re.IGNORECASE)
        if vote_match:
            voted_text = vote_match.group(1).strip()
            for name, proposal in proposals.items():
                proposal_str = str(proposal)
                if name.lower() in voted_text.lower() or voted_text.lower(
                    ) in proposal_str.lower():
                    return proposal
        return None

    def _count_majority_votes(self, votes: dict[str, str], proposals: dict[
        str, str], abstentions: int) ->dict[str, object]:
        """Count votes and determine winner by majority."""
        vote_counts = Counter(votes.values())
        proposal_votes = dict.fromkeys(proposals.keys(), 0)
        for voter, voted_content in votes.items():
            for prop_name, prop_content in proposals.items():
                if str(prop_content) == str(voted_content):
                    proposal_votes[prop_name] += 1
                    break
        if not vote_counts:
            return {'winner': list(proposals.values())[0], 'votes':
                proposal_votes, 'abstentions': abstentions}
        max_votes = max(vote_counts.values())
        winners = [prop for prop, count in vote_counts.items() if count ==
            max_votes]
        if len(winners) > 1:
            return {'winner': winners[0], 'votes': proposal_votes,
                'abstentions': abstentions, 'tie': True, 'tie_resolution':
                'first_proposal'}
        return {'winner': winners[0], 'votes': proposal_votes,
            'abstentions': abstentions}

    def _count_weighted_votes(self, votes: dict[str, str], proposals: dict[
        str, str]) ->dict[str, object]:
        """Count votes with agent expertise weighting."""
        weighted_scores = dict.fromkeys(proposals.keys(), 0.0)
        for agent in self.agents:
            if agent.name in votes:
                expertise = getattr(agent, 'expertise_level', 0.5)
                voted_content = votes[agent.name]
                for prop_name, prop_content in proposals.items():
                    if str(prop_content) == str(voted_content):
                        weighted_scores[prop_name] += expertise
                        break
        winner_name = max(weighted_scores.items(), key=lambda x: x[1])[0]
        winner = proposals[winner_name]
        return {'winner': winner, 'weighted_scores': weighted_scores}

    def _extract_selection(self, response: str, proposals: dict[str, str]
        ) ->str:
        """Extract selected proposal from moderator response."""
        for name, proposal in proposals.items():
            if name in response:
                return proposal
            if len(proposal) > 50:
                if proposal[:50] in response:
                    return proposal
            elif proposal in response:
                return proposal
        return list(proposals.values())[0]

    async def _check_consensus(self, proposals: list[str]) ->bool:
        """Check if all agents proposed the same solution."""
        normalized_proposals = set()
        for prop in proposals:
            if len(prop) > 100:
                normalized_proposals.add(prop[:100])
            else:
                normalized_proposals.add(prop)
        if len(normalized_proposals) == 1:
            return True
        return False

    def _get_latest_proposals(self, all_proposals: dict[str, str]) ->dict[
        str, str]:
        """Get the most recent proposal from each agent."""
        latest = {}
        for agent in self.agents:
            agent_proposals = [(k, v) for k, v in all_proposals.items() if
                k.startswith(agent.name)]
            if agent_proposals:
                latest[agent.name] = sorted(agent_proposals, key=lambda x: x[0]
                    )[-1][1]
        return latest

    async def execute(self, task: str, context: Context) -> StepResult:
        """Execute the debate process."""
        proposals = {}
        all_proposals = []
        proposal_tasks = []
        for agent in self.agents:
            prompt = self._build_prompt_with_time(task, context)
            proposal_tasks.append(self._get_proposal(agent, prompt))
        initial_proposals = await asyncio.gather(*proposal_tasks)
        for agent, proposal in zip(self.agents, initial_proposals, strict=False
            ):
            proposals[agent.name] = proposal
            all_proposals.append(proposal)
        rounds_to_consensus = 1
        consensus_reached = False
        for round_num in range(self.rounds):
            debate_context = self._create_debate_prompt(proposals, round_num)
            debate_tasks = []
            for agent in self.agents:
                from datetime import datetime
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                prompt = f"""Current date and time: {current_time}

{debate_context}

Provide your updated proposal or critique others."""
                debate_tasks.append(self._get_proposal(agent, prompt))
            round_responses = await asyncio.gather(*debate_tasks)
            for agent, response in zip(self.agents, round_responses, strict
                =False):
                proposals[f'{agent.name}_round_{round_num}'] = response
                all_proposals.append(response)
            rounds_to_consensus += 1
            if self.voting_strategy == 'consensus':
                if await self._check_consensus(round_responses):
                    consensus_reached = True
                    break
        winner_data = await self._select_winner(proposals, all_proposals,
            task, context)
        metadata = {'winner': winner_data['winner'], 'proposals': proposals,
            'strategy': self.voting_strategy}
        if 'votes' in winner_data:
            metadata['votes'] = winner_data['votes']
        if 'abstentions' in winner_data:
            metadata['abstentions'] = winner_data['abstentions']
            metadata['total_votes'] = sum(winner_data['votes'].values())
        if 'tie' in winner_data:
            metadata['tie'] = winner_data['tie']
            metadata['tie_resolution'] = winner_data.get('tie_resolution',
                'first_proposal')
        if 'weighted_scores' in winner_data:
            metadata['weighted_scores'] = winner_data['weighted_scores']
        if 'selected_by' in winner_data:
            metadata['selected_by'] = winner_data['selected_by']
        if self.voting_strategy == 'consensus':
            metadata['consensus_reached'] = consensus_reached
            metadata['rounds_to_consensus'] = rounds_to_consensus
        return StepResult(output=winner_data['winner'], metadata=metadata)

    async def _get_proposal(self, agent: AgentWrapper, prompt: str) ->str:
        """Get a proposal from an agent."""
        result = await agent.work_on(prompt)
        # Handle various response formats
        if hasattr(result, '__getitem__'):
            try:
                if 'message' in result:  # type: ignore[operator]
                    return str(result['message'])  # type: ignore[index]
                elif 'content' in result:  # type: ignore[operator]
                    return str(result['content'])  # type: ignore[index]
            except (TypeError, KeyError):
                pass
        return str(result)

    def _create_debate_prompt(self, proposals: dict[str, str], round_num: int
        ) ->str:
        """Create a prompt summarizing the debate so far."""
        prompt = f'Debate Round {round_num + 1}\n\nCurrent Proposals:\n'
        for name, proposal in proposals.items():
            if not name.endswith(f'_round_{round_num}'):
                if len(proposal) > 500:
                    prompt += f'\n{name}:\n{proposal[:500]}...\n'
                else:
                    prompt += f'\n{name}:\n{proposal}\n'
        return prompt

    async def _select_winner(self, proposals: dict[str, str], all_proposals:
        list[str], task: str, context: Context) ->dict[str, object]:
        """Select the winning proposal based on voting strategy."""
        original_proposals = {k: v for k, v in proposals.items() if 
            '_round_' not in k}
        if self.voting_strategy == 'moderator' and self.moderator:
            from datetime import datetime
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            prompt = f"""Current date and time: {current_time}

Select the best proposal for: {task}

Proposals:
"""
            for name, proposal in original_proposals.items():
                if len(proposal) > 300:
                    prompt += f'\n{name}: {proposal[:300]}...\n'
                else:
                    prompt += f'\n{name}: {proposal}\n'
            response = await self.moderator.work_on(prompt)
            winner = self._extract_selection(response, original_proposals)
            return {'winner': winner, 'selected_by': 'moderator'}
        elif self.voting_strategy in ['majority', 'weighted', 'consensus']:
            votes, abstentions = await self._collect_votes(original_proposals)
            if self.voting_strategy == 'majority':
                return self._count_majority_votes(votes, original_proposals,
                    abstentions)
            elif self.voting_strategy == 'weighted':
                return self._count_weighted_votes(votes, original_proposals)
            elif self.voting_strategy == 'consensus':
                latest_proposals = self._get_latest_proposals(proposals)
                if len(set(latest_proposals.values())) == 1:
                    return {'winner': list(latest_proposals.values())[0]}
                else:
                    return self._count_majority_votes(votes,
                        original_proposals, abstentions)
        return {'winner': list(original_proposals.values())[0]}


class ParallelStep(Step):
    """Agents work on different aspects simultaneously."""

    def __init__(self, agents: list[AgentWrapper], task_splitter: (Callable[..., Any] |
        None)=None, result_combiner: (AgentWrapper | None)=None):
        """Initialize parallel step.

        Args:
            agents: List of agents to work in parallel
            task_splitter: Optional function to split task into subtasks
            result_combiner: Optional agent to synthesize parallel results
        """
        super().__init__()
        self.agents = agents
        self.task_splitter = task_splitter
        self.result_combiner = result_combiner

    async def execute(self, task: str, context: Context) ->StepResult:
        """Execute agents in parallel."""
        if self.task_splitter:
            subtasks = self.task_splitter(task, len(self.agents))
        else:
            subtasks = [task] * len(self.agents)
        tasks = []
        for agent, subtask in zip(self.agents, subtasks, strict=False):
            prompt = self._build_prompt_with_time(subtask, context)
            tasks.append(agent.work_on(prompt))
        results = await asyncio.gather(*tasks)
        parallel_results = {agent.name: result for agent, result in zip(
            self.agents, results, strict=False)}
        if self.result_combiner:
            combined_output = await self._combine_with_llm(task,
                parallel_results, context)
            final_output = combined_output
        else:
            output_lines = ['Parallel execution results:']
            for agent_name, result in parallel_results.items():
                output_lines.append(f'\n[{agent_name}]:\n{result}')
            final_output = '\n'.join(output_lines)
        return StepResult(output=final_output, metadata={'parallel_results':
            parallel_results, 'execution_time': 'parallel',
            'agents_involved': [agent.name for agent in self.agents],
            'combined_by': self.result_combiner.name if self.
            result_combiner else 'concatenation'})

    async def _combine_with_llm(self, task: str, parallel_results: dict[str,
        str], context: Context) ->str:
        """Use LLM to synthesize parallel results into a coherent output."""
        combine_prompt = self._build_prompt_with_time(
            f'Synthesize the following parallel results for the task: {task}',
            context)
        combine_prompt += '\n\nParallel Results:'
        for agent_name, result in parallel_results.items():
            combine_prompt += f'\n\n[{agent_name}]:\n{result}'
        combine_prompt += """

Please synthesize these results into a coherent, unified response that captures the key insights and findings from all agents."""
        if self.result_combiner is None:
            raise ValueError("result_combiner is required for LLM combination")
        combined_result = await self.result_combiner.work_on(combine_prompt)
        return str(combined_result)


class SplitStep(Step):
    """Dynamically split work across multiple agent instances."""

    def __init__(self, agent_template: Agent, min_agents: int=2, max_agents:
        int=10, split_strategy: str='auto'):
        """Initialize split step.

        Args:
            agent_template: Template agent to clone
            min_agents: Minimum number of agents
            max_agents: Maximum number of agents
            split_strategy: How to determine split (auto, fixed, adaptive)
        """
        super().__init__()
        self.agent_template = agent_template
        self.min_agents = min_agents
        self.max_agents = max_agents
        self.split_strategy = split_strategy

    async def execute(self, task: str, context: Context) ->StepResult:
        """Execute with dynamically created agents."""
        num_agents = self._determine_agent_count(task, context)
        agents = self._create_agent_clones(num_agents)
        if hasattr(self, '_split_task_with_context'):
            subtasks = self._split_task_with_context(task, num_agents, context)
        else:
            subtasks = self._split_task(task, num_agents)
        tasks = []
        for agent, subtask in zip(agents, subtasks, strict=False):
            prompt = self._build_prompt_with_time(subtask, context)
            tasks.append(agent.work_on(prompt))
        results = await asyncio.gather(*tasks)
        output_lines = [f'Split across {num_agents} agents:']
        for i, (agent, result) in enumerate(zip(agents, results, strict=False)
            ):
            output_lines.append(f'\n[Agent {i + 1}]:\n{result}')
        return StepResult(output='\n'.join(output_lines), metadata={
            'split_results': results, 'num_agents': num_agents, 'strategy':
            self.split_strategy, 'subtasks': subtasks})

    def _determine_agent_count(self, task: str, context: Context) ->int:
        """Determine how many agents to create based on task complexity."""
        if self.split_strategy == 'fixed':
            return self.min_agents
        if self.split_strategy == 'auto':
            word_count = len(task.split())
            line_count = len(task.strip().split('\n'))
            sentence_count = len(re.split('[.!?]+', task))
            has_list = bool(re.search('^\\s*[\\d\\-\\*]', task, re.MULTILINE))
            if word_count < 50:
                base_agents = self.min_agents
            elif word_count < 150:
                base_agents = min(3, self.max_agents)
            elif word_count < 300:
                base_agents = min(5, self.max_agents)
            else:
                base_agents = self.max_agents
            if has_list and line_count > 1:
                base_agents = min(max(line_count, self.min_agents), self.
                    max_agents)
            return base_agents
        return self.min_agents

    def _split_task(self, task: str, num_agents: int) ->list[str]:
        """Intelligently split task into subtasks for each agent."""
        task = task.strip()
        list_items = re.findall('^\\s*[\\d\\-\\*\\.]+\\s*(.+)$', task, re.
            MULTILINE)
        if len(list_items) >= num_agents:
            return self._distribute_items(list_items, num_agents)
        sentences = [s.strip() for s in re.split('[.!?]+', task) if s.strip()]
        if len(sentences) >= num_agents:
            return self._distribute_items(sentences, num_agents)
        if ', and ' in task or ' and ' in task:
            parts = re.split(',\\s*and\\s*|\\s+and\\s+|,\\s*', task)
            parts = [p.strip() for p in parts if p.strip()]
            if len(parts) >= num_agents:
                return self._distribute_items(parts, num_agents)
        components = self._extract_components(task)
        if len(components) >= num_agents:
            subtasks = []
            for i, comp in enumerate(components[:num_agents]):
                subtasks.append(f'Focus on {comp}: {task}')
            return subtasks
        paths = re.findall('\\b\\w+/\\w*\\b', task)
        if len(paths) >= num_agents:
            subtasks = []
            for i, path in enumerate(paths[:num_agents]):
                subtasks.append(f'Handle {path}: {task}')
            return subtasks
        if num_agents == 1:
            return [task]
        else:
            return [f'Agent {i + 1} of {num_agents}: {task}' for i in range
                (num_agents)]

    def _distribute_items(self, items: list[str], num_agents: int) ->list[str]:
        """Distribute items among agents as evenly as possible."""
        subtasks: list[list[str]] = [[] for _ in range(num_agents)]
        for i, item in enumerate(items):
            subtasks[i % num_agents].append(item)
        result = []
        for i, agent_items in enumerate(subtasks):
            if agent_items:
                if len(agent_items) == 1:
                    result.append(agent_items[0])
                else:
                    result.append(' '.join([f'{j + 1}. {item}' for j, item in
                        enumerate(agent_items)]))
            else:
                result.append(f'Agent {i + 1}: Assist with overall task')
        return result

    def _extract_components(self, task: str) ->list[str]:
        """Extract component names from task description."""
        components = []
        component_keywords = ['frontend', 'backend', 'database', 'api',
            'ui', 'server', 'client', 'mobile', 'web', 'desktop', 'service',
            'infrastructure']
        task_lower = task.lower()
        for keyword in component_keywords:
            if keyword in task_lower:
                components.append(keyword)
        return components

    def _split_task_with_context(self, task: str, num_agents: int, context:
        Context) ->list[str]:
        """Split task using context information for better distribution."""
        project_structure_value = context.get('project_structure', {})
        if not isinstance(project_structure_value, dict):
            return self._default_split(task, num_agents)
        project_structure = project_structure_value
        if project_structure and len(project_structure) >= num_agents:
            subtasks = []
            components = list(project_structure.keys())[:num_agents]
            for component in components:
                tech_stack = project_structure[component]
                if isinstance(tech_stack, list):
                    tech_str = ' and '.join(tech_stack)
                    subtasks.append(f'Handle {component} ({tech_str}): {task}')
                else:
                    subtasks.append(f'Handle {component}: {task}')
            return subtasks
        return self._split_task(task, num_agents)

    def _create_agent_clones(self, num_agents: int) ->list[AgentWrapper]:
        """Create cloned agent wrappers."""
        agents = []
        template_wrapper = AgentWrapper(agent=self.agent_template, name=
            'template')
        for i in range(num_agents):
            cloned_wrapper = template_wrapper.clone(f'split_agent_{i}')
            agents.append(cloned_wrapper)
        return agents
