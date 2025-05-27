"""Example councils showcasing different multi-agent architectures."""

from .agents.base import AgentWrapper, create_agent
from .core.council import Council
from .core.steps import DebateStep, ParallelStep
from .personas import (
    ANALYST_PROMPT,
    CODER_PROMPT,
    CRITIC_PROMPT,
    EXPLORER_PROMPT,
    PLANNER_PROMPT,
    VISIONARY_PROMPT,
)


def create_innovation_council() -> Council:
    """Create a council focused on innovative solutions and brainstorming."""
    explorer = AgentWrapper(
        create_agent(
            name="Explorer",
            system_prompt=EXPLORER_PROMPT,
            temperature=0.9
        ), 
        name="Explorer"
    )
    
    visionary = AgentWrapper(
        create_agent(
            name="Visionary",
            system_prompt=VISIONARY_PROMPT,
            temperature=0.9
        ), 
        name="Visionary"
    )
    
    critic = AgentWrapper(
        create_agent(
            name="Critic",
            system_prompt=CRITIC_PROMPT,
            temperature=0.6
        ), 
        name="Critic"
    )
    
    return Council(
        name="InnovationCouncil",
        steps=[
            ParallelStep(
                agents=[explorer, visionary],
                task_splitter=lambda task, n: [
                    f"Explore unconventional approaches to: {task}",
                    f"Envision the transformative potential of: {task}"
                ]
            ),
            DebateStep(
                agents=[explorer, visionary, critic],
                rounds=2,
                voting_strategy="weighted"
            )
        ]
    )


def create_development_council() -> Council:
    """Create a council for software development tasks."""
    planner = AgentWrapper(
        create_agent(
            name="Planner",
            system_prompt=PLANNER_PROMPT,
            temperature=0.7
        ), 
        name="Planner",
        expertise_level=0.8
    )
    
    coder = AgentWrapper(
        create_agent(
            name="Coder",
            system_prompt=CODER_PROMPT,
            temperature=0.5
        ), 
        name="Coder",
        expertise_level=1.0
    )
    
    analyst = AgentWrapper(
        create_agent(
            name="Analyst",
            system_prompt=ANALYST_PROMPT,
            temperature=0.6
        ), 
        name="Analyst",
        expertise_level=0.9
    )
    
    return Council(
        name="DevelopmentCouncil",
        steps=[
            # First, plan the approach
            DebateStep(
                agents=[planner, analyst],
                rounds=1,
                voting_strategy="consensus"
            ),
            # Then implement with code review
            ParallelStep(
                agents=[coder, analyst],
                task_splitter=lambda task, n: [
                    f"Implement a solution for: {task}",
                    f"Review and analyze the approach for: {task}"
                ]
            )
        ]
    )


def create_research_council() -> Council:
    """Create a council for research and analysis tasks."""
    explorer = AgentWrapper(
        create_agent(
            name="Explorer",
            system_prompt=EXPLORER_PROMPT,
            temperature=0.8
        ), 
        name="Explorer"
    )
    
    analyst = AgentWrapper(
        create_agent(
            name="Analyst",
            system_prompt=ANALYST_PROMPT,
            temperature=0.6
        ), 
        name="Analyst"
    )
    
    critic = AgentWrapper(
        create_agent(
            name="Critic",
            system_prompt=CRITIC_PROMPT,
            temperature=0.7
        ), 
        name="Critic"
    )
    
    return Council(
        name="ResearchCouncil",
        steps=[
            # Parallel exploration
            ParallelStep(
                agents=[explorer, analyst, critic],
                task_splitter=lambda task, n: [
                    f"Explore different perspectives on: {task}",
                    f"Analyze data and evidence for: {task}",
                    f"Critically evaluate claims about: {task}"
                ]
            ),
            # Synthesis debate
            DebateStep(
                agents=[explorer, analyst, critic],
                rounds=2,
                voting_strategy="moderator",
                moderator=analyst  # Analyst moderates final decision
            )
        ]
    )


def create_balanced_council() -> Council:
    """Create a well-balanced council for general tasks."""
    explorer = AgentWrapper(
        create_agent(
            name="Explorer",
            system_prompt=EXPLORER_PROMPT,
            temperature=0.8
        ), 
        name="Explorer",
        expertise_level=0.7
    )
    
    planner = AgentWrapper(
        create_agent(
            name="Planner",
            system_prompt=PLANNER_PROMPT,
            temperature=0.7
        ), 
        name="Planner",
        expertise_level=0.8
    )
    
    coder = AgentWrapper(
        create_agent(
            name="Coder",
            system_prompt=CODER_PROMPT,
            temperature=0.6
        ), 
        name="Coder",
        expertise_level=0.9
    )
    
    analyst = AgentWrapper(
        create_agent(
            name="Analyst",
            system_prompt=ANALYST_PROMPT,
            temperature=0.6
        ), 
        name="Analyst",
        expertise_level=0.8
    )
    
    return Council(
        name="BalancedCouncil",
        steps=[
            DebateStep(
                agents=[explorer, planner, coder, analyst],
                rounds=2,
                voting_strategy="weighted"  # Uses expertise_level for weighting
            )
        ]
    )


# Quick access to councils
COUNCILS = {
    "innovation": create_innovation_council,
    "development": create_development_council,
    "research": create_research_council,
    "balanced": create_balanced_council,
    "example": None  # Will be set in main.py
}