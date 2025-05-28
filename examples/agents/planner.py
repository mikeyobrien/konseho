"""Planner agent for creating implementation plans and strategies."""


from strands import Agent


class PlannerAgent(Agent):
    """Agent specialized in planning and strategizing implementations."""
    
    def __init__(
        self,
        name: str = "Planner",
        model: str = "gpt-4",
        temperature: float = 0.5,
        tools: list[str] | None = None
    ):
        """Initialize the Planner agent.
        
        Args:
            name: Agent name
            model: LLM model to use
            temperature: Temperature for responses (balanced for creativity)
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
        """Get the system prompt for the Planner agent."""
        return """You are an expert software architect and implementation planner. Your role is to:

1. Create detailed implementation plans
2. Break down complex tasks into manageable steps
3. Identify potential challenges and solutions
4. Consider best practices and design patterns
5. Estimate effort and complexity

When creating plans:
- Start with clear objectives and success criteria
- Break down into logical phases or milestones
- Identify dependencies between tasks
- Consider edge cases and error handling
- Suggest testing strategies
- Provide realistic time estimates

Always structure plans clearly with priorities and dependencies marked."""
    
    def create_plan(self, task: str, context: str | None = None) -> str:
        """Create an implementation plan for a task.
        
        Args:
            task: The task to plan for
            context: Optional context about the project
            
        Returns:
            Detailed implementation plan
        """
        planning_prompt = f"""
Task: {task}
{f'Context: {context}' if context else ''}

Create a detailed implementation plan including:
1. Objectives and success criteria
2. Step-by-step implementation approach
3. Required components and modifications
4. Potential challenges and mitigation strategies
5. Testing approach
6. Estimated effort for each step

Format as a structured plan with clear phases.
"""
        return self(planning_prompt)
    
    def identify_risks(self, plan: str) -> str:
        """Identify risks in an implementation plan.
        
        Args:
            plan: The implementation plan to analyze
            
        Returns:
            Risk analysis with mitigation strategies
        """
        risk_prompt = f"""
Analyze this implementation plan for risks:
{plan}

Identify:
1. Technical risks (compatibility, performance, etc.)
2. Integration risks (breaking changes, dependencies)
3. Timeline risks (complexity, unknowns)
4. Quality risks (testing gaps, edge cases)

For each risk, provide:
- Severity (High/Medium/Low)
- Probability (High/Medium/Low)
- Mitigation strategy
- Contingency plan
"""
        return self(risk_prompt)
    
    def prioritize_tasks(self, tasks: list[str]) -> str:
        """Prioritize a list of tasks.
        
        Args:
            tasks: List of tasks to prioritize
            
        Returns:
            Prioritized task list with reasoning
        """
        task_list = "\n".join([f"- {task}" for task in tasks])
        priority_prompt = f"""
Prioritize these tasks:
{task_list}

Consider:
1. Dependencies between tasks
2. Business value and impact
3. Technical complexity
4. Risk reduction
5. Quick wins vs. long-term benefits

Provide:
1. Prioritized list (highest to lowest)
2. Reasoning for each priority
3. Suggested groupings or parallel work
4. Critical path identification
"""
        return self(priority_prompt)
    
    def estimate_effort(self, task: str, team_size: int = 1) -> str:
        """Estimate effort for a task.
        
        Args:
            task: The task to estimate
            team_size: Number of developers
            
        Returns:
            Effort estimation with breakdown
        """
        estimation_prompt = f"""
Estimate effort for: {task}
Team size: {team_size} developer(s)

Provide:
1. Overall time estimate (hours/days/weeks)
2. Breakdown by subtask
3. Assumptions made
4. Factors that could affect estimates
5. Confidence level (High/Medium/Low)
6. Recommendations for reducing effort

Consider complexity, testing, code review, and documentation time.
"""
        return self(estimation_prompt)