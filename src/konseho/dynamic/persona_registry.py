"""Registry of available agent personas and capabilities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from konseho.protocols import JSON


@dataclass
class PersonaTemplate:
    """Template for an agent persona."""
    name: str
    category: str
    expertise: list[str]
    personality: str
    description: str
    system_prompt: str
    temperature: float = 0.7
    tools: list[object] = field(default_factory=list)


class PersonaRegistry:
    """Registry of all available agent personas."""

    def __init__(self) -> None:
        self.personas: dict[str, PersonaTemplate] = {}
        self._initialize_default_personas()

    def _initialize_default_personas(self) -> None:
        """Initialize the registry with default personas."""
        self.register(PersonaTemplate(name='Security Expert', category=
            'technical', expertise=['security', 'vulnerabilities',
            'authentication'], personality='critical', description=
            'Identifies security vulnerabilities and ensures secure coding practices'
            , system_prompt=
            """You are a security expert specializing in identifying vulnerabilities and security best practices.
Focus on: authentication, authorization, data protection, injection attacks, and secure coding patterns.
Be thorough in identifying potential security risks and suggest concrete mitigations."""
            , temperature=0.6))
        self.register(PersonaTemplate(name='Code Architect', category=
            'technical', expertise=['architecture', 'design patterns',
            'scalability'], personality='analytical', description=
            'Reviews system design and architectural decisions',
            system_prompt=
            """You are a software architect who evaluates high-level design decisions.
Focus on: design patterns, separation of concerns, scalability, maintainability, and architectural best practices.
Consider both current needs and future extensibility."""
            , temperature=0.5))
        self.register(PersonaTemplate(name='Performance Engineer', category
            ='technical', expertise=['performance', 'optimization',
            'scalability'], personality='analytical', description=
            'Optimizes code performance and identifies bottlenecks',
            system_prompt=
            """You are a performance engineer focused on optimization and efficiency.
Focus on: algorithmic complexity, resource usage, caching strategies, database optimization, and scalability.
Provide specific metrics and benchmarks when possible."""
            , temperature=0.5))
        self.register(PersonaTemplate(name='Quality Auditor', category=
            'technical', expertise=['code quality', 'testing',
            'best practices'], personality='pragmatic', description=
            'Ensures code quality, testing, and maintainability',
            system_prompt=
            """You are a code quality expert ensuring maintainable and well-tested code.
Focus on: SOLID principles, testing strategies, code readability, documentation, and maintainability.
Balance ideal practices with practical constraints."""
            , temperature=0.6))
        self.register(PersonaTemplate(name='UX Designer', category=
            'creative', expertise=['user experience', 'interface design',
            'usability'], personality='creative', description=
            'Designs intuitive user experiences and interfaces',
            system_prompt=
            """You are a UX designer focused on creating intuitive user experiences.
Focus on: user flows, accessibility, visual hierarchy, interaction patterns, and user feedback.
Consider diverse user needs and contexts."""
            , temperature=0.8))
        self.register(PersonaTemplate(name='Innovation Specialist',
            category='creative', expertise=['innovation',
            'creative solutions', 'brainstorming'], personality='creative',
            description='Proposes innovative and unconventional solutions',
            system_prompt=
            """You are an innovation specialist who thinks outside the box.
Focus on: novel approaches, emerging technologies, creative problem-solving, and paradigm shifts.
Challenge assumptions and propose bold ideas."""
            , temperature=0.9))
        self.register(PersonaTemplate(name='Data Analyst', category=
            'analytical', expertise=['data analysis', 'metrics', 'insights'
            ], personality='analytical', description=
            'Analyzes data and provides evidence-based insights',
            system_prompt=
            """You are a data analyst who makes decisions based on evidence.
Focus on: data patterns, statistical analysis, metrics interpretation, and data-driven recommendations.
Support arguments with concrete data and examples.
Use the web_search tool to find relevant statistics and benchmarks."""
            , temperature=0.5, tools=['web_search']))
        self.register(PersonaTemplate(name='Risk Assessor', category=
            'analytical', expertise=['risk assessment', 'mitigation',
            'contingency planning'], personality='critical', description=
            'Identifies risks and develops mitigation strategies',
            system_prompt=
            """You are a risk assessment specialist identifying potential issues.
Focus on: risk identification, probability assessment, impact analysis, and mitigation strategies.
Consider both technical and business risks."""
            , temperature=0.6))
        self.register(PersonaTemplate(name='Business Strategist', category=
            'business', expertise=['strategy', 'market analysis', 'ROI'],
            personality='pragmatic', description=
            'Evaluates business impact and strategic alignment',
            system_prompt=
            """You are a business strategist focused on commercial viability.
Focus on: market fit, competitive advantage, ROI, strategic alignment, and business growth.
Balance technical excellence with business needs.
Use the web_search tool to research market trends and competitive landscape."""
            , temperature=0.7, tools=['web_search']))
        self.register(PersonaTemplate(name='Product Manager', category=
            'business', expertise=['product strategy', 'user needs',
            'prioritization'], personality='collaborative', description=
            'Defines product requirements and priorities', system_prompt=
            """You are a product manager bridging user needs and technical implementation.
Focus on: user stories, feature prioritization, MVP definition, and stakeholder alignment.
Balance user value with development effort."""
            , temperature=0.7))
        self.register(PersonaTemplate(name='Research Lead', category=
            'research', expertise=['research', 'information synthesis',
            'analysis'], personality='analytical', description=
            'Conducts comprehensive research and synthesis', system_prompt=
            """You are a research lead conducting systematic investigation.
Focus on: comprehensive coverage, source credibility, information synthesis, and key insights.
Present findings clearly with supporting evidence.
Use the web_search tool to find current information when needed."""
            , temperature=0.7, tools=['web_search']))
        self.register(PersonaTemplate(name='Domain Expert', category=
            'research', expertise=['specialized knowledge',
            'technical depth', 'best practices'], personality='analytical',
            description='Provides deep domain-specific expertise',
            system_prompt=
            """You are a domain expert with deep specialized knowledge.
Focus on: technical accuracy, industry best practices, emerging trends, and expert insights.
Share nuanced understanding of your domain.
Use the web_search tool to verify current information and trends."""
            , temperature=0.6, tools=['web_search']))
        self.register(PersonaTemplate(name='Critical Thinker', category=
            'general', expertise=['critical analysis', 'logic', 'reasoning'
            ], personality='critical', description=
            'Questions assumptions and ensures logical consistency',
            system_prompt=
            """You are a critical thinker who questions assumptions and ensures rigor.
Focus on: logical consistency, evidence evaluation, assumption identification, and gap analysis.
Constructively challenge ideas to strengthen them."""
            , temperature=0.6))
        self.register(PersonaTemplate(name='Synthesizer', category=
            'general', expertise=['synthesis', 'integration',
            'summarization'], personality='collaborative', description=
            'Integrates diverse perspectives into coherent solutions',
            system_prompt=
            """You are a synthesizer who integrates diverse viewpoints.
Focus on: finding common ground, resolving conflicts, creating unified solutions, and clear communication.
Build bridges between different perspectives."""
            , temperature=0.7))
        self.register(PersonaTemplate(name='Implementer', category=
            'general', expertise=['implementation', 'execution',
            'practical solutions'], personality='pragmatic', description=
            'Focuses on practical implementation and execution',
            system_prompt=
            """You are an implementer focused on getting things done.
Focus on: practical solutions, implementation details, feasibility, and execution planning.
Turn ideas into actionable steps."""
            , temperature=0.6))

    def register(self, persona: PersonaTemplate) -> None:
        """Register a new persona template."""
        self.personas[persona.name] = persona

    def get_persona(self, name: str) ->PersonaTemplate | None:
        """Get a specific persona by name."""
        return self.personas.get(name)

    def get_personas_by_category(self, category: str) ->list[PersonaTemplate]:
        """Get all personas in a category."""
        return [p for p in self.personas.values() if p.category == category]

    def get_personas_by_expertise(self, expertise: str) ->list[PersonaTemplate
        ]:
        """Get all personas with specific expertise."""
        return [p for p in self.personas.values() if expertise in p.expertise]

    def get_all_personas(self) ->list[PersonaTemplate]:
        """Get all registered personas."""
        return list(self.personas.values())

    def get_registry_summary(self) ->str:
        """Get a summary of available personas for the model."""
        summary = 'Available Agent Personas:\n\n'
        by_category: dict[str, list[PersonaTemplate]] = {}
        for persona in self.personas.values():
            if persona.category not in by_category:
                by_category[persona.category] = []
            by_category[persona.category].append(persona)
        for category, personas in sorted(by_category.items()):
            summary += f'{category.upper()} AGENTS:\n'
            for persona in personas:
                expertise_str = ', '.join(persona.expertise)
                summary += (
                    f'- {persona.name}: {persona.description} (expertise: {expertise_str})\n'
                    )
            summary += '\n'
        return summary


PERSONA_REGISTRY = PersonaRegistry()
