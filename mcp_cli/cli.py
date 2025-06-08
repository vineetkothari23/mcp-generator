# mcp_cli/cli.py
"""
MCP Server CLI Tool - Initialize and generate MCP servers from templates or OpenAPI specs

This CLI tool provides commands to:
1. Initialize standard MCP server projects
2. Generate MCP servers from OpenAPI specifications
3. Add tools and resources to existing projects
4. Validate and test MCP server configurations

Author: AI Development Team
Version: 1.0.0
"""

import click
import os
import sys
import json
import yaml
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader
import subprocess
import shutil
from openapi_client_generator import OpenAPIClientGenerator
from mcp_tool_mapper import MCPToolMapper

# Import our template generators
from .generators import (
    ProjectStructureGenerator,
    OpenAPIGenerator,
    TestGenerator,
    DockerGenerator,
    ConfigGenerator
)
from .validators import OpenAPIValidator, ProjectValidator
from .utils import (
    setup_logging,
    create_directory_structure,
    copy_template_files,
    install_dependencies,
    run_initial_tests
)

@dataclass
class MCPProjectConfig:
    """Configuration for MCP project generation"""
    project_name: str
    service_name: str
    description: str
    author: str
    version: str = "1.0.0"
    python_version: str = "3.11"
    include_docker: bool = True
    include_ci: bool = True
    test_framework: str = "pytest"
    openapi_spec: Optional[str] = None
    output_dir: str = "."

class MCPCLIError(Exception):
    """Custom exception for MCP CLI errors"""
    pass

class MCPCLI:
    """Main CLI class for MCP server generation"""
    
    def __init__(self):
        """Initialize the CLI with default settings"""
        self.logger = setup_logging()
        self.template_dir = Path(__file__).parent / "templates"
        self.generators = {
            "structure": ProjectStructureGenerator(),
            "openapi": OpenAPIGenerator(),
            "tests": TestGenerator(),
            "docker": DockerGenerator(),
            "config": ConfigGenerator()
        }
    
    def validate_project_name(self, name: str) -> str:
        """
        Validate and sanitize project name
        
        Args:
            name: Raw project name input
            
        Returns:
            str: Sanitized project name
            
        Raises:
            MCPCLIError: If name is invalid
            
        Example:
            validate_project_name("My API Server") -> "my-api-server"
        """
        if not name or not name.strip():
            raise MCPCLIError("Project name cannot be empty")
        
        # Convert to lowercase, replace spaces and special chars with hyphens
        sanitized = name.lower().strip()
        sanitized = "".join(c if c.isalnum() else "-" for c in sanitized)
        sanitized = "-".join(filter(None, sanitized.split("-")))
        
        if not sanitized:
            raise MCPCLIError("Project name must contain alphanumeric characters")
        
        return sanitized

# CLI Commands using Click
@click.group()
@click.version_option(version="1.0.0", prog_name="mcp-cli")
@click.pass_context
def cli(ctx):
    """
    MCP Server CLI Tool
    
    Generate, initialize, and manage MCP (Model Context Protocol) servers
    with support for OpenAPI specification integration.
    """
    ctx.ensure_object(dict)
    ctx.obj['cli'] = MCPCLI()

@cli.command()
@click.option('--name', '-n', required=True, help='Project name')
@click.option('--description', '-d', default='', help='Project description')
@click.option('--author', '-a', default='Developer', help='Author name')
@click.option('--output-dir', '-o', default='.', help='Output directory')
@click.option('--python-version', default='3.11', help='Python version')
@click.option('--no-docker', is_flag=True, help='Skip Docker setup')
@click.option('--no-ci', is_flag=True, help='Skip CI/CD setup')
@click.option('--test-framework', default='pytest', help='Testing framework')
@click.pass_context
def init(ctx, name, description, author, output_dir, python_version, no_docker, no_ci, test_framework):
    """
    Initialize a new MCP server project with standard structure
    
    Creates a complete MCP server project with:
    - Standard directory structure
    - Configuration files
    - Test framework setup
    - Docker containerization (optional)
    - CI/CD pipeline (optional)
    
    Example:
        mcp-cli init --name "weather-api" --author "John Doe"
    """
    cli_instance = ctx.obj['cli']
    
    try:
        # Validate and create project config
        project_config = MCPProjectConfig(
            project_name=cli_instance.validate_project_name(name),
            service_name=name.replace('-', '_').replace(' ', '_').lower(),
            description=description or f"MCP server for {name}",
            author=author,
            python_version=python_version,
            include_docker=not no_docker,
            include_ci=not no_ci,
            test_framework=test_framework,
            output_dir=output_dir
        )
        
        click.echo(f"🚀 Initializing MCP server project: {project_config.project_name}")
        
        # Generate project structure
        project_path = _generate_standard_project(cli_instance, project_config)
        
        click.echo(f"✅ Project created successfully at: {project_path}")
        click.echo("\n📋 Next steps:")
        click.echo(f"  cd {project_config.project_name}")
        click.echo("  python -m pip install -r requirements-dev.txt")
        click.echo("  python -m pytest tests/")
        
    except MCPCLIError as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Unexpected error: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--spec', '-s', required=True, help='OpenAPI spec file path or URL')
@click.option('--name', '-n', help='Project name (auto-generated if not provided)')
@click.option('--output-dir', '-o', default='.', help='Output directory')
@click.option('--author', '-a', default='Developer', help='Author name')
@click.option('--generator-engine', default='enhanced', 
              type=click.Choice(['basic', 'enhanced']), 
              help='Generation engine to use')
@click.option('--async-client', is_flag=True, help='Generate async API client')
@click.option('--include-auth', help='Include authentication (oauth2, apikey, basic)')
@click.option('--client-config', help='Custom openapi-generator config file')
@click.option('--validate-only', is_flag=True, help='Only validate the OpenAPI spec')
@click.option('--include-examples', is_flag=True, help='Generate usage examples')
@click.option('--max-tools', default=50, help='Maximum number of tools to generate')
@click.pass_context
def from_openapi(ctx, spec, name, output_dir, author, generator_engine, async_client, 
                include_auth, client_config, validate_only, include_examples, max_tools):
    """
    Generate MCP server from OpenAPI specification
    
    Uses either basic generation or enhanced generation with openapi-generator.
    Enhanced mode provides more robust API client generation and better OpenAPI support.
    """
    
    if generator_engine == 'enhanced':
        # Use OpenAPIEnhancedGenerator
        generator = OpenAPIEnhancedGenerator()
    else:
        # Use existing OpenAPIGenerator  
        generator = OpenAPIGenerator()
    
    # Rest of implementation...

@cli.command()
@click.option('--spec', '-s', required=True, help='OpenAPI spec file path or URL')
@click.option('--output', '-o', help='Output file (default: stdout)')
@click.option('--format', default='json', type=click.Choice(['json', 'yaml']), help='Output format')
@click.pass_context
def analyze(ctx, spec, output, format):
    """
    Analyze OpenAPI specification and show MCP generation plan
    
    Shows what will be generated without creating files:
    - Available endpoints and operations
    - MCP tools mapping
    - Data models to be created
    - Potential issues or limitations
    
    Example:
        mcp-cli analyze --spec ./api-spec.yaml --format yaml
    """
    cli_instance = ctx.obj['cli']
    
    try:
        click.echo(f"🔍 Analyzing OpenAPI specification: {spec}")
        
        # Load OpenAPI spec
        openapi_data = _load_openapi_spec(spec)
        
        # Analyze and generate report
        analyzer = cli_instance.generators["openapi"]
        analysis_result = analyzer.analyze_spec(openapi_data)
        
        # Convert analysis result to dict for serialization
        analysis_dict = analysis_result.to_dict()
        
        # Format output
        if format == 'json':
            output_data = json.dumps(analysis_dict, indent=2)
        else:
            output_data = yaml.dump(analysis_dict, default_flow_style=False)
        
        if output:
            with open(output, 'w') as f:
                f.write(output_data)
            click.echo(f"📄 Analysis saved to: {output}")
        else:
            click.echo(output_data)
            
    except Exception as e:
        click.echo(f"❌ Error analyzing specification: {e}", err=True)
        sys.exit(1)

@cli.command()
@click.option('--project-dir', '-p', default='.', help='Project directory to validate')
@click.pass_context
def validate(ctx, project_dir):
    """
    Validate existing MCP server project structure and configuration
    
    Checks for:
    - Required files and directories
    - Configuration validity
    - Dependencies and imports
    - Test coverage
    - MCP protocol compliance
    
    Example:
        mcp-cli validate --project-dir ./my-mcp-server
    """
    cli_instance = ctx.obj['cli']
    
    try:
        click.echo(f"🔍 Validating MCP project: {project_dir}")
        
        validator = ProjectValidator()
        validation_result = validator.validate_project(Path(project_dir))
        
        if validation_result.is_valid:
            click.echo("✅ Project validation passed")
        else:
            click.echo("❌ Project validation failed:")
            for error in validation_result.errors:
                click.echo(f"  - {error}")
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"❌ Error validating project: {e}", err=True)
        sys.exit(1)

# Helper Functions

def _load_openapi_spec(spec_path: str) -> Dict[str, Any]:
    """
    Load OpenAPI specification from file or URL
    
    Args:
        spec_path: File path or URL to OpenAPI specification
        
    Returns:
        dict: Parsed OpenAPI specification
        
    Raises:
        MCPCLIError: If spec cannot be loaded or parsed
    """
    try:
        if spec_path.startswith(('http://', 'https://')):
            # Load from URL
            response = requests.get(spec_path, timeout=30)
            response.raise_for_status()
            
            if spec_path.endswith('.yaml') or spec_path.endswith('.yml'):
                return yaml.safe_load(response.text)
            else:
                return response.json()
        else:
            # Load from file
            spec_file = Path(spec_path)
            if not spec_file.exists():
                raise MCPCLIError(f"Specification file not found: {spec_path}")
            
            with open(spec_file, 'r', encoding='utf-8') as f:
                if spec_file.suffix in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
                    
    except requests.RequestException as e:
        raise MCPCLIError(f"Failed to load specification from URL: {e}")
    except (json.JSONDecodeError, yaml.YAMLError) as e:
        raise MCPCLIError(f"Failed to parse specification: {e}")
    except Exception as e:
        raise MCPCLIError(f"Unexpected error loading specification: {e}")

def _extract_project_name_from_openapi(openapi_data: Dict[str, Any]) -> str:
    """
    Extract project name from OpenAPI specification
    
    Args:
        openapi_data: Parsed OpenAPI specification
        
    Returns:
        str: Generated project name
    """
    info = openapi_data.get('info', {})
    
    # Try title first, then fallback to servers or default
    if 'title' in info:
        return info['title'].lower().replace(' ', '-')
    
    servers = openapi_data.get('servers', [])
    if servers and 'url' in servers[0]:
        # Extract domain name from server URL
        from urllib.parse import urlparse
        parsed = urlparse(servers[0]['url'])
        return parsed.netloc.split('.')[0] if parsed.netloc else 'api-server'
    
    return 'mcp-api-server'

def _generate_standard_project(cli_instance: MCPCLI, config: MCPProjectConfig) -> str:
    """
    Generate standard MCP server project structure
    
    Args:
        cli_instance: CLI instance with generators
        config: Project configuration
        
    Returns:
        str: Path to generated project
    """
    project_path = Path(config.output_dir) / config.project_name
    
    # Create directory structure
    cli_instance.generators["structure"].generate(project_path, config)
    
    # Generate configuration files
    cli_instance.generators["config"].generate(project_path, config)
    
    # Generate test framework
    cli_instance.generators["tests"].generate(project_path, config)
    
    # Generate Docker setup if requested
    if config.include_docker:
        cli_instance.generators["docker"].generate(project_path, config)
    
    return str(project_path)

def _generate_openapi_project(
    cli_instance: MCPCLI, 
    config: MCPProjectConfig, 
    openapi_data: Dict[str, Any],
    include_examples: bool,
    max_tools: int
) -> str:
    """
    Generate MCP server project from OpenAPI specification
    
    Args:
        cli_instance: CLI instance with generators
        config: Project configuration
        openapi_data: Parsed OpenAPI specification
        include_examples: Whether to generate usage examples
        max_tools: Maximum number of tools to generate
        
    Returns:
        str: Path to generated project
    """
    project_path = Path(config.output_dir) / config.project_name
    
    # Generate standard structure first
    project_path_str = _generate_standard_project(cli_instance, config)
    
    # Generate OpenAPI-specific components
    cli_instance.generators["openapi"].generate(
        project_path, 
        config, 
        openapi_data,
        include_examples=include_examples,
        max_tools=max_tools
    )
    
    return project_path_str

if __name__ == '__main__':
    cli()