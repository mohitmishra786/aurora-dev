"""
Status commands for AURORA-DEV CLI.
"""
import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


console = Console()
app = typer.Typer(help="Check AURORA-DEV system status")


@app.callback(invoke_without_command=True)
def status(
    ctx: typer.Context,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed status"),
) -> None:
    """
    Show AURORA-DEV system status.
    
    Without subcommand, shows overall system status.
    """
    if ctx.invoked_subcommand is not None:
        return
    
    # Check system components
    components = _check_components()
    
    # Build status panel
    table = Table(show_header=True, header_style="bold")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details", style="dim")
    
    for name, status_info in components.items():
        icon = "[green]●[/green]" if status_info["ok"] else "[red]●[/red]"
        table.add_row(
            name,
            f"{icon} {'OK' if status_info['ok'] else 'Error'}",
            status_info.get("details", ""),
        )
    
    all_ok = all(c["ok"] for c in components.values())
    border_style = "green" if all_ok else "red"
    
    console.print(Panel(
        table,
        title="AURORA-DEV Status",
        subtitle="[green]All systems operational[/green]" if all_ok else "[red]Some issues detected[/red]",
        border_style=border_style,
    ))
    
    if verbose:
        _show_detailed_status()


def _check_components() -> dict:
    """Check status of system components."""
    import os
    from pathlib import Path
    
    components = {}
    
    # Check API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    config_file = Path.home() / ".aurora" / "config.yaml"
    
    if not api_key and config_file.exists():
        try:
            import yaml
            config = yaml.safe_load(config_file.read_text()) or {}
            api_key = config.get("anthropic_api_key")
        except Exception:
            pass
    
    components["Anthropic API"] = {
        "ok": bool(api_key),
        "details": "API key configured" if api_key else "Run: aurora config set api_key YOUR_KEY",
    }
    
    # Check Redis
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, socket_timeout=1)
        r.ping()
        components["Redis"] = {"ok": True, "details": "localhost:6379"}
    except Exception:
        components["Redis"] = {"ok": False, "details": "Not running (optional)"}
    
    # Check PostgreSQL
    try:
        import psycopg2
        # Just check if library is available
        components["PostgreSQL"] = {"ok": True, "details": "Driver available"}
    except ImportError:
        components["PostgreSQL"] = {"ok": False, "details": "psycopg2 not installed"}
    
    # Check Python version
    import sys
    py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    components["Python"] = {
        "ok": sys.version_info >= (3, 12),
        "details": py_version,
    }
    
    # Check config
    components["Configuration"] = {
        "ok": config_file.exists(),
        "details": str(config_file) if config_file.exists() else "Run: aurora config init",
    }
    
    return components


def _show_detailed_status() -> None:
    """Show detailed system information."""
    import sys
    import platform
    
    console.print("\n[bold]System Information:[/bold]")
    console.print(f"  Python: {sys.version}")
    console.print(f"  Platform: {platform.platform()}")
    console.print(f"  Machine: {platform.machine()}")
    
    # Show installed packages
    try:
        import pkg_resources
        
        key_packages = [
            "anthropic", "celery", "redis", "fastapi",
            "typer", "rich", "pydantic", "sqlalchemy",
        ]
        
        console.print("\n[bold]Key Packages:[/bold]")
        for pkg in key_packages:
            try:
                version = pkg_resources.get_distribution(pkg).version
                console.print(f"  [green]✓[/green] {pkg}: {version}")
            except pkg_resources.DistributionNotFound:
                console.print(f"  [red]✗[/red] {pkg}: not installed")
    except ImportError:
        pass


@app.command(name="api")
def api_status() -> None:
    """Check API server status."""
    import httpx
    
    api_url = "http://localhost:8000"
    
    try:
        response = httpx.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            console.print(Panel(
                f"[green]API Server is running[/green]\n\n"
                f"  Version: {data.get('version', 'unknown')}\n"
                f"  Status: {data.get('status', 'unknown')}",
                title="API Status",
                border_style="green",
            ))
        else:
            console.print(f"[yellow]API returned status {response.status_code}[/yellow]")
    except httpx.ConnectError:
        console.print(Panel(
            "[red]API Server is not running[/red]\n\n"
            "Start with:\n"
            "  uvicorn aurora_dev.interfaces.api.main:app --reload",
            title="API Status",
            border_style="red",
        ))
    except Exception as e:
        console.print(f"[red]Error checking API: {e}[/red]")


@app.command(name="workers")
def workers_status() -> None:
    """Check Celery workers status."""
    try:
        from aurora_dev.core.task_queue import celery_app
        
        # Try to get worker stats
        inspect = celery_app.control.inspect()
        active = inspect.active()
        
        if active:
            table = Table(title="Celery Workers")
            table.add_column("Worker", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Active Tasks", justify="right")
            
            for worker, tasks in active.items():
                table.add_row(worker, "[green]●[/green] Running", str(len(tasks)))
            
            console.print(table)
        else:
            console.print("[yellow]No workers currently running[/yellow]")
            console.print("\nStart workers with:")
            console.print("  celery -A aurora_dev.core.task_queue worker --loglevel=info")
    
    except Exception as e:
        console.print(f"[red]Cannot connect to workers: {e}[/red]")
        console.print("\nEnsure Redis is running and start workers with:")
        console.print("  celery -A aurora_dev.core.task_queue worker --loglevel=info")
