"""Reviewer agent for code review and quality assurance."""

from typing import List, Optional, Dict
from strands import Agent


class ReviewerAgent(Agent):
    """Agent specialized in code review and quality assurance."""
    
    def __init__(
        self,
        name: str = "Reviewer",
        model: str = "gpt-4",
        temperature: float = 0.3,
        tools: Optional[List[str]] = None
    ):
        """Initialize the Reviewer agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            temperature: Temperature for responses (low for consistency)
            tools: Optional list of tools
        """
        if tools is None:
            tools = ["read_file", "search_files"]
        
        super().__init__(
            name=name,
            model=model,
            temperature=temperature,
            tools=tools,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Reviewer agent."""
        return """You are an expert code reviewer and quality assurance specialist. Your role is to:

1. Review code for correctness, efficiency, and maintainability
2. Identify bugs, security issues, and potential problems
3. Ensure code follows best practices and standards
4. Suggest improvements and optimizations
5. Verify test coverage and quality

When reviewing code:
- Check for logical errors and edge cases
- Verify proper error handling
- Assess code readability and documentation
- Look for security vulnerabilities
- Consider performance implications
- Ensure consistent style and conventions

Provide constructive feedback with specific suggestions."""
    
    def review_code(self, code: str, context: Optional[str] = None) -> str:
        """Perform a comprehensive code review.
        
        Args:
            code: The code to review
            context: Optional context about the code
            
        Returns:
            Detailed review with suggestions
        """
        review_prompt = f"""
Review this code:
{f'Context: {context}' if context else ''}
```
{code}
```

Please review for:
1. Correctness and logic errors
2. Code quality and maintainability
3. Performance considerations
4. Security vulnerabilities
5. Error handling
6. Code style and conventions
7. Documentation completeness

Provide:
- Overall assessment (Excellent/Good/Needs Work/Poor)
- Specific issues found
- Suggestions for improvement
- Positive aspects worth keeping
"""
        return self(review_prompt)
    
    def security_audit(self, code: str) -> str:
        """Perform a security audit of the code.
        
        Args:
            code: The code to audit
            
        Returns:
            Security audit results
        """
        security_prompt = f"""
Perform a security audit on this code:
```
{code}
```

Check for:
1. Input validation vulnerabilities
2. SQL injection risks
3. XSS vulnerabilities
4. Authentication/authorization issues
5. Sensitive data exposure
6. Insecure dependencies
7. Cryptographic weaknesses
8. Race conditions

For each issue found:
- Severity (Critical/High/Medium/Low)
- Description of vulnerability
- Potential impact
- Recommended fix
"""
        return self(security_prompt)
    
    def check_best_practices(self, code: str, language: str = "python") -> Dict[str, str]:
        """Check if code follows best practices.
        
        Args:
            code: The code to check
            language: Programming language
            
        Returns:
            Best practices assessment
        """
        practices_prompt = f"""
Check if this {language} code follows best practices:
```
{code}
```

Evaluate:
1. Naming conventions
2. Code organization
3. Design patterns usage
4. DRY principle
5. SOLID principles
6. Error handling patterns
7. Testing approach
8. Documentation standards

Rate each area and provide specific feedback.
"""
        result = self(practices_prompt)
        
        # Parse result into structured format
        # In real implementation, would parse the response
        return {"assessment": result}
    
    def suggest_refactoring(self, code: str) -> str:
        """Suggest refactoring opportunities.
        
        Args:
            code: The code to analyze
            
        Returns:
            Refactoring suggestions
        """
        refactor_prompt = f"""
Analyze this code for refactoring opportunities:
```
{code}
```

Look for:
1. Code duplication
2. Long methods/functions
3. Complex conditionals
4. Poor abstraction
5. Tight coupling
6. Missing design patterns
7. Performance bottlenecks

Provide specific refactoring suggestions with benefits.
"""
        return self(refactor_prompt)
    
    def review_tests(self, test_code: str, implementation_code: Optional[str] = None) -> str:
        """Review test code quality and coverage.
        
        Args:
            test_code: The test code to review
            implementation_code: Optional implementation being tested
            
        Returns:
            Test review results
        """
        test_review_prompt = f"""
Review this test code:
```
{test_code}
```

{f'Implementation being tested:\n```\n{implementation_code}\n```' if implementation_code else ''}

Evaluate:
1. Test coverage completeness
2. Edge case handling
3. Test isolation and independence
4. Mock/stub usage appropriateness
5. Test naming and organization
6. Assertion quality
7. Performance of tests

Identify gaps and suggest improvements.
"""
        return self(test_review_prompt)