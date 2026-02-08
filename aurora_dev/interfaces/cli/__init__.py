"""
AURORA-DEV Command Line Interface.

Provides CLI commands for managing AURORA-DEV projects, agents, and workflows.
Built with Typer for a modern CLI experience with type hints and auto-completion.

Example usage:
    aurora create-project --name my-api --type backend --tech fastapi,postgresql
    aurora monitor my-project-id
    aurora status
    aurora config set anthropic_api_key sk-xxx
"""
from .main import app, cli

__all__ = ["app", "cli"]
