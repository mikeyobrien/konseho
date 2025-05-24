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
    
    def __init__(self, use_rich: bool = True):
        """Initialize chat interface.
        
        Args:
            use_rich: Whether to use rich for formatting (fallback to basic if not available)
        """
        self.use_rich = use_rich and RICH_AVAILABLE
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
            elif event == "council:complete":
                self.console.print(f"\n[bold green]✓ Council completed successfully[/bold green]")
            elif event.endswith(":error"):
                self.console.print(f"[bold red]✗ Error:[/bold red] {data.get('error', 'Unknown error')}")
        else:
            print(f"[{timestamp}] {event}: {data}")
    
    def display_result(self, result: Dict[str, Any]) -> None:
        """Display final result."""
        if self.use_rich:
            self.console.print("\n[bold]Final Result:[/bold]")
            self.console.print(Panel(str(result), border_style="green"))
        else:
            print("\nFinal Result:")
            print("-" * 50)
            print(result)
            print("-" * 50)
    
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