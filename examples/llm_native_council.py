"""Example of using the LLM-native dynamic council generation.

This example shows how an LLM can directly generate council specifications
without being constrained by predefined personas or workflows.
"""

import asyncio
import json
from strands import Agent

from konseho.dynamic.llm_native import (
    LLMCouncilGenerator,
    LLMCouncilBuilder,
    CouncilSpec
)


async def main():
    """Demonstrate LLM-native council generation."""
    
    # Example 1: Generate council from user query
    print("=== Example 1: LLM generates council for code review ===\n")
    
    # Create an LLM to generate council specs
    generator_model = Agent(
        model="claude-3-5-sonnet-20241022",
        system_prompt="You are a council configuration generator."
    )
    
    # Create generator
    generator = LLMCouncilGenerator(
        model=generator_model,
        available_tools=["read_file", "code_edit", "web_search"]
    )
    
    # Generate council spec from query
    query = "Review this Python code for security vulnerabilities and performance issues"
    print(f"Query: {query}")
    print("\nGenerating council specification...")
    
    try:
        spec = await generator.generate_council_spec(query)
        print(f"\nGenerated Council: {spec.name}")
        print(f"Agents: {[agent.id for agent in spec.agents]}")
        print(f"Steps: {[step.type for step in spec.steps]}")
    except Exception as e:
        print(f"Generation failed: {e}")
        print("Using fallback example...")
        
        # Fallback: Use a predefined spec for demonstration
        spec = CouncilSpec(
            name="SecurityPerformanceReview",
            description="Reviews code for security and performance",
            agents=[
                {
                    "id": "security_expert",
                    "prompt": "You are a security expert. Analyze code for vulnerabilities, focusing on OWASP top 10, injection flaws, and authentication issues.",
                    "model": "claude-3-haiku",
                    "temperature": 0.2,
                    "tools": ["read_file"]
                },
                {
                    "id": "performance_analyst",
                    "prompt": "You analyze code performance. Look for inefficiencies, memory leaks, and optimization opportunities.",
                    "model": "claude-3-haiku",
                    "temperature": 0.3,
                    "tools": ["read_file", "code_edit"]
                }
            ],
            steps=[
                {
                    "type": "parallel",
                    "agents": ["security_expert", "performance_analyst"],
                    "task_template": "Analyze the code for issues in your domain"
                },
                {
                    "type": "debate",
                    "agents": ["security_expert", "performance_analyst"],
                    "task_template": "Discuss findings and prioritize issues",
                    "config": {"rounds": 2}
                }
            ]
        )
    
    # Example 2: Build council from spec
    print("\n\n=== Example 2: Building council from specification ===\n")
    
    builder = LLMCouncilBuilder()
    
    # Show available tools and models
    print("Available tools:", builder.get_available_tools())
    print("Available models:", builder.get_available_models())
    
    # Build the council
    print("\nBuilding council...")
    council = await builder.build(spec)
    
    print(f"✓ Built council: {council.name}")
    print(f"✓ Created {len(council.steps)} steps")
    
    # Example 3: Direct specification
    print("\n\n=== Example 3: Direct JSON specification ===\n")
    
    json_spec = """
    {
        "name": "SimpleAnalysisCouncil",
        "agents": [
            {
                "id": "analyst",
                "prompt": "You are a code analyst. Review code for clarity and best practices."
            }
        ],
        "steps": [
            {
                "type": "parallel",
                "agents": ["analyst"]
            }
        ]
    }
    """
    
    # Parse and build
    spec_dict = json.loads(json_spec)
    simple_spec = CouncilSpec(**spec_dict)
    simple_council = await builder.build(simple_spec)
    
    print(f"✓ Built simple council: {simple_council.name}")
    
    # Show how the council could be executed (without actually running it)
    print("\n\n=== Council Ready for Execution ===")
    print(f"Council '{council.name}' is ready to execute with:")
    print(f"- {len(spec.agents)} specialized agents")
    print(f"- {len(spec.steps)} execution steps")
    print("\nTo execute: await council.convene(task='Review this code: ...')")


if __name__ == "__main__":
    asyncio.run(main())