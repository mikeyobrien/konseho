"""Factory for creating agents from model-generated specifications."""

from typing import List, Dict, Any
from ..agents.base import AgentWrapper, create_agent
from .persona_registry import PERSONA_REGISTRY


class ModelAgentFactory:
    """Creates agents based on model-generated specifications."""
    
    def __init__(self):
        self.registry = PERSONA_REGISTRY
    
    def create_agents_from_spec(self, agent_specs: List[Dict[str, Any]]) -> List[AgentWrapper]:
        """Create agents from model-generated specifications.
        
        Args:
            agent_specs: List of agent specifications from model analysis
            
        Returns:
            List of configured agent wrappers
        """
        agents = []
        
        for spec in agent_specs:
            agent_name = spec["name"]
            
            # Look up persona in registry
            persona_template = self.registry.get_persona(agent_name)
            
            if persona_template:
                # Use registered persona
                strands_agent = create_agent(
                    name=agent_name,
                    system_prompt=persona_template.system_prompt,
                    temperature=persona_template.temperature
                )
                
                expertise_level = self._get_expertise_level_from_template(persona_template)
            else:
                # Agent not found in registry - this should not happen with proper model
                raise ValueError(
                    f"Agent '{agent_name}' not found in persona registry. "
                    f"Model must only suggest agents from the available personas. "
                    f"Available agents: {', '.join(self.registry.get_all_names())}"
                )
            
            # Wrap the agent
            agent_wrapper = AgentWrapper(
                strands_agent,
                name=agent_name,
                expertise_level=expertise_level
            )
            
            agents.append(agent_wrapper)
        
        return agents
    
    def _get_expertise_level_from_template(self, template) -> float:
        """Get expertise level based on persona template."""
        # Higher expertise for specialized roles
        if template.category == "technical" and "architecture" in template.expertise:
            return 0.9
        elif template.category == "technical":
            return 0.85
        elif template.category in ["analytical", "research"]:
            return 0.8
        else:
            return 0.75
    
    def _build_persona(self, spec: Dict[str, Any]) -> str:
        """Build a detailed persona from agent specification."""
        name = spec["name"]
        role = spec["role"]
        expertise = spec.get("expertise", "general")
        personality = spec.get("personality", "collaborative")
        
        # Personality traits
        personality_traits = {
            "collaborative": "You work well with others, building on ideas and finding common ground.",
            "analytical": "You think systematically, breaking down problems and evaluating options carefully.",
            "creative": "You think outside the box, proposing innovative and unconventional solutions.",
            "critical": "You identify potential issues, question assumptions, and ensure thoroughness.",
            "pragmatic": "You focus on practical, implementable solutions that balance ideals with reality."
        }
        
        # Expertise descriptions
        expertise_descriptions = {
            "security": "security best practices, vulnerability assessment, and threat modeling",
            "architecture": "system design, architectural patterns, and scalability considerations",
            "quality": "code quality, maintainability, testing strategies, and best practices",
            "business": "business strategy, market analysis, and commercial viability",
            "design": "user experience, interface design, and human-centered thinking",
            "implementation": "practical coding, technical feasibility, and development efficiency",
            "performance": "optimization, scalability, resource efficiency, and benchmarking",
            "research": "information gathering, synthesis, and comprehensive analysis",
            "analysis": "data examination, pattern recognition, and evidence-based conclusions"
        }
        
        personality_trait = personality_traits.get(personality, personality_traits["collaborative"])
        expertise_desc = expertise_descriptions.get(expertise, f"expertise in {expertise}")
        
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
    
    def _get_temperature(self, personality: str) -> float:
        """Get appropriate temperature based on personality type."""
        temperature_map = {
            "creative": 0.8,
            "collaborative": 0.7,
            "analytical": 0.5,
            "critical": 0.6,
            "pragmatic": 0.6
        }
        return temperature_map.get(personality, 0.7)
    
    def _get_expertise_level(self, expertise: str) -> float:
        """Estimate expertise level for weighted voting."""
        # Higher expertise level for more specialized roles
        high_expertise = ["security", "architecture", "performance"]
        medium_expertise = ["quality", "implementation", "analysis", "design"]
        
        if expertise in high_expertise:
            return 0.9
        elif expertise in medium_expertise:
            return 0.8
        else:
            return 0.7