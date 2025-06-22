"""
MCP CLI - Model Context Protocol Server Generator

A command-line tool for generating MCP servers from templates or OpenAPI specifications.
Provides standardized project structure, comprehensive testing, and deployment ready code.

Author: AI Development Team
"""

# Import version dynamically from package metadata (pyproject.toml)
try:
    from importlib.metadata import version
    __version__ = version("mcp-cli")
except ImportError:
    # Fallback for development or when package not installed
    __version__ = "1.0.1"
__author__ = "AI Development Team"
__description__ = "CLI tool for generating MCP (Model Context Protocol) servers"

from .generators import (
    ProjectStructureGenerator,
    OpenAPIGenerator,
    TestGenerator,
    DockerGenerator,
    ConfigGenerator
)
from .validators import OpenAPIValidator, ProjectValidator
from .utils import setup_logging, create_directory_structure

__all__ = [
    "__version__",
    "__author__", 
    "__description__",
    "ProjectStructureGenerator",
    "OpenAPIGenerator",
    "TestGenerator",
    "DockerGenerator",
    "ConfigGenerator",
    "OpenAPIValidator",
    "ProjectValidator",
    "setup_logging",
    "create_directory_structure"
] 