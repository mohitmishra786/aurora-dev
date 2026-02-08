"""
Project monitoring commands for AURORA-DEV CLI.
"""
import time
from typing import Optional

import typer
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
from rich.table import Table


console = Console()
app = typer.Typer(help="Monitor AURORA-DEV projects")


@app.command(name="project")
def project(
    project_id: str = typer.Argument(..., help="Project ID to monitor"),
    live: bool = typer.Option(False, "--live", "-l", help="Enable live updates"),
    interval: int = typer.Option(5, "--interval", "-i", help="Update interval in seconds"),
) -> None:
    """
    Monitor project execution progress.
    
    Example:
        aurora monitor project abc123 --live
    """
    console.print(f"[blue]Monitoring project: {project_id}[/blue]\n")
    
    # TODO: Implement actual monitoring via API
    # For now, show a demo view
    
    if live:
        with Live(console=console, refresh_per_second=1) as live_display:
            for _ in range(10):
                table = _create_status_table(project_id)
                live_display.update(table)
                time.sleep(interval)
    else:
        table = _create_status_table(project_id)
        console.print(table)


def _create_status_table(project_id: str) -> Table:
    """Create a status table for the project."""
    table = Table(title=f"Project Status: {project_id[:8]}...")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Progress", style="magenta")
    table.add_column("Last Update", style="yellow")
    
    # Demo data
    components = [
        ("Maestro", "Active", "Orchestrating tasks", "Just now"),
        ("Architect", "Completed", "100%", "2m ago"),
        ("Backend Developer", "Working", "45%", "Just now"),
        ("Database Agent", "Waiting", "0%", "5m ago"),
        ("Test Engineer", "Queued", "-", "-"),
    ]
    
    for name, status, progress, updated in components:
        status_icon = {
            "Active": "[bold green]●[/bold green]",
            "Completed": "[green]✓[/green]",
            "Working": "[yellow]◐[/yellow]",
            "Waiting": "[dim]○[/dim]",
            "Queued": "[dim]○[/dim]",
            "Failed": "[red]✗[/red]",
        }.get(status, "○")
        
        table.add_row(name, f"{status_icon} {status}", progress, updated)
    
    return table


@app.command(name="agents")
def agents(
    project_id: Optional[str] = typer.Argument(None, help="Project ID (optional)"),
) -> None:
    """
    Monitor active agents.
    
    Shows all agents and their current status across projects.
    """
    table = Table(title="Active Agents")
    table.add_column("Agent", style="cyan")
    table.add_column("Project", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Task", style="magenta")
    table.add_column("Tokens Used", justify="right", style="yellow")
    
    # Demo data
    agents_data = [
        ("Maestro", "proj-abc", "Active", "Coordinating workflow", "1,234"),
        ("Architect", "proj-abc", "Completed", "-", "5,678"),
        ("Backend", "proj-abc", "Working", "Implementing API endpoints", "3,456"),
        ("Frontend", "proj-xyz", "Working", "Creating React components", "2,890"),
    ]
    
    for name, proj, status, task, tokens in agents_data:
        if project_id and not proj.startswith(project_id[:8]):
            continue
        
        status_icon = {
            "Active": "[bold green]●[/bold green]",
            "Completed": "[green]✓[/green]",
            "Working": "[yellow]◐[/yellow]",
            "Idle": "[dim]○[/dim]",
        }.get(status, "○")
        
        table.add_row(name, proj, f"{status_icon} {status}", task or "-", tokens)
    
    console.print(table)


@app.command(name="tasks")
def tasks(
    project_id: Optional[str] = typer.Argument(None, help="Project ID (optional)"),
    status_filter: Optional[str] = typer.Option(None, "--status", "-s", help="Filter by status"),
) -> None:
    """
    Monitor task queue.
    
    Shows all tasks in the queue with their status.
    """
    table = Table(title="Task Queue")
    table.add_column("Task ID", style="dim")
    table.add_column("Type", style="cyan")
    table.add_column("Priority", style="magenta")
    table.add_column("Status", style="green")
    table.add_column("Agent", style="yellow")
    table.add_column("Duration", justify="right")
    
    # Demo data
    tasks_data = [
        ("task-001", "Design API", "HIGH", "Completed", "Architect", "1m 23s"),
        ("task-002", "Implement Auth", "CRITICAL", "Running", "Backend", "45s"),
        ("task-003", "Create Models", "MEDIUM", "Queued", "-", "-"),
        ("task-004", "Write Tests", "LOW", "Pending", "-", "-"),
    ]
    
    for tid, ttype, priority, status, agent, duration in tasks_data:
        if status_filter and status.lower() != status_filter.lower():
            continue
        
        priority_color = {
            "CRITICAL": "red",
            "HIGH": "yellow",
            "MEDIUM": "blue",
            "LOW": "dim",
        }.get(priority, "white")
        
        status_icon = {
            "Completed": "[green]✓[/green]",
            "Running": "[yellow]◐[/yellow]",
            "Queued": "[dim]○[/dim]",
            "Pending": "[dim]○[/dim]",
            "Failed": "[red]✗[/red]",
        }.get(status, "○")
        
        table.add_row(
            tid,
            ttype,
            f"[{priority_color}]{priority}[/{priority_color}]",
            f"{status_icon} {status}",
            agent or "-",
            duration,
        )
    
    console.print(table)


@app.command(name="logs")
def logs(
    project_id: str = typer.Argument(..., help="Project ID"),
    agent: Optional[str] = typer.Option(None, "--agent", "-a", help="Filter by agent"),
    lines: int = typer.Option(20, "--lines", "-n", help="Number of lines to show"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow log output"),
) -> None:
    """
    View project logs.
    
    Example:
        aurora monitor logs abc123 --agent backend --follow
    """
    console.print(f"[blue]Logs for project: {project_id}[/blue]\n")
    
    # Demo log output
    demo_logs = [
        "[2024-01-15 10:30:01] [INFO] [maestro] Project initialized",
        "[2024-01-15 10:30:02] [INFO] [maestro] Decomposing requirements",
        "[2024-01-15 10:30:05] [INFO] [architect] Starting architecture design",
        "[2024-01-15 10:30:15] [INFO] [architect] Generated system diagram",
        "[2024-01-15 10:30:20] [INFO] [maestro] Assigning tasks to developers",
        "[2024-01-15 10:30:21] [INFO] [backend] Starting API implementation",
        "[2024-01-15 10:30:45] [INFO] [backend] Created user model",
        "[2024-01-15 10:31:00] [INFO] [backend] Implemented authentication",
    ]
    
    for log in demo_logs[-lines:]:
        if agent and f"[{agent}]" not in log:
            continue
        
        # Color based on log level
        if "[ERROR]" in log:
            console.print(f"[red]{log}[/red]")
        elif "[WARN]" in log:
            console.print(f"[yellow]{log}[/yellow]")
        elif "[DEBUG]" in log:
            console.print(f"[dim]{log}[/dim]")
        else:
            console.print(log)
    
    if follow:
        console.print("\n[dim]Following logs... Press Ctrl+C to stop[/dim]")
        # TODO: Implement actual log following
