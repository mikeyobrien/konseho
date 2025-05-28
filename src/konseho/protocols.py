"""Core protocol definitions for konseho components.

This module defines the abstract interfaces (protocols) that all core components
should implement. Using protocols provides:
- Loose coupling between components
- Better testability through easy mocking
- Clear contracts for implementations
- Runtime type checking support
"""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class IAgent(Protocol):
    """Core agent interface for all agent implementations."""

    @property
    def name(self) -> str:
        """Agent's unique name."""
        ...

    @property
    def model(self) -> str:
        """Model identifier (e.g., 'claude-3-5-sonnet-20241022')."""
        ...

    async def work_on(self, task: str) -> str:
        """Process a task and return result.

        Args:
            task: The task description to process

        Returns:
            The agent's response as a string
        """
        ...

    def get_capabilities(self) -> dict[str, Any]:
        """Return agent capabilities and metadata.

        Returns:
            Dictionary containing agent capabilities
        """
        ...


@runtime_checkable
class IToolAgent(IAgent, Protocol):
    """Agent with tool execution capabilities."""

    async def work_on_with_tools(self, task: str, tools: list["ITool"]) -> str:
        """Process task using provided tools.

        Args:
            task: The task description to process
            tools: List of tools available to the agent

        Returns:
            The agent's response after potentially using tools
        """
        ...


@runtime_checkable
class IStep(Protocol):
    """Step execution interface for workflow steps."""

    @property
    def name(self) -> str:
        """Step name for identification."""
        ...

    async def execute(self, task: str, context: "IContext") -> "IStepResult":
        """Execute the step with given task and context.

        Args:
            task: The task to execute
            context: Shared context for the execution

        Returns:
            Step execution result
        """
        ...

    def validate(self) -> list[str]:
        """Validate step configuration.

        Returns:
            List of validation error messages (empty if valid)
        """
        ...


@runtime_checkable
class IStepResult(Protocol):
    """Result from step execution."""

    @property
    def output(self) -> str:
        """Main output from the step."""
        ...

    @property
    def metadata(self) -> dict[str, Any]:
        """Additional metadata about the execution."""
        ...

    @property
    def success(self) -> bool:
        """Whether the step executed successfully."""
        ...


@runtime_checkable
class IContext(Protocol):
    """Context management interface for sharing state."""

    def add(self, key: str, value: Any) -> None:
        """Add a key-value pair to context.

        Args:
            key: Context key
            value: Value to store
        """
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from context.

        Args:
            key: Context key
            default: Default value if key not found

        Returns:
            Stored value or default
        """
        ...

    def update(self, data: dict[str, Any]) -> None:
        """Update context with multiple key-value pairs.

        Args:
            data: Dictionary of updates
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """Export context as dictionary.

        Returns:
            Dictionary representation of context
        """
        ...

    def get_size(self) -> int:
        """Get context size in bytes/tokens.

        Returns:
            Size of context data
        """
        ...

    def clear(self) -> None:
        """Clear all context data."""
        ...


@runtime_checkable
class ITool(Protocol):
    """Tool interface for agent capabilities."""

    @property
    def name(self) -> str:
        """Tool name for identification."""
        ...

    @property
    def description(self) -> str:
        """Human-readable tool description."""
        ...

    async def execute(self, **kwargs) -> Any:
        """Execute tool with parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result
        """
        ...


@runtime_checkable
class IModelProvider(Protocol):
    """Interface for model/agent providers."""

    async def create_agent(self, name: str, model: str, **kwargs) -> IAgent:
        """Create an agent instance.

        Args:
            name: Agent name
            model: Model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            Created agent instance
        """
        ...

    async def list_models(self) -> list[str]:
        """List available models.

        Returns:
            List of model identifiers
        """
        ...

    def supports_streaming(self) -> bool:
        """Check if provider supports streaming responses.

        Returns:
            True if streaming is supported
        """
        ...


@runtime_checkable
class ISearchProvider(Protocol):
    """Interface for search providers."""

    async def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Execute a search query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of search results
        """
        ...

    @property
    def name(self) -> str:
        """Provider name."""
        ...

    def is_available(self) -> bool:
        """Check if provider is configured and available.

        Returns:
            True if provider can be used
        """
        ...


@runtime_checkable
class IExecutor(Protocol):
    """Interface for step executors."""

    async def execute_step(
        self, step: IStep, task: str, context: IContext
    ) -> IStepResult:
        """Execute a single step.

        Args:
            step: Step to execute
            task: Task description
            context: Execution context

        Returns:
            Step execution result
        """
        ...


@runtime_checkable
class ICouncil(Protocol):
    """Interface for council orchestrators."""

    @property
    def agents(self) -> list[IAgent]:
        """List of council agents."""
        ...

    @property
    def steps(self) -> list[IStep]:
        """List of execution steps."""
        ...

    async def convene(self, task: str) -> str:
        """Execute the council workflow.

        Args:
            task: Task to process

        Returns:
            Final council output
        """
        ...


@runtime_checkable
class IEventEmitter(Protocol):
    """Interface for event emission system."""

    def on(self, event: str, handler: Any) -> None:
        """Register an event handler.

        Args:
            event: Event name
            handler: Callback function
        """
        ...

    def emit(self, event: str, data: Any = None) -> None:
        """Emit an event with optional data.

        Args:
            event: Event name
            data: Optional event data
        """
        ...

    async def emit_async(self, event: str, data: Any = None) -> None:
        """Emit an event asynchronously.

        Args:
            event: Event name
            data: Optional event data
        """
        ...


@runtime_checkable
class IOutputManager(Protocol):
    """Interface for output management."""

    def save_formatted_output(
        self,
        task: str,
        result: Any,
        council_name: str = "council",
        metadata: dict[str, Any] | None = None,
    ) -> Any:
        """Save council output in formatted form.

        Args:
            task: The task that was executed
            result: The execution result
            council_name: Name of the council
            metadata: Additional metadata to save

        Returns:
            Path to saved output
        """
        ...

    def clean_old_outputs(self, max_age_days: int = 7) -> int:
        """Clean up old output files.

        Args:
            max_age_days: Maximum age of files to keep

        Returns:
            Number of files cleaned
        """
        ...


# Type aliases for migration support
AgentLike = IAgent | Any  # Any allows existing Agent class
StepLike = IStep | Any  # Any allows existing Step class
ContextLike = IContext | Any  # Any allows existing Context class
