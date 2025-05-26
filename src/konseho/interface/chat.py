"""Terminal chat interface for councils."""

from typing import Optional, Dict, Any
import asyncio
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    

class ChatInterface:
    """Terminal interface for interacting with councils."""
    
    def __init__(self, use_rich: bool = True, save_outputs: bool = False, output_dir: Optional[str] = None):
        """Initialize chat interface.
        
        Args:
            use_rich: Whether to use rich for formatting (fallback to basic if not available)
            save_outputs: Whether to save council outputs
            output_dir: Directory for saving outputs
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.save_outputs = save_outputs
        self.output_dir = output_dir
        if self.use_rich:
            self.console = Console()
        
        self._event_log = []
    
    def display_welcome(self) -> None:
        """Display welcome message."""
        if self.use_rich:
            self.console.print(
                Panel.fit(
                    "[bold cyan]Welcome to Konseho Council[/bold cyan]\n"
                    "Multi-agent collaboration framework",
                    border_style="cyan"
                )
            )
        else:
            print("=" * 50)
            print("Welcome to Konseho Council")
            print("Multi-agent collaboration framework")
            print("=" * 50)
    
    def _display_step_result(self, step_result: Any) -> None:
        """Display the result of a single step."""
        try:
            # For debate step results
            if isinstance(step_result, dict) and 'winner' in step_result:
                winner = step_result.get('winner', 'No winner selected')
                proposals = step_result.get('proposals', {})
                votes = step_result.get('votes', {})
                
                if self.use_rich:
                    self.console.print("\n[bold cyan]Council Debate Results:[/bold cyan]")
                    
                    # Extract proposals into a list format
                    proposal_list = []
                    for key, value in proposals.items():
                        agent_name = key.split('_round_')[0] if '_round_' in key else key
                        proposal_list.append({'agent': agent_name, 'text': value})
                    
                    # Display all proposals  
                    self.console.print("\n[bold]All Proposals:[/bold]")
                    for proposal in proposal_list:
                        agent_name = proposal.get('agent', 'Unknown')
                        text = proposal.get('text', 'No text provided')
                        vote_count = votes.get(agent_name, 0)
                        
                        # Truncate long texts but show more than before
                        display_text = text[:800] + "..." if len(text) > 800 else text
                        
                        self.console.print(f"\n[yellow]→ {agent_name}[/yellow] (Votes: {vote_count})")
                        self.console.print(Panel(display_text, border_style="yellow"))
                    
                    # Display winner - NEVER truncate
                    self.console.print("\n[bold green]✓ Winner:[/bold green]")
                    self.console.print(Panel(winner, border_style="green"))
                else:
                    print("\nCouncil Debate Results:")
                    print("=" * 70)
                    
                    # Extract and display proposals
                    proposal_list = []
                    for key, value in proposals.items():
                        agent_name = key.split('_round_')[0] if '_round_' in key else key
                        proposal_list.append({'agent': agent_name, 'text': value})
                    
                    print("\nAll Proposals:")
                    for proposal in proposal_list:
                        agent_name = proposal.get('agent', 'Unknown')
                        text = proposal.get('text', 'No text provided')
                        vote_count = votes.get(agent_name, 0)
                        
                        print(f"\n→ {agent_name} (Votes: {vote_count})")
                        print("-" * 50)
                        display_text = text[:800] + "..." if len(text) > 800 else text
                        print(display_text)
                    
                    # Display winner - NEVER truncate
                    print("\n✓ Winner:")
                    print("=" * 50)
                    print(winner)
                    print("=" * 70)
            
            # For parallel step results
            elif isinstance(step_result, dict) and ('results' in step_result or 'parallel_results' in step_result):
                results_key = 'parallel_results' if 'parallel_results' in step_result else 'results'
                parallel_results = step_result[results_key]
                
                if self.use_rich:
                    self.console.print("\n[bold cyan]Parallel Execution Results:[/bold cyan]")
                    for agent_name, agent_result in parallel_results.items():
                        self.console.print(f"\n[yellow]→ {agent_name}:[/yellow]")
                        # Extract text content from strands agent response format
                        if isinstance(agent_result, dict) and 'content' in agent_result:
                            content = agent_result['content']
                            if isinstance(content, list) and content and isinstance(content[0], dict) and 'text' in content[0]:
                                text = content[0]['text']
                            else:
                                text = str(content)
                        else:
                            text = str(agent_result)
                        # Display full content without truncation
                        self.console.print(Panel(text, border_style="yellow"))
                else:
                    print("\nParallel Execution Results:")
                    print("=" * 70)
                    for agent_name, agent_result in parallel_results.items():
                        print(f"\n→ {agent_name}:")
                        print("-" * 50)
                        # Extract text content
                        if isinstance(agent_result, dict) and 'content' in agent_result:
                            content = agent_result['content']
                            if isinstance(content, list) and content and isinstance(content[0], dict) and 'text' in content[0]:
                                text = content[0]['text']
                            else:
                                text = str(content)
                        else:
                            text = str(agent_result)
                        print(text)
                    print("=" * 70)
            
            # For other step results
            else:
                if self.use_rich:
                    self.console.print("\n[bold]Step Result:[/bold]")
                    display_text = str(step_result)[:1000] + "..." if len(str(step_result)) > 1000 else str(step_result)
                    self.console.print(Panel(display_text, border_style="blue"))
                else:
                    print("\nStep Result:")
                    print("-" * 50)
                    display_text = str(step_result)[:1000] + "..." if len(str(step_result)) > 1000 else str(step_result)
                    print(display_text)
                    print("-" * 50)
                    
        except Exception as e:
            # Handle display errors gracefully
            if self.use_rich:
                self.console.print(f"[bold red]Error displaying step result:[/bold red] {str(e)}")
            else:
                print(f"Error displaying step result: {str(e)}")
    
    def display_event(self, event: str, data: Dict[str, Any]) -> None:
        """Display an event in the interface."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._event_log.append({"time": timestamp, "event": event, "data": data})
        
        if self.use_rich:
            if event == "council:start":
                self.console.print(f"\n[bold green]▶ Starting Council:[/bold green] {data.get('council', 'Unknown')}")
                self.console.print(f"[dim]Task: {data.get('task', 'No task')}[/dim]")
            elif event == "step:start":
                self.console.print(f"\n[yellow]→ Step {data.get('step', '?')}:[/yellow] {data.get('type', 'Unknown')}")
            elif event == "step:complete":
                self.console.print(f"[green]✓ Step completed[/green]")
                # Display step results immediately
                if 'result' in data:
                    self._display_step_result(data['result'])
            elif event == "council:complete":
                self.console.print(f"\n[bold green]✓ Council completed successfully[/bold green]")
            elif event.endswith(":error"):
                self.console.print(f"[bold red]✗ Error:[/bold red] {data.get('error', 'Unknown error')}")
        else:
            if event == "step:complete" and 'result' in data:
                print(f"[{timestamp}] Step completed")
                self._display_step_result(data['result'])
            else:
                print(f"[{timestamp}] {event}: {data}")
    
    def display_result(self, result: Dict[str, Any]) -> None:
        """Display final result."""
        try:
            # Extract the actual result from the council execution
            if 'results' in result:
                # This is the council result format
                step_results = result['results']
                if step_results:
                    # Display ALL step results, not just the first one
                    for step_key in sorted(step_results.keys()):
                        step_result = step_results[step_key]
                        
                        # Display each step's result using the existing _display_step_result method
                        if self.use_rich:
                            self.console.print(f"\n[bold cyan]Results from {step_key}:[/bold cyan]")
                        else:
                            print(f"\nResults from {step_key}:")
                        
                        self._display_step_result(step_result)
                    
                    return
            
            # Fallback to showing the full result if structure is different
            if self.use_rich:
                self.console.print("\n[bold]Final Result:[/bold]")
                self.console.print(Panel(str(result)[:1000], border_style="green"))
            else:
                print("\nFinal Result:")
                print("-" * 50)
                print(str(result)[:1000])
                print("-" * 50)
                
        except Exception as e:
            # Handle any display errors gracefully
            if self.use_rich:
                self.console.print(f"[bold red]Error displaying result:[/bold red] {str(e)}")
            else:
                print(f"Error displaying result: {str(e)}")
    
    async def interactive_session(self, council) -> None:
        """Run an interactive session with a council."""
        self.display_welcome()
        
        # Subscribe to council events
        if hasattr(council, '_event_emitter'):
            council._event_emitter.on("council:start", lambda e, d: self.display_event(e, d))
            council._event_emitter.on("step:start", lambda e, d: self.display_event(e, d))
            council._event_emitter.on("step:complete", lambda e, d: self.display_event(e, d))
            council._event_emitter.on("council:complete", lambda e, d: self.display_event(e, d))
            council._event_emitter.on("council:error", lambda e, d: self.display_event(e, d))
        
        while True:
            try:
                # Get user input
                if self.use_rich:
                    task = self.console.input("\n[bold cyan]Enter task (or 'quit' to exit):[/bold cyan] ")
                else:
                    task = input("\nEnter task (or 'quit' to exit): ")
                
                if task.lower() in ['quit', 'exit', 'q']:
                    break
                
                # Execute council
                result = await council.execute(task)
                self.display_result(result)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                if self.use_rich:
                    self.console.print(f"[bold red]Error:[/bold red] {e}")
                else:
                    print(f"Error: {e}")
        
        if self.use_rich:
            self.console.print("\n[dim]Goodbye![/dim]")
        else:
            print("\nGoodbye!")