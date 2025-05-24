# Konseho - Multi-Agent Council SDK

## Requirements Gathering Summary

### Core Concept
- **What**: An SDK built on top of Strands Agent SDK for creating multi-agent "councils"
- **Purpose**: Enable specialized agents to work together to accomplish common goals with better context management and improved outcomes

### Target Audience
- AI/ML developers building complex automation systems
- Organizations needing complex orchestration capabilities
- Expected technical expertise: Intermediate to advanced Python developers

### Pain Points Addressed
- Difficulty coordinating multiple specialized agents
- Context getting lost between different agents
- Complex orchestration code that must be written manually
- Lack of goal alignment between agents

### Scope & Implementation
- Python-based open source framework
- Includes interactive terminal chat interface
- Framework-first approach with UI component

### Core Features (MVP)
1. Council creation/configuration system
2. Context sharing/management between agents
3. Terminal chat interface for interaction

### Success Metrics
- Clear improvement in task completion (both alignment and speed) vs single agents
- Developers can spin up a functional council in less than 10 lines of code

## Strands SDK Research Summary

### Key Capabilities
- **Agent Creation**: Simple `Agent()` constructor with customizable prompts, tools, and models
- **Tool System**: `@tool` decorator for easy function integration
- **Multi-Agent Support**: "Agents as Tools" pattern - wrap specialized agents as callable functions
- **State Management**: Conversation history via `agent.messages`, supports persistence
- **Model Flexibility**: Works with multiple providers (Bedrock, OpenAI, Anthropic, etc.)

### Limitations for Council Systems
- No built-in inter-agent messaging (communication through orchestrator only)
- Stateless by default - requires explicit state management
- Single orchestrator pattern - no peer-to-peer communication
- Synchronous coordination - parallel execution needs custom implementation

### Design Implications
1. Use orchestrator agent as "council moderator" with specialist agents as "members"
2. Implement voting/consensus logic within orchestrator
3. Build custom async wrappers for parallel agent consultations
4. Create centralized state store for shared council knowledge
5. Use message history initialization to share context between agents

## Multi-Agent Coordination Patterns Research

### Key Findings
- **Voting vs Consensus**: Voting improves reasoning tasks by 13.2%, consensus better for knowledge tasks (+2.8%)
- **Agent Scaling**: More agents = better performance, but more debate rounds can decrease effectiveness
- **Modern Patterns**: All-Agents Drafting (+3.3%) and Collective Improvement (+7.4%) show promise

### Recommended MVP Pattern: Orchestrated Debate
1. **Moderator assigns tasks** to specialist agents
2. **Parallel proposal generation** from specialists
3. **Structured debate round** for critique/improvement
4. **Voting/consensus** mechanism
5. **Moderator synthesizes** final output with full context

### Benefits
- Combines orchestration with collective intelligence
- Natural fit with Strands' "agents as tools" pattern
- Measurable performance improvements
- Scales to multi-phase workflows

## Council Architecture Design

### Multi-Step Workflow Pattern
Councils can execute complex workflows through defined steps:

```python
# Example: Code Council with steps
council = Council(
    steps=[
        Step("explore", agents=[FileExplorer(), CodeAnalyzer()]),
        Step("plan", agents=[Architect(), TaskPlanner()]), 
        Step("code", agents=[Coder(), Reviewer()])
    ],
    workflow="sequential"  # or "iterative"
)

result = council.execute("Add authentication to the API")
```

### Key Components
1. **Step-Aware Moderator**: Manages workflow progression and context passing
2. **Specialized Step Agents**: Each step has agents optimized for that phase
3. **Context Accumulation**: Each step builds on previous findings
4. **Flexible Workflows**: Sequential, iterative, or conditional step execution

### Benefits
- Maintains <10 line council creation goal
- Scales from simple tasks to complex multi-step processes
- Clear separation of concerns per step
- Natural context flow between steps

## Detailed Architecture Design

### Core Classes & Interfaces

```python
# Base Council class
class Council:
    def __init__(self, steps=None, agents=None, workflow="sequential"):
        # Support both simple (agents only) and complex (steps) councils
        pass
    
    def execute(self, task: str) -> CouncilResult:
        # Main execution method
        pass

# Step definition
class Step:
    def __init__(self, name: str, agents: List[Agent], 
                 debate_rounds: int = 1, decision_method: str = "vote"):
        pass

# Council-aware agent wrapper
class CouncilAgent:
    def __init__(self, strands_agent: Agent, role: str):
        # Wraps Strands agent with council capabilities
        pass

# Shared context
class CouncilContext:
    def __init__(self):
        self.shared_memory = {}
        self.step_results = []
        self.decisions = []
```

### Communication Flow & Parallelization

```python
# Clear separation of step types
class Step:
    """Base step class"""
    def __init__(self, name: str):
        self.name = name

class ParallelStep(Step):
    """Agents work on different parts of the problem simultaneously"""
    def __init__(self, name: str, agents: Dict[str, Agent]):
        # agents = {"frontend": CodeAgent(), "backend": CodeAgent(), "tests": TestAgent()}
        super().__init__(name)
        self.agents = agents
        
    async def execute(self, task: str, context: CouncilContext):
        # Each agent works on their assigned domain
        results = await asyncio.gather(*[
            agent.work_on(f"{task} for {domain}", context)
            for domain, agent in self.agents.items()
        ])
        return self.synthesize(results)

class DebateStep(Step):
    """Agents propose competing solutions and debate"""
    def __init__(self, name: str, agents: List[Agent], rounds: int = 1):
        super().__init__(name)
        self.agents = agents
        self.rounds = rounds
        
    async def execute(self, task: str, context: CouncilContext):
        proposals = await self.gather_proposals(task, context)
        for _ in range(self.rounds):
            proposals = await self.debate_round(proposals)
        return self.vote(proposals)

class SplitStep(Step):
    """Automatically splits work based on strategy"""
    def __init__(self, name: str, agent_template: Agent, split_by: str = "auto"):
        # split_by: "files", "functions", "topics", "auto"
        super().__init__(name)
        self.agent_template = agent_template
        self.split_by = split_by
        
    async def execute(self, task: str, context: CouncilContext):
        # Analyze task and create agents dynamically
        work_items = await self.analyze_and_split(task, context)
        agents = [self.agent_template.clone() for _ in work_items]
        
        results = await asyncio.gather(*[
            agent.work_on(item, context)
            for agent, item in zip(agents, work_items)
        ])
        return self.merge(results)

# Usage examples
council = Council([
    # Parallel exploration by domain
    ParallelStep("explore", {
        "codebase": CodeExplorer(),
        "dependencies": DependencyAnalyzer(),
        "patterns": PatternFinder()
    }),
    
    # Debate on approach
    DebateStep("design", [Architect(), Designer(), Pragmatist()], rounds=2),
    
    # Auto-split implementation work
    SplitStep("implement", agent_template=Coder(), split_by="files"),
    
    # Single agent review
    Step("review", agents=[Reviewer()])
])
```

### Voting/Consensus Protocols

```python
class DecisionProtocol:
    @staticmethod
    def vote(proposals: List[Proposal]) -> Decision:
        # Simple majority voting
        votes = Counter(p.agent_id for p in proposals)
        return votes.most_common(1)[0]
    
    @staticmethod
    def weighted_vote(proposals: List[Proposal], weights: Dict) -> Decision:
        # Expertise-weighted voting
        pass
    
    @staticmethod
    def consensus(proposals: List[Proposal], threshold: float = 0.8) -> Decision:
        # Require threshold agreement
        pass
```

## API Design Summary

### Simple Usage (<10 lines)

```python
from konseho import Council, ParallelStep, DebateStep, SplitStep
from my_agents import Explorer, Planner, Coder, Reviewer

# Simple debate council
council = Council([
    DebateStep("solve", [Explorer(), Planner(), Coder()])
])
result = council.execute("Fix the authentication bug")

# Multi-step parallel council
council = Council([
    ParallelStep("explore", {
        "code": CodeExplorer(),
        "tests": TestAnalyzer(),
        "docs": DocReader()
    }),
    DebateStep("plan", [Architect(), Designer()], rounds=2),
    SplitStep("implement", Coder(), split_by="files"),
    Step("review", Reviewer())
])
result = council.execute("Add OAuth2 support")
```

### Core Design Principles
1. **Explicit Step Types**: Clear intent with ParallelStep, DebateStep, SplitStep
2. **Flexible Parallelization**: Domain-based dict or auto-splitting
3. **Natural Strands Integration**: Wraps Strands agents seamlessly
4. **Progressive Complexity**: Simple by default, powerful when needed

## Context Management Design

### Context Architecture

```python
class CouncilContext:
    """Manages shared state and knowledge across council execution"""
    
    def __init__(self, max_history: int = 100):
        # Core memory stores
        self.shared_memory = {}  # Key-value store for any data
        self.step_results = []   # Results from each step
        self.decisions = []      # Decision history with rationale
        
        # Message history for Strands compatibility
        self.messages = []       # Can initialize agents with this
        self.max_history = max_history
        
        # Working memory for current step
        self.current_step = None
        self.proposals = {}      # Agent proposals in current step
        self.critiques = {}      # Critiques in debate rounds
        
    def add_message(self, role: str, content: str):
        """Add message and manage history window"""
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_history:
            # Summarize old messages before dropping
            self.messages = self._summarize_and_truncate()
    
    def set(self, key: str, value: Any, scope: str = "global"):
        """Set context value with scope control"""
        if scope == "step":
            # Only visible within current step
            self.current_step[key] = value
        else:
            self.shared_memory[key] = value
    
    def get_step_context(self, step_name: str) -> Dict:
        """Get relevant context for a specific step"""
        return {
            "previous_results": self.step_results[-3:],  # Last 3 steps
            "shared_memory": self.shared_memory,
            "current_task": self.current_task,
            "messages": self._get_relevant_messages(step_name)
        }
    
    def fork_for_agent(self, agent_id: str) -> "AgentContext":
        """Create agent-specific view of context"""
        return AgentContext(
            parent=self,
            agent_id=agent_id,
            read_only=["decisions", "step_results"],
            read_write=["proposals", "shared_memory"]
        )

class AgentContext:
    """Agent-specific view with access control"""
    
    def __init__(self, parent: CouncilContext, agent_id: str, 
                 read_only: List[str], read_write: List[str]):
        self.parent = parent
        self.agent_id = agent_id
        self.read_only = read_only
        self.read_write = read_write
        
    def read(self, key: str) -> Any:
        # Can read from allowed stores
        if key in self.read_only or key in self.read_write:
            return getattr(self.parent, key)
        raise PermissionError(f"Agent {self.agent_id} cannot read {key}")
```

### Context Flow Patterns

```python
class ContextManager:
    """Manages context flow between steps and agents"""
    
    def __init__(self, summarizer: Agent = None):
        self.summarizer = summarizer or DefaultSummarizer()
        
    async def prepare_step_context(self, step: Step, context: CouncilContext) -> Dict:
        """Prepare context for step execution"""
        
        if isinstance(step, ParallelStep):
            # Each parallel agent gets filtered context
            contexts = {}
            for domain, agent in step.agents.items():
                contexts[domain] = {
                    "domain": domain,
                    "shared": context.shared_memory,
                    "previous": context.step_results[-1] if context.step_results else None,
                    # Domain-specific context filtering
                    "relevant_files": self._filter_by_domain(context, domain)
                }
            return contexts
            
        elif isinstance(step, DebateStep):
            # All agents get same full context for fair debate
            return {
                "full_history": context.messages[-20:],
                "shared_memory": context.shared_memory,
                "debate_topic": context.current_task
            }
            
        elif isinstance(step, SplitStep):
            # Prepare for dynamic work distribution
            return {
                "task": context.current_task,
                "available_work": await self._analyze_splittable_work(context),
                "shared_memory": context.shared_memory
            }
    
    async def merge_step_results(self, results: List[Any], 
                                 step: Step, context: CouncilContext):
        """Merge results back into context"""
        
        if isinstance(step, ParallelStep):
            # Merge domain-specific results
            merged = {}
            for domain, result in results.items():
                merged[domain] = result
                # Update shared memory with domain findings
                context.set(f"{step.name}_{domain}_result", result)
                
        elif isinstance(step, DebateStep):
            # Store winning proposal and rationale
            context.decisions.append({
                "step": step.name,
                "winner": results["winner"],
                "rationale": results["rationale"],
                "alternatives": results["alternatives"]
            })
            
        # Summarize if getting too large
        if len(str(context.shared_memory)) > 10000:
            summary = await self.summarizer.summarize(context.shared_memory)
            context.set("memory_summary", summary)
```

### Context Persistence & Initialization

```python
class CouncilContextSerializer:
    """Save and restore context between sessions"""
    
    @staticmethod
    def to_json(context: CouncilContext) -> str:
        return json.dumps({
            "shared_memory": context.shared_memory,
            "messages": context.messages,
            "step_results": context.step_results,
            "decisions": context.decisions
        }, indent=2)
    
    @staticmethod
    def from_json(json_str: str) -> CouncilContext:
        data = json.loads(json_str)
        context = CouncilContext()
        context.shared_memory = data["shared_memory"]
        context.messages = data["messages"]
        context.step_results = data["step_results"]
        context.decisions = data["decisions"]
        return context

# Usage with Strands agents
class CouncilAgent:
    def __init__(self, strands_agent: Agent, context: AgentContext):
        # Initialize Strands agent with context history
        self.agent = strands_agent
        self.agent.messages = context.parent.messages.copy()
        self.context = context
        
    async def work_on(self, task: str) -> str:
        # Include context in prompts
        enhanced_task = f"""
        Task: {task}
        
        Context:
        - Previous findings: {self.context.read('step_results')[-1]}
        - Shared knowledge: {self.context.read('shared_memory')}
        """
        
        response = await self.agent(enhanced_task)
        
        # Update context with findings
        self.context.parent.add_message("assistant", response)
        
        return response
```

## Additional P0 Components

### Error Handling & Recovery

```python
class StepExecutionError(Exception):
    """Captures step-level failures with context"""
    def __init__(self, step_name: str, agent_id: str, error: Exception):
        self.step_name = step_name
        self.agent_id = agent_id
        self.original_error = error
        super().__init__(f"Step '{step_name}' failed in agent '{agent_id}': {error}")

class Council:
    def __init__(self, steps: List[Step], error_strategy: str = "halt"):
        """
        error_strategy options:
        - "halt": Stop execution on first error
        - "continue": Skip failed step, continue with degraded results
        - "retry": Retry failed steps with exponential backoff
        - "fallback": Use simpler fallback agent
        """
        self.steps = steps
        self.error_strategy = error_strategy
        self.retry_attempts = 3
        
    async def handle_error(self, error: StepExecutionError, context: CouncilContext):
        if self.error_strategy == "retry":
            for attempt in range(self.retry_attempts):
                try:
                    # Retry with backoff
                    await asyncio.sleep(2 ** attempt)
                    return await self.retry_step(error.step_name, context)
                except Exception:
                    continue
        elif self.error_strategy == "continue":
            # Log error and provide degraded result
            context.step_results.append({
                "step": error.step_name,
                "status": "failed",
                "error": str(error),
                "fallback": "skipped"
            })
```

### Terminal Chat Interface

```python
class CouncilChat:
    """Interactive terminal interface for council interactions"""
    
    def __init__(self, council: Council, verbose: bool = True):
        self.council = council
        self.context = CouncilContext()
        self.verbose = verbose
        self.history = []
        
    async def chat(self):
        """Main chat loop with real-time agent deliberations"""
        print("Council Chat initialized. Type 'exit' to quit, 'help' for commands.")
        
        while True:
            user_input = input("\n🤔 You: ")
            
            if user_input.lower() == 'exit':
                break
            elif user_input.lower() == 'help':
                self.show_help()
                continue
            elif user_input.lower() == 'history':
                self.show_history()
                continue
                
            # Stream execution with live updates
            print("\n🏛️ Council deliberating...\n")
            
            async for event in self.council.stream_execute(user_input, self.context):
                if self.verbose:
                    self.display_event(event)
                    
            # Display final result
            result = await self.council.get_result()
            print(f"\n✅ Council Decision: {result.final_answer}")
            
            if self.verbose:
                print(f"\n📊 Explanation: {result.explain()}")
                
            self.history.append((user_input, result))
    
    def display_event(self, event: 'CouncilEvent'):
        """Pretty-print council events"""
        if event.type == "step_started":
            print(f"📍 Starting {event.step.name} step...")
        elif event.type == "agent_working":
            print(f"   🤖 [{event.agent_id}] working on: {event.task[:50]}...")
        elif event.type == "proposal_made":
            print(f"   💡 [{event.agent_id}] proposed: {event.proposal[:100]}...")
        elif event.type == "debate_round":
            print(f"   ⚔️  Debate round {event.round_num} in progress...")
        elif event.type == "decision_made":
            print(f"   ✓ Decision made via {event.method}")
```

### Observability & Events

```python
from enum import Enum
from dataclasses import dataclass
from typing import Any, Callable, Optional

class EventType(Enum):
    COUNCIL_STARTED = "council_started"
    STEP_STARTED = "step_started"
    AGENT_WORKING = "agent_working"
    PROPOSAL_MADE = "proposal_made"
    DEBATE_ROUND = "debate_round"
    DECISION_MADE = "decision_made"
    STEP_COMPLETED = "step_completed"
    COUNCIL_COMPLETED = "council_completed"
    ERROR_OCCURRED = "error_occurred"

@dataclass
class CouncilEvent:
    type: EventType
    timestamp: float
    step_name: Optional[str] = None
    agent_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    # Convenience properties
    @property
    def task(self) -> Optional[str]:
        return self.data.get("task") if self.data else None
    
    @property
    def proposal(self) -> Optional[str]:
        return self.data.get("proposal") if self.data else None

class ObservableCouncil(Council):
    """Council with event streaming capabilities"""
    
    def __init__(self, steps: List[Step], on_event: Optional[Callable] = None):
        super().__init__(steps)
        self.event_handlers = [on_event] if on_event else []
        
    def add_observer(self, handler: Callable):
        self.event_handlers.append(handler)
        
    async def emit_event(self, event: CouncilEvent):
        for handler in self.event_handlers:
            if asyncio.iscoroutinefunction(handler):
                await handler(event)
            else:
                handler(event)
                
    async def stream_execute(self, task: str, context: CouncilContext):
        """Execute with event streaming"""
        await self.emit_event(CouncilEvent(
            type=EventType.COUNCIL_STARTED,
            timestamp=time.time(),
            data={"task": task}
        ))
        
        for step in self.steps:
            await self.emit_event(CouncilEvent(
                type=EventType.STEP_STARTED,
                timestamp=time.time(),
                step_name=step.name
            ))
            
            # Execute step with events
            result = await step.execute_with_events(task, context, self.emit_event)
            
            await self.emit_event(CouncilEvent(
                type=EventType.STEP_COMPLETED,
                timestamp=time.time(),
                step_name=step.name,
                data={"result": result}
            ))
```

### Result Structure

```python
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class StepResult:
    step_name: str
    status: str  # "success", "failed", "skipped"
    output: Any
    execution_time: float
    agent_contributions: Dict[str, str]  # agent_id -> their contribution

@dataclass
class Decision:
    step_name: str
    method: str  # "vote", "consensus", "synthesis"
    winner: str
    rationale: str
    alternatives: List[Dict[str, Any]]
    vote_details: Optional[Dict[str, int]] = None

@dataclass
class CouncilResult:
    """Complete result of council execution"""
    final_answer: str
    step_results: List[StepResult]
    decisions: List[Decision]
    total_execution_time: float
    success: bool
    error: Optional[str] = None
    
    def explain(self) -> str:
        """Human-readable explanation of how council reached decision"""
        explanation = f"Council completed in {self.total_execution_time:.2f}s\n\n"
        
        for i, (step_result, decision) in enumerate(zip(self.step_results, self.decisions)):
            explanation += f"Step {i+1}: {step_result.step_name}\n"
            explanation += f"  Status: {step_result.status}\n"
            
            if decision:
                explanation += f"  Decision method: {decision.method}\n"
                explanation += f"  Rationale: {decision.rationale}\n"
                
            if step_result.agent_contributions:
                explanation += "  Agent contributions:\n"
                for agent, contribution in step_result.agent_contributions.items():
                    explanation += f"    - {agent}: {contribution[:100]}...\n"
                    
            explanation += "\n"
            
        explanation += f"Final Answer: {self.final_answer}"
        
        return explanation
    
    def to_json(self) -> str:
        """Serialize result for storage/API responses"""
        return json.dumps({
            "final_answer": self.final_answer,
            "success": self.success,
            "execution_time": self.total_execution_time,
            "steps": [asdict(step) for step in self.step_results],
            "decisions": [asdict(decision) for decision in self.decisions],
            "error": self.error
        }, indent=2)
```

## Human-in-the-Loop Design

### Human Agent Integration

```python
class HumanAgent:
    """Human participant in council deliberations"""
    
    def __init__(self, name: str = "Human", role: str = "reviewer"):
        self.name = name
        self.role = role
        self.interface = HumanInterface()
        
    async def work_on(self, task: str, context: CouncilContext) -> str:
        """Present task to human and get response"""
        # Show context to human
        await self.interface.show_context(task, context)
        
        # Get human input with timeout
        response = await self.interface.get_input(
            prompt=f"[{self.role}] Your input on: {task}",
            timeout=300  # 5 minute timeout
        )
        
        return response
        
    async def review_proposal(self, proposal: str) -> Dict[str, Any]:
        """Human reviews and rates proposal"""
        return await self.interface.review(
            proposal,
            options=["approve", "reject", "modify"]
        )

class HumanInterface:
    """Terminal interface for human interaction"""
    
    async def show_context(self, task: str, context: CouncilContext):
        """Display relevant context to human"""
        print("\n" + "="*50)
        print(f"🤝 Human input requested for: {task}")
        print("="*50)
        
        # Show previous step results
        if context.step_results:
            print("\n📋 Previous findings:")
            for result in context.step_results[-2:]:
                print(f"  - {result.step_name}: {result.output[:100]}...")
                
        # Show other agents' proposals if in debate
        if context.proposals:
            print("\n💭 Other agents' proposals:")
            for agent_id, proposal in context.proposals.items():
                print(f"  [{agent_id}]: {proposal[:150]}...")
                
    async def get_input(self, prompt: str, timeout: int) -> str:
        """Get input with async timeout"""
        print(f"\n{prompt}")
        
        # Start async input with timeout
        try:
            return await asyncio.wait_for(
                self._async_input("> "),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            print("\n⏰ Timeout - using default response")
            return "No human input provided within timeout"
            
    async def _async_input(self, prompt: str) -> str:
        """Non-blocking input"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, input, prompt)
```

### Human-Enabled Council Patterns

```python
# 1. Human as Reviewer (Quality Gate)
council = Council([
    DebateStep("analyze", [Analyzer1(), Analyzer2()]),
    Step("human_review", HumanAgent(role="reviewer")),  # Human approves/rejects
    SplitStep("implement", Coder(), split_by="approved_items")
])

# 2. Human as Specialist (Domain Expert)  
council = Council([
    ParallelStep("research", {
        "technical": TechAnalyzer(),
        "business": BusinessAnalyzer(),
        "legal": HumanAgent(role="legal_expert")  # Human provides legal input
    }),
    DebateStep("synthesize", [Synthesizer()])
])

# 3. Human as Tie-Breaker (Decision Maker)
class HumanTieBreakerStep(DebateStep):
    def __init__(self, name: str, agents: List[Agent], human: HumanAgent):
        super().__init__(name, agents)
        self.human = human
        
    async def make_decision(self, proposals: List[Proposal]) -> Decision:
        # Try normal voting
        votes = self.vote(proposals)
        
        if self.is_tie(votes):
            # Human breaks the tie
            print("\n🤔 Tie detected - human decision needed")
            decision = await self.human.review_proposal(proposals)
            return Decision(
                method="human_tiebreak",
                winner=decision["selected"],
                rationale=decision["reason"]
            )
        
        return super().make_decision(proposals)

# 4. Human as Validator (Safety Check)
council = Council([
    DebateStep("generate", [Creator1(), Creator2()]),
    Step("safety_check", HumanAgent(role="safety_validator")),
    Step("execute", Executor())
])
```

### Interactive Council Modes

```python
class InteractiveCouncil(Council):
    """Council with human interaction points"""
    
    def __init__(self, steps: List[Step], interaction_mode: str = "checkpoint"):
        """
        interaction_mode:
        - "checkpoint": Human reviews at key decision points
        - "continuous": Human can intervene at any time  
        - "approval": Human must approve critical steps
        """
        super().__init__(steps)
        self.interaction_mode = interaction_mode
        self.human = HumanAgent(role="supervisor")
        
    async def execute(self, task: str, context: CouncilContext):
        for step in self.steps:
            # Pre-step human checkpoint
            if self.should_checkpoint(step):
                approval = await self.human.review_proposal(
                    f"About to execute: {step.name}"
                )
                if approval["result"] == "skip":
                    continue
                    
            # Execute step with potential interruption
            if self.interaction_mode == "continuous":
                result = await self.execute_with_interruption(step, task, context)
            else:
                result = await step.execute(task, context)
                
            # Post-step review for critical steps
            if step.critical and self.interaction_mode == "approval":
                approval = await self.human.review_proposal(result)
                if approval["result"] == "reject":
                    # Rollback or retry
                    result = await self.handle_rejection(step, context)
                    
            context.step_results.append(result)
```

### Human-Friendly Event Display

```python
class HumanCouncilChat(CouncilChat):
    """Enhanced chat for human participation"""
    
    def display_event(self, event: CouncilEvent):
        # Special formatting for human-relevant events
        if event.type == EventType.HUMAN_INPUT_REQUESTED:
            print("\n" + "🟡"*25)
            print("🤝 YOUR INPUT NEEDED")
            print("🟡"*25)
            
        elif event.type == EventType.WAITING_FOR_HUMAN:
            # Show spinner while waiting
            self.show_waiting_animation()
            
        elif event.type == EventType.HUMAN_DECISION_MADE:
            print(f"\n✅ Human decision: {event.data['decision']}")
            
        else:
            super().display_event(event)
            
    def show_waiting_animation(self):
        """Show that we're waiting for human"""
        frames = ["⏳", "⌛", "⏳", "⌛"]
        for frame in itertools.cycle(frames):
            print(f"\r{frame} Waiting for human input...", end="", flush=True)
            time.sleep(0.5)
```

### Usage Example

```
🤔 You: Review and fix the security vulnerabilities in our auth system

🏛️ Council deliberating...

📍 Starting analyze step...
   🤖 [SecurityScanner] working on: Scanning for vulnerabilities...
   🤖 [CodeAnalyzer] working on: Analyzing auth flow...
   
🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡
🤝 YOUR INPUT NEEDED
🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡🟡

[security_expert] Your input on: Review found vulnerabilities

📋 Previous findings:
  - analyze: Found SQL injection risk in login endpoint...

> I confirm the SQL injection risk. Also check for timing attacks in password comparison.

✅ Human decision: Additional vulnerability identified

📍 Starting fix step...
   🤖 [Coder] working on: Implementing security fixes...
   
🤝 Human input requested for: Approve security fixes

💭 Other agents' proposals:
  [Coder]: Use parameterized queries and constant-time comparison...

[safety_validator] Your input on: Approve implementation
> approve - looks good, but add rate limiting too

✅ Council Decision: Security vulnerabilities fixed with human-approved implementation including SQL injection prevention, timing attack mitigation, and rate limiting.
```

This design enables:
1. **Flexible human roles** - Expert, reviewer, decision maker
2. **Multiple interaction patterns** - Continuous, checkpoint, approval
3. **Async human input** - Non-blocking with timeouts
4. **Clear context** - Humans see relevant information
5. **Natural integration** - Humans are just special agents

## Next Steps
1. ~~Research Strands Agent SDK capabilities and architecture~~ ✓
2. ~~Research multi-agent coordination patterns based on Strands capabilities~~ ✓
3. ~~Define council architecture and communication protocols~~ ✓
4. ~~Design simple API for council creation~~ ✓
5. Create detailed implementation plan