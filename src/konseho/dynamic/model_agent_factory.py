"""Factory for creating agents from model-generated specifications."""
from __future__ import annotations

from typing import Any
from konseho.protocols import JSON
from ..agents.base import AgentWrapper, create_agent
from .persona_registry import PERSONA_REGISTRY, PersonaTemplate


class ModelAgentFactory:
    """Creates agents based on model-generated specifications."""

    def __init__(self) -> None:
        self.registry = PERSONA_REGISTRY

    def _resolve_tools(self, tool_names: list[object]) ->list[object]:
        """Resolve tool names to actual tool instances.

        Args:
            tool_names: List of tool names or tool instances

        Returns:
            List of resolved tool instances
        """
        resolved_tools = []
        for item in tool_names:
            if isinstance(item, str):
                if item == 'web_search':
                    if mcp_tool := self._get_mcp_search_tool():
                        resolved_tools.append(mcp_tool)
                    else:
                        try:
                            from ..tools.search_tool import web_search
                            resolved_tools.append(web_search)
                        except ImportError:
                            print(f'Warning: Could not import {item} tool')
                else:
                    print(f'Warning: Unknown tool name: {item}')
            else:
                resolved_tools.append(item)
        return resolved_tools

    def _get_mcp_search_tool(self) -> object | None:
        """Try to get search tool from MCP servers.

        Returns:
            MCP search tool if available, None otherwise
        """
        try:
            from ..mcp.strands_integration import StrandsMCPManager
            manager = StrandsMCPManager()
            if tools := manager.get_tools('brave-search'):
                print('Using MCP search tool from brave-search server')
                return tools[0]
        except Exception as e:
            print(f'Could not get MCP search tool: {e}')
        return None

    def create_agents_from_spec(self, agent_specs: list[dict[str, object]]
        ) ->list[AgentWrapper]:
        """Create agents from model-generated specifications.

        Args:
            agent_specs: List of agent specifications from model analysis

        Returns:
            List of configured agent wrappers
        """
        agents = []
        for spec in agent_specs:
            agent_name_value = spec.get('name')
            if not isinstance(agent_name_value, str):
                raise ValueError(f"Agent spec missing valid 'name': {spec}")
            agent_name = agent_name_value
            if persona_template := self.registry.get_persona(agent_name):
                tools = self._resolve_tools(persona_template.tools)
                strands_agent = create_agent(name=agent_name, system_prompt
                    =persona_template.system_prompt, temperature=
                    persona_template.temperature, tools=tools, model=
                    'claude-3-5-haiku-20241022')
                expertise_level = self._get_expertise_level_from_template(
                    persona_template)
            else:
                raise ValueError(
                    f"Agent '{agent_name}' not found in persona registry. Model must only suggest agents from the available personas. Available agents: {', '.join([p.name for p in self.registry.get_all_personas()])}"
                    )
            agent_wrapper = AgentWrapper(strands_agent, name=agent_name,
                expertise_level=expertise_level)
            agents.append(agent_wrapper)
        return agents

    def _get_expertise_level_from_template(self, template: PersonaTemplate) ->float:
        """Get expertise level based on persona template."""
        if (template.category == 'technical' and 'architecture' in template
            .expertise):
            return 0.9
        elif template.category == 'technical':
            return 0.85
        elif template.category in ['analytical', 'research']:
            return 0.8
        else:
            return 0.75

    def _build_persona(self, spec: dict[str, object]) ->str:
        """Build a detailed persona from agent specification."""
        name = spec.get('name', 'agent')
        role = spec.get('role', 'assistant')
        expertise = spec.get('expertise', 'general')
        personality = spec.get('personality', 'collaborative')
        
        # Ensure all values are strings
        name = str(name)
        role = str(role)
        expertise = str(expertise)
        personality = str(personality)
        personality_traits = {'collaborative':
            'You work well with others, building on ideas and finding common ground.'
            , 'analytical':
            'You think systematically, breaking down problems and evaluating options carefully.'
            , 'creative':
            'You think outside the box, proposing innovative and unconventional solutions.'
            , 'critical':
            'You identify potential issues, question assumptions, and ensure thoroughness.'
            , 'pragmatic':
            'You focus on practical, implementable solutions that balance ideals with reality.'
            }
        expertise_descriptions = {'security':
            'security best practices, vulnerability assessment, and threat modeling'
            , 'architecture':
            'system design, architectural patterns, and scalability considerations'
            , 'quality':
            'code quality, maintainability, testing strategies, and best practices'
            , 'business':
            'business strategy, market analysis, and commercial viability',
            'design':
            'user experience, interface design, and human-centered thinking',
            'implementation':
            'practical coding, technical feasibility, and development efficiency'
            , 'performance':
            'optimization, scalability, resource efficiency, and benchmarking',
            'research':
            'information gathering, synthesis, and comprehensive analysis',
            'analysis':
            'data examination, pattern recognition, and evidence-based conclusions'
            }
        personality_trait = personality_traits.get(personality,
            personality_traits['collaborative'])
        expertise_desc = expertise_descriptions.get(expertise,
            f'expertise in {expertise}')
        persona = f"""You are {name}, a specialized agent with {expertise_desc}.

Your primary role: {role}

{personality_trait}

When working in a council:
- Share your unique perspective based on your expertise
- Be concise but thorough in your analysis
- Support your points with specific examples when relevant
- Acknowledge and build upon insights from other agents
- Focus on your area of expertise while considering the broader context

Remember: Your goal is to contribute your specialized knowledge to help the council reach the best possible solution."""
        return persona

    def _get_temperature(self, personality: str) ->float:
        """Get appropriate temperature based on personality type."""
        temperature_map = {'creative': 0.8, 'collaborative': 0.7,
            'analytical': 0.5, 'critical': 0.6, 'pragmatic': 0.6}
        return temperature_map.get(personality, 0.7)

    def _get_expertise_level(self, expertise: str) ->float:
        """Estimate expertise level for weighted voting."""
        high_expertise = ['security', 'architecture', 'performance']
        medium_expertise = ['quality', 'implementation', 'analysis', 'design']
        if expertise in high_expertise:
            return 0.9
        elif expertise in medium_expertise:
            return 0.8
        else:
            return 0.7
