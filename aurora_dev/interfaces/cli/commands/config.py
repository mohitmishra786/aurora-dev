"""
Configuration commands for AURORA-DEV CLI.
"""
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


console = Console()
app = typer.Typer(help="Manage AURORA-DEV configuration")


# Config file locations
CONFIG_DIR = Path.home() / ".aurora"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def _ensure_config_dir() -> None:
    """Ensure config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_config() -> dict:
    """Load configuration from file."""
    if not CONFIG_FILE.exists():
        return {}
    
    try:
        import yaml
        return yaml.safe_load(CONFIG_FILE.read_text()) or {}
    except Exception:
        return {}


def _save_config(config: dict) -> None:
    """Save configuration to file."""
    _ensure_config_dir()
    
    import yaml
    CONFIG_FILE.write_text(yaml.dump(config, default_flow_style=False))


@app.command(name="set")
def set_config(
    key: str = typer.Argument(..., help="Configuration key"),
    value: str = typer.Argument(..., help="Configuration value"),
    global_config: bool = typer.Option(False, "--global", "-g", help="Set in global config"),
) -> None:
    """
    Set a configuration value.
    
    Examples:
        aurora config set api_key sk-xxx --global
        aurora config set model claude-sonnet-4-20250514
    """
    # Handle special keys
    if key.lower() in ("api_key", "anthropic_api_key"):
        # Store API key in environment or secure location
        config = _load_config()
        config["anthropic_api_key"] = value
        _save_config(config)
        console.print(f"[green]✓ Set {key} (value hidden for security)[/green]")
        console.print(f"[dim]Stored in: {CONFIG_FILE}[/dim]")
        return
    
    config = _load_config()
    
    # Support nested keys with dot notation
    keys = key.split(".")
    current = config
    
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    _save_config(config)
    
    console.print(f"[green]✓ Set {key} = {value}[/green]")


@app.command(name="get")
def get_config(
    key: str = typer.Argument(..., help="Configuration key"),
) -> None:
    """
    Get a configuration value.
    
    Example:
        aurora config get model
    """
    config = _load_config()
    
    # Support nested keys
    keys = key.split(".")
    current = config
    
    try:
        for k in keys:
            current = current[k]
        
        # Hide sensitive values
        if "key" in key.lower() or "secret" in key.lower() or "password" in key.lower():
            display_value = current[:4] + "****" if current else "(not set)"
        else:
            display_value = current
        
        console.print(f"{key} = {display_value}")
    except (KeyError, TypeError):
        console.print(f"[yellow]Key not found: {key}[/yellow]")
        raise typer.Exit(1)


@app.command(name="list")
def list_config(
    show_secrets: bool = typer.Option(False, "--show-secrets", help="Show secret values"),
) -> None:
    """
    List all configuration values.
    """
    config = _load_config()
    
    if not config:
        console.print("[yellow]No configuration set. Use 'aurora config set KEY VALUE'[/yellow]")
        return
    
    table = Table(title="AURORA-DEV Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Source", style="dim")
    
    def _flatten(d: dict, prefix: str = "") -> list:
        items = []
        for k, v in d.items():
            full_key = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                items.extend(_flatten(v, full_key))
            else:
                items.append((full_key, v))
        return items
    
    for key, value in _flatten(config):
        # Hide sensitive values
        if not show_secrets and ("key" in key.lower() or "secret" in key.lower() or "password" in key.lower()):
            display_value = str(value)[:4] + "****" if value else "(not set)"
        else:
            display_value = str(value)
        
        table.add_row(key, display_value, str(CONFIG_FILE))
    
    # Also show environment variables
    env_vars = [
        ("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY")),
        ("AURORA_MODEL", os.environ.get("AURORA_MODEL")),
        ("AURORA_LOG_LEVEL", os.environ.get("AURORA_LOG_LEVEL")),
    ]
    
    for key, value in env_vars:
        if value:
            if not show_secrets and "KEY" in key:
                display_value = value[:4] + "****"
            else:
                display_value = value
            table.add_row(key, display_value, "environment")
    
    console.print(table)


@app.command(name="unset")
def unset_config(
    key: str = typer.Argument(..., help="Configuration key to remove"),
) -> None:
    """
    Remove a configuration value.
    """
    config = _load_config()
    
    # Support nested keys
    keys = key.split(".")
    current = config
    
    try:
        for k in keys[:-1]:
            current = current[k]
        
        del current[keys[-1]]
        _save_config(config)
        console.print(f"[green]✓ Removed {key}[/green]")
    except (KeyError, TypeError):
        console.print(f"[yellow]Key not found: {key}[/yellow]")


@app.command(name="path")
def config_path() -> None:
    """
    Show configuration file location.
    """
    console.print(Panel(
        f"[bold]Global Config:[/bold] {CONFIG_FILE}\n"
        f"[bold]Config Dir:[/bold] {CONFIG_DIR}\n"
        f"[bold]Exists:[/bold] {'Yes' if CONFIG_FILE.exists() else 'No'}",
        title="Configuration Paths",
        border_style="blue",
    ))


@app.command(name="init")
def init_config(
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite existing config"),
) -> None:
    """
    Initialize default configuration.
    """
    if CONFIG_FILE.exists() and not force:
        console.print("[yellow]Config already exists. Use --force to overwrite.[/yellow]")
        raise typer.Exit(1)
    
    default_config = {
        "model": "claude-sonnet-4-20250514",
        "max_retries": 3,
        "logging": {
            "level": "INFO",
            "format": "rich",
        },
        "agents": {
            "enable_reflexion": True,
            "max_concurrent": 5,
        },
    }
    
    _save_config(default_config)
    console.print(f"[green]✓ Created default config at {CONFIG_FILE}[/green]")
