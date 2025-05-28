#!/usr/bin/env python3
"""Example showing how to use a custom model for query analysis."""

import asyncio

from konseho.dynamic.builder import DynamicCouncilBuilder


async def main():
    """Run example with custom analyzer model."""
    
    # Example 1: Use a faster model for query analysis
    print("Example 1: Using Haiku for fast query analysis")
    print("-" * 50)
    
    builder_fast = DynamicCouncilBuilder(
        verbose=True,
        analyzer_model="claude-3-haiku-20240307",  # Fast model for analysis
        analyzer_temperature=0.3  # Low temperature for consistent analysis
    )
    
    query = "Review this Python code for security vulnerabilities"
    council = await builder_fast.build(query)
    
    print(f"\nCreated council with {len(council.steps)} steps")
    
    # Example 2: Use a more capable model for complex queries
    print("\n\nExample 2: Using Sonnet for complex query analysis")
    print("-" * 50)
    
    builder_advanced = DynamicCouncilBuilder(
        verbose=True,
        analyzer_model="claude-3-5-sonnet-20241022",  # More capable model
        analyzer_temperature=0.5  # Slightly higher temperature for creativity
    )
    
    complex_query = """
    Design a distributed microservices architecture for an e-commerce platform 
    that needs to handle 1M concurrent users with real-time inventory updates
    """
    
    council2 = await builder_advanced.build(complex_query)
    
    print(f"\nCreated council with {len(council2.steps)} steps")
    
    # Example 3: Using environment default
    print("\n\nExample 3: Using default model from environment config")
    print("-" * 50)
    
    builder_default = DynamicCouncilBuilder(
        verbose=True
        # No analyzer_model specified - uses default from config
    )
    
    query3 = "Write unit tests for a shopping cart class"
    council3 = await builder_default.build(query3)
    
    print(f"\nCreated council with {len(council3.steps)} steps")

if __name__ == "__main__":
    print("🔧 Custom Analyzer Model Examples")
    print("=" * 70)
    print()
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure you have configured your model provider.")
        print("Run: python -m konseho --setup")