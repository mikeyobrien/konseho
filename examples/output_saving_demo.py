#!/usr/bin/env python3
"""Example demonstrating council output saving functionality."""

import asyncio
from pathlib import Path

from konseho import Context, DebateStep
from konseho.factories import CouncilFactory
from konseho.agents.base import AgentWrapper, create_agent
from konseho.core.output_manager import OutputManager
from konseho.dynamic.builder import create_dynamic_council
from konseho.personas import ANALYST_PROMPT, EXPLORER_PROMPT, PLANNER_PROMPT


async def demo_basic_output_saving():
    """Demo basic output saving with a simple council."""
    print("=== Basic Output Saving Demo ===\n")
    
    # Create agents
    explorer = AgentWrapper(
        create_agent(
            name="Explorer",
            system_prompt=EXPLORER_PROMPT,
            temperature=0.8
        ),
        name="Explorer"
    )
    
    planner = AgentWrapper(
        create_agent(
            name="Planner", 
            system_prompt=PLANNER_PROMPT,
            temperature=0.7
        ),
        name="Planner"
    )
    
    # Create council with output saving enabled
    factory = CouncilFactory()

    council = factory.create_council(
        name="PlanningCouncil",
        steps=[DebateStep(agents=[explorer, planner], rounds=1

    )],
        save_outputs=True,  # Enable output saving
        output_dir="demo_outputs"  # Custom output directory
    )
    
    # Execute task
    task = "Plan a sustainable urban garden project"
    print(f"Task: {task}\n")
    
    result = await council.execute(task)
    
    print("\n✅ Task completed!")
    print("📁 Output saved to: demo_outputs/planningcouncil/")


async def demo_dynamic_council_outputs():
    """Demo output saving with dynamic councils."""
    print("\n\n=== Dynamic Council Output Saving Demo ===\n")
    
    # Create dynamic council with output saving
    query = "Analyze the security implications of using AI in healthcare"
    print(f"Query: {query}\n")
    
    council = await create_dynamic_council(
        query,
        verbose=False,
        save_outputs=True,
        output_dir="demo_outputs"
    )
    
    result = await council.execute(query)
    
    print("\n✅ Task completed!")
    print("📁 Output saved to: demo_outputs/dynamiccouncil/")


def demo_output_management():
    """Demo the output manager functionality."""
    print("\n\n=== Output Management Demo ===\n")
    
    # Create output manager
    manager = OutputManager("demo_outputs")
    
    # List all saved outputs
    outputs = manager.list_outputs()
    
    if outputs:
        print(f"Found {len(outputs)} saved outputs:\n")
        
        for i, output in enumerate(outputs[:5]):  # Show first 5
            print(f"{i+1}. {output['council_name']} - {output['timestamp']}")
            print(f"   Task: {output['task'][:60]}...")
            print(f"   File: {Path(output['file']).name}")
            if output['has_text']:
                print("   ✓ Has formatted text version")
            print()
        
        # Load and display a sample output
        if outputs:
            print("\n--- Sample Output Content ---")
            sample = manager.load_output(outputs[0]['file'])
            print(f"Council: {sample['council_name']}")
            print(f"Task: {sample['task']}")
            print(f"Timestamp: {sample['timestamp']}")
            if 'metadata' in sample:
                print(f"Metadata: {sample['metadata']}")
    else:
        print("No outputs found. Run the demos above first!")


async def demo_custom_metadata():
    """Demo saving outputs with custom metadata."""
    print("\n\n=== Custom Metadata Demo ===\n")
    
    # Create agents
    analyst = AgentWrapper(
        create_agent(
            name="Analyst",
            system_prompt=ANALYST_PROMPT,
            temperature=0.6
        ),
        name="Analyst"
    )
    
    # Create council
    factory = CouncilFactory()

    council = factory.create_council(
        name="AnalysisCouncil",
        agents=[analyst],
        save_outputs=True,
        output_dir="demo_outputs"

    )
    
    # Execute task with context that includes metadata
    task = "Analyze the ROI of implementing renewable energy in office buildings"
    context = Context()
    context.add("project_id", "RENEW-2024-001")
    context.add("client", "GreenCorp Industries")
    
    # Set council context
    council.context = context
    
    result = await council.execute(task)
    
    print("\n✅ Task completed with custom metadata!")
    print("📁 Output includes project_id and client information")


async def main():
    """Run all demos."""
    print("🏛️  Konseho Output Saving Demos")
    print("=" * 50)
    
    # Run demos
    await demo_basic_output_saving()
    await demo_dynamic_council_outputs()
    await demo_custom_metadata()
    
    # Show output management
    demo_output_management()
    
    print("\n\n✨ All demos completed!")
    print("\nCheck the 'demo_outputs' directory to see saved outputs:")
    print("- JSON files: Complete structured data")
    print("- TXT files: Human-readable formatted reports")
    
    # Clean up old outputs (optional)
    # manager = OutputManager("demo_outputs")
    # manager.cleanup_old_outputs(days=7)  # Remove outputs older than 7 days


if __name__ == "__main__":
    asyncio.run(main())