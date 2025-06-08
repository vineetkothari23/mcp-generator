"""
MCP CLI - Model Context Protocol Server Generator

A command-line tool for generating MCP servers from templates or OpenAPI specifications.
Provides standardized project structure, comprehensive testing, and deployment ready code.

Version: 1.0.0
Author: AI Development Team
"""

__version__ = "1.0.0"
__author__ = "AI Development Team"
__description__ = "CLI tool for generating MCP (Model Context Protocol) servers"

from .cli import cli, MCPCLI
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
    "cli",
    "MCPCLI",
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