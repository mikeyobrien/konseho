"""Comparison of the old persona-based and new LLM-native dynamic council approaches."""

import asyncio
from strands import Agent

from konseho.dynamic.builder import DynamicCouncilBuilder
from konseho.dynamic.llm_native import LLMCouncilGenerator, LLMCouncilBuilder


async def old_approach(query: str):
    """Demonstrate the old persona-based approach."""
    print("=== OLD APPROACH: Persona-Based Dynamic Council ===\n")
    
    # Create the builder with analyzer model
    analyzer_model = Agent(
        model="claude-3-5-sonnet-20241022",
        system_prompt="You are a query analyzer for a multi-agent council system."
    )
    
    builder = DynamicCouncilBuilder(analyzer_model=analyzer_model)
    
    try:
        # Build council - limited to predefined personas
        council = await builder.build_dynamic_council(query)
        print(f"✓ Built council: {council.name}")
        print("  - Must choose from 16 predefined personas")
        print("  - Fixed workflow patterns")
        print("  - Limited tool options")
    except Exception as e:
        print(f"✗ Failed: {e}")


async def new_approach(query: str):
    """Demonstrate the new LLM-native approach."""
    print("\n=== NEW APPROACH: LLM-Native Dynamic Council ===\n")
    
    # Create generator model
    generator_model = Agent(
        model="claude-3-5-sonnet-20241022",
        system_prompt="You are a council configuration generator."
    )
    
    # Create generator with custom tools
    generator = LLMCouncilGenerator(
        model=generator_model,
        available_tools=[
            "read_file", "write_file", "code_edit", "web_search",
            "http_get", "http_post", "custom_analyzer", "security_scanner"
        ]
    )
    
    try:
        # Generate custom council spec
        spec = await generator.generate_council_spec(query)
        
        # Build the council
        builder = LLMCouncilBuilder()
        council = await builder.build(spec)
        
        print(f"✓ Built council: {council.name}")
        print(f"  - Custom agents: {[a.id for a in spec.agents]}")
        print(f"  - Flexible prompts tailored to task")
        print(f"  - Dynamic tool assignment")
        print(f"  - Novel workflow patterns")
        
        # Show the generated spec
        print("\nGenerated specification:")
        for agent in spec.agents[:2]:  # Show first 2 agents
            print(f"\nAgent: {agent.id}")
            print(f"  Prompt: {agent.prompt[:100]}...")
            print(f"  Tools: {agent.tools}")
            print(f"  Temperature: {agent.temperature}")
            
    except Exception as e:
        print(f"✗ Failed: {e}")


async def main():
    """Compare both approaches."""
    query = "Perform a comprehensive security audit of my authentication system, focusing on OAuth2 implementation and session management"
    
    print(f"Query: {query}\n")
    
    # Try old approach
    await old_approach(query)
    
    # Try new approach
    await new_approach(query)
    
    print("\n=== KEY DIFFERENCES ===")
    print("\nOld Approach:")
    print("- Limited to predefined personas")
    print("- Fixed step patterns (debate, parallel, split)")
    print("- Heuristic-based agent selection")
    print("- Rigid tool assignments")
    
    print("\nNew Approach:")
    print("- LLM creates custom agents for specific task")
    print("- Flexible step configurations")
    print("- Direct specification of requirements")
    print("- Dynamic tool assignment based on needs")
    print("- Can create novel workflows")


if __name__ == "__main__":
    asyncio.run(main())