"""Explorer agent for codebase analysis and exploration."""

from typing import List, Optional
from strands import Agent


class ExplorerAgent(Agent):
    """Agent specialized in exploring and understanding codebases."""
    
    def __init__(
        self,
        name: str = "Explorer",
        model: str = "gpt-4",
        temperature: float = 0.3,
        tools: Optional[List[str]] = None
    ):
        """Initialize the Explorer agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            temperature: Temperature for responses (lower = more focused)
            tools: Optional list of tools (defaults to exploration tools)
        """
        if tools is None:
            tools = ["read_file", "search_files", "list_directory"]
        
        super().__init__(
            name=name,
            model=model,
            temperature=temperature,
            tools=tools,
            system_prompt=self._get_system_prompt()
        )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Explorer agent."""
        return """You are an expert code explorer and analyzer. Your role is to:

1. Understand project structure and architecture
2. Identify key components and their relationships
3. Find relevant code sections for given tasks
4. Analyze dependencies and interactions
5. Document findings clearly and concisely

When exploring code:
- Start with high-level structure (directories, main files)
- Identify entry points and core modules
- Note important patterns and conventions
- Look for configuration files and documentation
- Map out the flow of data and control

Always provide clear, structured summaries of your findings."""
    
    def explore_project(self, task: str) -> str:
        """Explore the project for a specific task.
        
        Args:
            task: The exploration task or question
            
        Returns:
            Structured findings from the exploration
        """
        exploration_prompt = f"""
Exploration Task: {task}

Please explore the codebase to understand:
1. Relevant files and directories
2. Key components involved
3. Current implementation (if any)
4. Potential areas of impact

Provide a structured summary of findings.
"""
        return self(exploration_prompt)
    
    def analyze_dependencies(self, component: str) -> str:
        """Analyze dependencies for a specific component.
        
        Args:
            component: The component to analyze
            
        Returns:
            Dependency analysis results
        """
        analysis_prompt = f"""
Analyze dependencies for: {component}

Please identify:
1. Direct dependencies (imports, includes)
2. Indirect dependencies (through other modules)
3. Dependents (what depends on this component)
4. External library dependencies
5. Potential circular dependencies

Format as a clear dependency tree or list.
"""
        return self(analysis_prompt)
    
    def find_similar_code(self, pattern: str) -> str:
        """Find similar code patterns in the codebase.
        
        Args:
            pattern: The code pattern or example to search for
            
        Returns:
            Locations and examples of similar code
        """
        search_prompt = f"""
Find similar code to: {pattern}

Search for:
1. Similar function signatures
2. Similar logic patterns
3. Similar data structures
4. Similar naming conventions

Return specific file locations and code snippets.
"""
        return self(search_prompt)