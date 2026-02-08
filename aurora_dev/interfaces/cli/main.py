"""
AURORA-DEV CLI Main Application.

Central Typer application that registers all command groups.
"""
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from aurora_dev.interfaces.cli.commands import create, monitor, config, status


# Initialize console for rich output
console = Console()

# Create main Typer app
app = typer.Typer(
    name="aurora",
    help="AURORA-DEV: Multi-agent autonomous development system",
    add_completion=True,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Register command groups
app.add_typer(create.app, name="create", help="Create new projects")
app.add_typer(monitor.app, name="monitor", help="Monitor project status")
app.add_typer(config.app, name="config", help="Manage configuration")


@app.command()
def version() -> None:
    """Show AURORA-DEV version information."""
    from aurora_dev import __version__
    
    console.print(
        Panel(
            f"[bold blue]AURORA-DEV[/bold blue] v{__version__}",
            subtitle="Multi-agent autonomous development system",
            border_style="blue",
        )
    )


@app.command()
def init(
    path: str = typer.Argument(".", help="Path to initialize project"),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
) -> None:
    """Initialize AURORA-DEV in the current directory."""
    import os
    from pathlib import Path
    
    target = Path(path).resolve()
    config_file = target / ".aurora.yaml"
    
    if config_file.exists() and not force:
        console.print("[yellow]⚠ Config file already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(1)
    
    # Create default config
    default_config = """# AURORA-DEV Configuration
project:
  name: my-project
  type: fullstack
  tech_stack:
    - python
    - fastapi
    - postgresql
    - react

settings:
  model: claude-sonnet-4-20250514
  max_retries: 3
  enable_reflexion: true
  
# Uncomment to customize agent behavior
# agents:
#   maestro:
#     max_concurrent_tasks: 5
#   architect:
#     design_depth: detailed
"""
    
    config_file.write_text(default_config)
    console.print(f"[green]✓ Initialized AURORA-DEV config at {config_file}[/green]")


@app.command(name="run")
def run_project(
    project_id: Optional[str] = typer.Argument(None, help="Project ID to run"),
    config_file: Optional[str] = typer.Option(None, "--config", "-c", help="Config file path"),
) -> None:
    """Run an AURORA-DEV project."""
    from aurora_dev.core.config import get_settings
    
    settings = get_settings()
    
    if not settings.anthropic.api_key:
        console.print("[red]✗ ANTHROPIC_API_KEY not set. Run: aurora config set api_key YOUR_KEY[/red]")
        raise typer.Exit(1)
    
    if project_id:
        console.print(f"[blue]▶ Resuming project: {project_id}[/blue]")
    else:
        console.print("[blue]▶ Starting new project from config...[/blue]")
    
    # TODO: Implement actual project execution
    console.print("[yellow]⚠ Project execution not yet implemented[/yellow]")


@app.command()
def agents() -> None:
    """List available agents and their status."""
    from rich.table import Table
    
    from aurora_dev.agents.base_agent import AgentRole
    
    table = Table(title="AURORA-DEV Agents", show_header=True)
    table.add_column("Agent", style="cyan")
    table.add_column("Tier", style="magenta")
    table.add_column("Role", style="green")
    table.add_column("Status", style="yellow")
    
    # Define agent info
    agent_info = [
        ("Maestro", "1", "Orchestration", "Available"),
        ("Memory Coordinator", "1", "Memory Management", "Available"),
        ("Architect", "2", "System Design", "Available"),
        ("Research", "2", "Technology Research", "Available"),
        ("Product Analyst", "2", "Requirements", "Available"),
        ("Backend", "3", "Backend Development", "Available"),
        ("Frontend", "3", "Frontend Development", "Available"),
        ("Database", "3", "Database Design", "Available"),
        ("Integration", "3", "System Integration", "Available"),
        ("Test Engineer", "4", "Testing", "Available"),
        ("Security Auditor", "4", "Security", "Available"),
        ("Code Reviewer", "4", "Code Review", "Available"),
        ("Validator", "4", "Validation", "Available"),
        ("DevOps", "5", "Deployment", "Available"),
        ("Documentation", "5", "Documentation", "Available"),
        ("Monitoring", "5", "Observability", "Available"),
    ]
    
    for name, tier, role, status in agent_info:
        table.add_row(name, f"Tier {tier}", role, f"[green]●[/green] {status}")
    
    console.print(table)


# Alias for common command
@app.command(name="new")
def new_project(
    name: str = typer.Argument(..., help="Project name"),
    project_type: str = typer.Option("fullstack", "--type", "-t", help="Project type"),
    tech_stack: Optional[str] = typer.Option(None, "--tech", help="Comma-separated tech stack"),
) -> None:
    """Quick alias for 'aurora create project'."""
    create.project(name=name, project_type=project_type, tech_stack=tech_stack)


def cli() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    cli()
