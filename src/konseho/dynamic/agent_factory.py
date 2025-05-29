"""Factory for creating agents with dynamic personas based on task requirements."""
from __future__ import annotations

from typing import Any  # TODO: Remove Any usage
from konseho.protocols import JSON
from ..agents.base import AgentWrapper, create_agent
from ..dynamic.analyzer import TaskType


class DynamicAgentFactory:
    """Creates agents with personas tailored to specific tasks."""

    def __init__(self) -> None:
        self.persona_templates = {TaskType.RESEARCH: [{'name':
            'Research Lead', 'persona':
            'You are a senior researcher with expertise in systematic investigation and information synthesis. You excel at identifying credible sources, extracting key insights, and presenting findings clearly.'
            }, {'name': 'Domain Expert', 'persona':
            'You are a subject matter expert with deep knowledge in {domain}. You provide specialized insights and ensure technical accuracy in your field.'
            }, {'name': 'Critical Analyst', 'persona':
            'You are a critical thinker who questions assumptions, identifies gaps in reasoning, and ensures comprehensive coverage of all aspects.'
            }], TaskType.CODE_REVIEW: [{'name': 'Security Reviewer',
            'persona':
            'You are a security expert who identifies vulnerabilities, ensures secure coding practices, and validates authentication/authorization logic.'
            }, {'name': 'Performance Optimizer', 'persona':
            'You focus on code efficiency, identifying bottlenecks, suggesting optimizations, and ensuring scalability.'
            }, {'name': 'Code Quality Inspector', 'persona':
            'You ensure code follows best practices, is maintainable, properly documented, and adheres to SOLID principles.'
            }, {'name': 'Architecture Reviewer', 'persona':
            'You evaluate high-level design decisions, ensure proper separation of concerns, and validate architectural patterns.'
            }], TaskType.DESIGN: [{'name': 'Solutions Architect', 'persona':
            'You design robust, scalable systems considering all technical constraints and future requirements.'
            }, {'name': 'User Experience Expert', 'persona':
            'You ensure designs are user-centric, intuitive, and provide excellent user experience.'
            }, {'name': 'Technical Implementer', 'persona':
            'You focus on practical implementation details, feasibility, and technical trade-offs.'
            }], TaskType.ANALYSIS: [{'name': 'Data Analyst', 'persona':
            'You excel at examining data, identifying patterns, and drawing evidence-based conclusions.'
            }, {'name': 'Strategic Advisor', 'persona':
            'You provide high-level strategic insights and consider long-term implications.'
            }, {'name': 'Risk Assessor', 'persona':
            'You identify potential risks, evaluate probabilities, and suggest mitigation strategies.'
            }], TaskType.PLANNING: [{'name': 'Project Strategist',
            'persona':
            'You create comprehensive plans, define milestones, and ensure all dependencies are considered.'
            }, {'name': 'Resource Coordinator', 'persona':
            'You optimize resource allocation, timeline estimation, and team coordination.'
            }, {'name': 'Risk Manager', 'persona':
            'You identify potential obstacles and create contingency plans.'
            }], TaskType.DEBATE: [{'name': 'Advocate', 'persona':
            'You strongly advocate for {position}, providing compelling arguments and evidence.'
            }, {'name': 'Critic', 'persona':
            'You critically examine {position}, identifying weaknesses and presenting counter-arguments.'
            }], TaskType.IMPLEMENTATION: [{'name': 'Lead Developer',
            'persona':
            'You implement core functionality with clean, efficient code following best practices.'
            }, {'name': 'Test Engineer', 'persona':
            'You ensure comprehensive test coverage and validate all edge cases.'
            }]}
        self.domain_specializations = {'technical':
            'software engineering, system design, and technical architecture',
            'business':
            'business strategy, market analysis, and commercial viability',
            'creative':
            'user experience, design thinking, and creative solutions',
            'scientific':
            'scientific method, research methodology, and empirical analysis',
            'general':
            'broad interdisciplinary knowledge and holistic thinking'}

    def create_agents(self, analysis: dict[str, JSON]) ->list[AgentWrapper]:
        """Create agents based on query analysis results."""
        # Extract values with type narrowing
        task_type_val = analysis.get('task_type', 'general')
        if isinstance(task_type_val, str):
            task_type = TaskType(task_type_val)
        else:
            task_type = TaskType.GENERAL
        
        domains_val = analysis.get('domains', [])
        if isinstance(domains_val, list):
            domains = [str(d) for d in domains_val if isinstance(d, str)]
        else:
            domains = []
        
        agent_count_val = analysis.get('suggested_agent_count', 3)
        if isinstance(agent_count_val, int):
            agent_count = agent_count_val
        else:
            agent_count = 3
        base_personas = self._get_base_personas(task_type, agent_count)
        customized_personas = self._customize_for_domains(base_personas,
            domains)
        if analysis.get('needs_debate') or len(customized_personas) > 2:
            customized_personas.insert(0, self._create_moderator())
        agents = []
        for persona_config in customized_personas:
            strands_agent = create_agent(name=persona_config['name'],
                system_prompt=persona_config['persona'], temperature=0.7)
            agent_wrapper = AgentWrapper(strands_agent, name=persona_config
                ['name'])
            agents.append(agent_wrapper)
        return agents

    def _get_base_personas(self, task_type: TaskType, count: int) ->list[dict
        [str, str]]:
        """Get base personas for a task type."""
        templates = self.persona_templates.get(task_type, self.
            persona_templates[TaskType.GENERAL])
        if len(templates) == count:
            return templates.copy()
        if len(templates) > count:
            return templates[:count]
        personas = templates.copy()
        for i in range(len(templates), count):
            personas.append({'name': f'Expert {i + 1}', 'persona':
                f'You are Expert {i + 1} with strong analytical skills and domain expertise. You provide unique insights and constructive contributions.'
                })
        return personas

    def _customize_for_domains(self, personas: list[dict[str, str]],
        domains: list[str]) ->list[dict[str, str]]:
        """Customize personas for specific domains."""
        customized = []
        for i, persona in enumerate(personas):
            custom_persona = persona.copy()
            if '{domain}' in custom_persona['persona']:
                domain = domains[i % len(domains)] if domains else 'general'
                specialization = self.domain_specializations.get(domain, domain
                    )
                custom_persona['persona'] = custom_persona['persona'].replace(
                    '{domain}', specialization)
            if '{position}' in custom_persona['persona']:
                position = ('the proposed approach' if i == 0 else
                    'alternative approaches')
                custom_persona['persona'] = custom_persona['persona'].replace(
                    '{position}', position)
            customized.append(custom_persona)
        return customized

    def _create_moderator(self) ->dict[str, str]:
        """Create a moderator agent for coordinating discussions."""
        return {'name': 'Moderator', 'persona':
            'You are an expert facilitator who guides productive discussions. You ensure all perspectives are heard, synthesize key insights, identify areas of consensus and disagreement, and help the team reach well-reasoned conclusions. You ask clarifying questions and keep discussions focused on the objective.'
            }

    def _get_general_personas(self, count: int) ->list[dict[str, str]]:
        """Get general-purpose personas when task type is unclear."""
        general_personas = [{'name': 'Strategic Thinker', 'persona':
            'You approach problems strategically, considering long-term implications and high-level design.'
            }, {'name': 'Detail Specialist', 'persona':
            'You focus on implementation details, edge cases, and practical considerations.'
            }, {'name': 'Creative Problem Solver', 'persona':
            'You think outside the box, proposing innovative solutions and alternative approaches.'
            }, {'name': 'Quality Advocate', 'persona':
            'You ensure high standards, best practices, and comprehensive solution coverage.'
            }, {'name': 'Pragmatist', 'persona':
            'You focus on practical, implementable solutions that balance ideal and reality.'
            }]
        return general_personas[:count]
