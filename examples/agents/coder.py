"""Coder agent for implementing code solutions."""

from typing import List, Optional
from strands import Agent


class CoderAgent(Agent):
    """Agent specialized in writing and implementing code."""
    
    def __init__(
        self,
        name: str = "Coder",
        model: str = "gpt-4",
        temperature: float = 0.2,
        tools: Optional[List[str]] = None
    ):
        """Initialize the Coder agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            temperature: Temperature for responses (low for precise code)
            tools: Optional list of tools (defaults to coding tools)
        """
        if tools is None:
            tools = ["read_file", "write_file", "edit_file", "run_command"]
        
        super().__init__(
            name=name,
            model=model,
            temperature=temperature,
            tools=tools,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Coder agent."""
        return """You are an expert software developer. Your role is to:

1. Write clean, efficient, and maintainable code
2. Follow established patterns and conventions
3. Implement proper error handling and validation
4. Write self-documenting code with clear names
5. Consider performance and scalability

When writing code:
- Follow the project's coding style and conventions
- Use appropriate design patterns
- Add minimal but meaningful comments
- Handle edge cases and errors gracefully
- Write testable code with clear interfaces
- Consider security implications

Always explain your implementation choices briefly."""
    
    def implement_feature(self, specification: str, language: str = "python") -> str:
        """Implement a feature based on specification.
        
        Args:
            specification: Feature specification
            language: Programming language to use
            
        Returns:
            Implementation code with explanation
        """
        implementation_prompt = f"""
Implement this feature in {language}:
{specification}

Requirements:
1. Follow best practices for {language}
2. Include proper error handling
3. Make the code modular and reusable
4. Add type hints/annotations where appropriate
5. Consider edge cases

Provide the implementation with a brief explanation of design choices.
"""
        return self(implementation_prompt)
    
    def refactor_code(self, code: str, goals: List[str]) -> str:
        """Refactor existing code based on goals.
        
        Args:
            code: The code to refactor
            goals: List of refactoring goals
            
        Returns:
            Refactored code with explanation
        """
        goals_list = "\n".join([f"- {goal}" for goal in goals])
        refactor_prompt = f"""
Refactor this code:
```
{code}
```

Refactoring goals:
{goals_list}

Maintain functionality while improving:
1. Code structure and organization
2. Readability and maintainability
3. Performance where possible
4. Error handling
5. Code reusability

Explain the changes made and why.
"""
        return self(refactor_prompt)
    
    def fix_bug(self, code: str, bug_description: str, error_message: Optional[str] = None) -> str:
        """Fix a bug in the code.
        
        Args:
            code: The code with the bug
            bug_description: Description of the bug
            error_message: Optional error message
            
        Returns:
            Fixed code with explanation
        """
        bug_prompt = f"""
Fix this bug:
Bug description: {bug_description}
{f'Error message: {error_message}' if error_message else ''}

Code:
```
{code}
```

Please:
1. Identify the root cause
2. Fix the bug
3. Ensure no new bugs are introduced
4. Add any necessary validation
5. Explain the fix

Provide the corrected code and explanation.
"""
        return self(bug_prompt)
    
    def write_tests(self, code: str, framework: str = "pytest") -> str:
        """Write tests for given code.
        
        Args:
            code: The code to test
            framework: Testing framework to use
            
        Returns:
            Test code with coverage explanation
        """
        test_prompt = f"""
Write comprehensive tests for this code using {framework}:
```
{code}
```

Include:
1. Unit tests for all functions/methods
2. Edge case testing
3. Error condition testing
4. Integration tests if applicable
5. Test fixtures and mocks as needed

Aim for high code coverage with meaningful tests.
"""
        return self(test_prompt)
    
    def optimize_performance(self, code: str, constraints: Optional[List[str]] = None) -> str:
        """Optimize code for performance.
        
        Args:
            code: The code to optimize
            constraints: Optional list of constraints
            
        Returns:
            Optimized code with performance analysis
        """
        constraints_list = "\n".join([f"- {c}" for c in constraints]) if constraints else "None"
        optimize_prompt = f"""
Optimize this code for performance:
```
{code}
```

Constraints:
{constraints_list}

Focus on:
1. Time complexity improvements
2. Space complexity improvements
3. Reducing redundant operations
4. Better data structures
5. Caching opportunities

Provide optimized code with complexity analysis.
"""
        return self(optimize_prompt)