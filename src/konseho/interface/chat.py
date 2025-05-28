"""Terminal chat interface for councils."""

from datetime import datetime
from typing import Any

try:
    from rich.console import Console
    from rich.live import Live
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


class ChatInterface:
    """Terminal interface for interacting with councils."""

    def __init__(
        self,
        use_rich: bool = True,
        save_outputs: bool = False,
        output_dir: str | None = None,
    ):
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

    def _extract_text_content(self, content: Any) -> str:
        """Extract text from various agent response formats."""
        if isinstance(content, str):
            # Try to parse as JSON first
            try:
                import json

                parsed = json.loads(content)
                # Recursively extract from parsed content
                return self._extract_text_content(parsed)
            except (json.JSONDecodeError, ValueError):
                # Not JSON, return as-is
                return content
        elif isinstance(content, list):
            # Handle [{'text': '...'}] format
            if content and isinstance(content[0], dict) and "text" in content[0]:
                return content[0]["text"]
            # Handle list of strings
            elif content and isinstance(content[0], str):
                return content[0]
            else:
                return str(content)
        elif isinstance(content, dict):
            # Handle {'text': '...'} format
            if "text" in content:
                return content["text"]
            elif "content" in content:
                return self._extract_text_content(content["content"])
            elif "message" in content:
                return content["message"]
            else:
                return str(content)
        else:
            return str(content)

    def display_welcome(self) -> None:
        """Display welcome message."""
        if self.use_rich:
            self.console.print(
                Panel.fit(
                    "[bold cyan]Welcome to Konseho Council[/bold cyan]\n"
                    "Multi-agent collaboration framework",
                    border_style="cyan",
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
            # Handle StepResult objects - convert to dict for display logic
            if hasattr(step_result, "output") and hasattr(step_result, "metadata"):
                # For debate results, put winner in the expected place
                if "winner" in step_result.metadata:
                    step_dict = {
                        "winner": step_result.output,  # output contains the winner
                        "proposals": step_result.metadata.get("proposals", {}),
                        "votes": step_result.metadata.get("votes", {}),
                    }
                    step_result = step_dict
                # For parallel results
                elif "parallel_results" in step_result.metadata:
                    # Ensure we get the dict from metadata
                    parallel_results = step_result.metadata.get("parallel_results", {})
                    if isinstance(parallel_results, dict):
                        step_result = {"parallel_results": parallel_results}
                    else:
                        # Fallback to just showing the output
                        if self.use_rich:
                            self.console.print("\n[bold]Step Result:[/bold]")
                            self.console.print(
                                Panel(step_result.output, border_style="blue")
                            )
                        else:
                            print("\nStep Result:")
                            print("-" * 50)
                            print(step_result.output)
                            print("-" * 50)
                        return
                # For other results, just display the output
                else:
                    if self.use_rich:
                        self.console.print("\n[bold]Step Result:[/bold]")
                        self.console.print(
                            Panel(step_result.output, border_style="blue")
                        )
                    else:
                        print("\nStep Result:")
                        print("-" * 50)
                        print(step_result.output)
                        print("-" * 50)
                    return

            # For debate step results
            if isinstance(step_result, dict) and "winner" in step_result:
                winner = self._extract_text_content(
                    step_result.get("winner", "No winner selected")
                )
                proposals = step_result.get("proposals", {})
                votes = step_result.get("votes", {})

                if self.use_rich:
                    self.console.print(
                        "\n[bold cyan]🎯 Council Debate Results[/bold cyan]"
                    )

                    # Only show initial proposals (not debate rounds)
                    initial_proposals = {}
                    for key, value in proposals.items():
                        if "_round_" not in key:  # Skip debate rounds
                            agent_name = key
                            text_content = self._extract_text_content(value)
                            initial_proposals[agent_name] = text_content

                    # Display initial proposals with better formatting
                    if initial_proposals:
                        self.console.print("\n[bold]Initial Proposals:[/bold]")
                        for agent_name, text_content in initial_proposals.items():
                            vote_count = votes.get(agent_name, 0)

                            # Show first 500 chars as preview
                            if len(text_content) > 500:
                                # Find a good break point (end of sentence/paragraph)
                                preview = text_content[:500]
                                last_period = preview.rfind(".")
                                last_newline = preview.rfind("\n")
                                break_point = max(last_period, last_newline)
                                if break_point > 300:
                                    preview = preview[: break_point + 1]
                                preview += "\n\n[dim]... (truncated for brevity)[/dim]"
                            else:
                                preview = text_content

                            self.console.print(
                                f"\n[yellow]→ {agent_name}[/yellow] [dim](Votes: {vote_count})[/dim]"
                            )
                            self.console.print(
                                Panel(preview, border_style="yellow", padding=(1, 2))
                            )

                    # Display winner with full content - NO TRUNCATION
                    self.console.print(
                        "\n[bold green]✅ Winning Approach:[/bold green]"
                    )
                    self.console.print(
                        Panel(winner, border_style="green", padding=(1, 2))
                    )
                else:
                    print("\n🎯 Council Debate Results")
                    print("=" * 70)

                    # Only show initial proposals (not debate rounds)
                    initial_proposals = {}
                    for key, value in proposals.items():
                        if "_round_" not in key:  # Skip debate rounds
                            agent_name = key
                            text_content = self._extract_text_content(value)
                            initial_proposals[agent_name] = text_content

                    if initial_proposals:
                        print("\nInitial Proposals:")
                        for agent_name, text_content in initial_proposals.items():
                            vote_count = votes.get(agent_name, 0)

                            print(f"\n→ {agent_name} (Votes: {vote_count})")
                            print("-" * 50)

                            # Show preview for proposals
                            if len(text_content) > 500:
                                preview = text_content[:500]
                                last_period = preview.rfind(".")
                                if last_period > 300:
                                    preview = preview[: last_period + 1]
                                print(preview)
                                print("\n... (truncated for brevity)")
                            else:
                                print(text_content)

                    # Display winner - FULL CONTENT
                    print("\n✅ Winning Approach:")
                    print("=" * 50)
                    print(winner)
                    print("=" * 70)

            # For parallel step results
            elif isinstance(step_result, dict) and (
                "results" in step_result or "parallel_results" in step_result
            ):
                results_key = (
                    "parallel_results"
                    if "parallel_results" in step_result
                    else "results"
                )
                parallel_results = step_result[results_key]

                if self.use_rich:
                    self.console.print(
                        "\n[bold cyan]🔄 Parallel Agent Analysis[/bold cyan]"
                    )
                    for agent_name, agent_result in parallel_results.items():
                        # Extract text content using our helper
                        text = self._extract_text_content(agent_result)

                        # Display with better formatting
                        self.console.print(f"\n[yellow]→ {agent_name}[/yellow]")

                        # For parallel results, show full content as they're usually more concise
                        self.console.print(
                            Panel(text, border_style="yellow", padding=(1, 2))
                        )
                else:
                    print("\n🔄 Parallel Agent Analysis")
                    print("=" * 70)
                    for agent_name, agent_result in parallel_results.items():
                        # Extract text content using our helper
                        text = self._extract_text_content(agent_result)

                        print(f"\n→ {agent_name}:")
                        print("-" * 50)
                        print(text)
                    print("=" * 70)

            # For other step results
            else:
                if self.use_rich:
                    self.console.print("\n[bold]Step Result:[/bold]")
                    display_text = (
                        str(step_result)[:1000] + "..."
                        if len(str(step_result)) > 1000
                        else str(step_result)
                    )
                    self.console.print(Panel(display_text, border_style="blue"))
                else:
                    print("\nStep Result:")
                    print("-" * 50)
                    display_text = (
                        str(step_result)[:1000] + "..."
                        if len(str(step_result)) > 1000
                        else str(step_result)
                    )
                    print(display_text)
                    print("-" * 50)

        except Exception as e:
            # Handle display errors gracefully
            if self.use_rich:
                self.console.print(
                    f"[bold red]Error displaying step result:[/bold red] {str(e)}"
                )
            else:
                print(f"Error displaying step result: {str(e)}")

    def display_event(self, event: str, data: dict[str, Any]) -> None:
        """Display an event in the interface."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self._event_log.append({"time": timestamp, "event": event, "data": data})

        if self.use_rich:
            if event == "council:start":
                self.console.print(
                    f"\n[bold green]▶ Starting Council:[/bold green] {data.get('council', 'Unknown')}"
                )
                self.console.print(f"[dim]Task: {data.get('task', 'No task')}[/dim]")
            elif event == "step:start":
                self.console.print(
                    f"\n[yellow]→ Step {data.get('step', '?')}:[/yellow] {data.get('type', 'Unknown')}"
                )
            elif event == "step:complete":
                self.console.print("[green]✓ Step completed[/green]")
                # Display step results immediately
                if "result" in data:
                    self._display_step_result(data["result"])
            elif event == "council:complete":
                self.console.print(
                    "\n[bold green]✓ Council completed successfully[/bold green]"
                )
            elif event.endswith(":error"):
                self.console.print(
                    f"[bold red]✗ Error:[/bold red] {data.get('error', 'Unknown error')}"
                )
        else:
            if event == "step:complete" and "result" in data:
                print(f"[{timestamp}] Step completed")
                self._display_step_result(data["result"])
            else:
                print(f"[{timestamp}] {event}: {data}")

    def display_result(self, result: dict[str, Any]) -> None:
        """Display final result."""
        try:
            # Extract the actual result from the council execution
            if "results" in result:
                # This is the council result format - results is always a list
                step_results = result["results"]
                if step_results:
                    # Display ALL step results from the list
                    for i, step_result in enumerate(step_results):
                        # Determine step type for better description
                        step_desc = f"Step {i + 1}"
                        if hasattr(step_result, "metadata"):
                            if "winner" in step_result.metadata:
                                step_desc = f"Step {i + 1}: Final Decision"
                            elif "parallel_results" in step_result.metadata:
                                step_desc = f"Step {i + 1}: Agent Research & Analysis"

                        # Display each step's result using the existing _display_step_result method
                        if self.use_rich:
                            self.console.print(
                                f"\n[bold cyan]━━━ {step_desc} ━━━[/bold cyan]"
                            )
                        else:
                            print(f"\n━━━ {step_desc} ━━━")

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
                self.console.print(
                    f"[bold red]Error displaying result:[/bold red] {str(e)}"
                )
            else:
                print(f"Error displaying result: {str(e)}")

    async def interactive_session(self, council) -> None:
        """Run an interactive session with a council."""
        self.display_welcome()

        # Subscribe to council events
        if hasattr(council, "_event_emitter"):
            council._event_emitter.on(
                "council:start", lambda e, d: self.display_event(e, d)
            )
            council._event_emitter.on(
                "step:start", lambda e, d: self.display_event(e, d)
            )
            council._event_emitter.on(
                "step:complete", lambda e, d: self.display_event(e, d)
            )
            council._event_emitter.on(
                "council:complete", lambda e, d: self.display_event(e, d)
            )
            council._event_emitter.on(
                "council:error", lambda e, d: self.display_event(e, d)
            )

        while True:
            try:
                # Get user input
                if self.use_rich:
                    task = self.console.input(
                        "\n[bold cyan]Enter task (or 'quit' to exit):[/bold cyan] "
                    )
                else:
                    task = input("\nEnter task (or 'quit' to exit): ")

                if task.lower() in ["quit", "exit", "q"]:
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
