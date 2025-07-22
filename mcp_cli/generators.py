"""
MCP Server Generators - Template-based code generation for MCP servers

This module contains generators for different aspects of MCP server projects:
- Project structure generation
- OpenAPI to MCP conversion
- Test suite generation
- Docker configuration
- Documentation generation

Each generator follows the test-first approach and creates comprehensive,
production-ready code with proper error handling and documentation.
"""

import os
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader, Template
import re
from urllib.parse import urlparse
from .openapi_client_generator import OpenAPIClientGenerator, ClientAnalysis
from .mcp_tool_mapper import MCPToolMapper
from .config import MCPProjectConfig

@dataclass
class GenerationResult:
    """Result of code generation operation"""
    success: bool
    files_created: List[str]
    errors: List[str]
    warnings: List[str]

@dataclass
class OpenAPIAnalysis:
    """Analysis result from OpenAPI specification"""
    endpoints: List[Dict[str, Any]]
    models: List[Dict[str, Any]]
    tools_count: int
    resources_count: int
    authentication_schemes: List[str]
    estimated_complexity: str
    potential_issues: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert analysis to dictionary for serialization"""
        return {
            "summary": {
                "tools_count": self.tools_count,
                "resources_count": self.resources_count,
                "estimated_complexity": self.estimated_complexity,
                "authentication_schemes": self.authentication_schemes
            },
            "endpoints": [
                {
                    "path": ep.get("path", ""),
                    "method": ep.get("method", ""),
                    "operation_id": ep.get("operation_id", ""),
                    "summary": ep.get("summary", ""),
                    "description": ep.get("description", ""),
                    "parameters_count": len(ep.get("parameters", []))
                }
                for ep in self.endpoints
            ],
            "models": [
                {
                    "name": model.get("name", ""),
                    "type": model.get("type", ""),
                    "properties_count": len(model.get("properties", {}))
                }
                for model in self.models
            ],
            "potential_issues": self.potential_issues
        }

class BaseGenerator:
    """Base class for all generators with common functionality"""
    
    def __init__(self):
        """Initialize generator with template environment"""
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Add custom filters
        self.env.filters['snake_case'] = self._to_snake_case
        self.env.filters['pascal_case'] = self._to_pascal_case
        self.env.filters['kebab_case'] = self._to_kebab_case
        
        # Add custom filters for template processing
        self.env.filters['snake_case'] = self._to_snake_case
        self.env.filters['pascal_case'] = self._to_pascal_case
        self.env.filters['kebab_case'] = self._to_kebab_case
    
    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case"""
        # Replace special chars and spaces with underscores
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text)
        # Insert underscore before uppercase letters
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        return text.lower()
    
    def _to_pascal_case(self, text: str) -> str:
        """Convert text to PascalCase"""
        words = re.findall(r'\w+', text)
        return ''.join(word.capitalize() for word in words)
    
    def _to_kebab_case(self, text: str) -> str:
        """Convert text to kebab-case"""
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '-', text)
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1-\2', text)
        return text.lower()
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render template with given context
        
        Args:
            template_name: Name of template file
            context: Template context variables
            
        Returns:
            str: Rendered template content
        """
        template = self.env.get_template(template_name)
        return template.render(**context)
    
    def write_file(self, file_path: Path, content: str) -> None:
        """
        Write content to file, creating directories as needed
        
        Args:
            file_path: Target file path
            content: File content to write
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

class ProjectStructureGenerator(BaseGenerator):
    """Generator for basic MCP server project structure"""
    
    def generate(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """
        Generate basic project structure and core files
        
        Args:
            project_path: Target project directory
            config: Project configuration object
            
        Returns:
            GenerationResult: Generation result with created files
        """
        files_created = []
        errors = []
        
        try:
            # Create directory structure
            directories = [
                "src",
                f"src/mcp_{config.service_name}",
                "tests/unit",
                "tests/integration",
                "tests/fixtures",
                "config",
                "scripts",
                "docs",
                "docker"
            ]
            
            for directory in directories:
                (project_path / directory).mkdir(parents=True, exist_ok=True)
            
            # Generate core Python files
            self._generate_core_files(project_path, config, files_created)
            
            # Generate configuration files
            self._generate_config_files(project_path, config, files_created)
            
            # Generate documentation
            self._generate_docs(project_path, config, files_created)
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )
            
        except Exception as e:
            errors.append(f"Failed to generate project structure: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )
    
    def _generate_core_files(self, project_path: Path, config, files_created: List[str]):
        """Generate core Python module files"""
        
        service_dir = project_path / "src" / f"mcp_{config.service_name}"
        
        # Generate __init__.py
        init_content = self.render_template("python/__init__.py.j2", {
            "service_name": config.service_name,
            "version": config.version,
            "description": config.description
        })
        init_path = service_dir / "__init__.py"
        self.write_file(init_path, init_content)
        files_created.append(str(init_path))
        
        # Generate server.py (main MCP server)
        server_content = self.render_template("python/server.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name,
            "description": config.description
        })
        server_path = service_dir / "server.py"
        self.write_file(server_path, server_content)
        files_created.append(str(server_path))
        
        # Generate config.py
        config_content = self.render_template("python/config.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name
        })
        config_path = service_dir / "config.py"
        self.write_file(config_path, config_content)
        files_created.append(str(config_path))
        
        # Generate models.py
        models_content = self.render_template("python/models.py.j2", {
            "service_name": config.service_name
        })
        models_path = service_dir / "models.py"
        self.write_file(models_path, models_content)
        files_created.append(str(models_path))
        
        # Generate client.py (API client wrapper)
        client_content = self.render_template("python/client.py.j2", {
            "service_name": config.service_name
        })
        client_path = service_dir / "client.py"
        self.write_file(client_path, client_content)
        files_created.append(str(client_path))
        
        # Generate tools.py (MCP tools)
        tools_content = self.render_template("python/tools.py.j2", {
            "service_name": config.service_name
        })
        tools_path = service_dir / "tools.py"
        self.write_file(tools_path, tools_content)
        files_created.append(str(tools_path))
    
    def _generate_config_files(self, project_path: Path, config, files_created: List[str]):
        """Generate configuration files"""
        
        # Generate requirements.txt
        requirements_content = self.render_template("config/requirements.txt.j2", {
            "python_version": config.python_version
        })
        req_path = project_path / "requirements.txt"
        self.write_file(req_path, requirements_content)
        files_created.append(str(req_path))
        
        # Generate requirements-dev.txt
        dev_req_content = self.render_template("config/requirements-dev.txt.j2", {
            "test_framework": config.test_framework
        })
        dev_req_path = project_path / "requirements-dev.txt"
        self.write_file(dev_req_path, dev_req_content)
        files_created.append(str(dev_req_path))
        
        # Generate pyproject.toml
        pyproject_content = self.render_template("config/pyproject.toml.j2", {
            "project_name": config.project_name,
            "service_name": config.service_name,
            "description": config.description,
            "author": config.author,
            "version": config.version,
            "python_version": config.python_version
        })
        pyproject_path = project_path / "pyproject.toml"
        self.write_file(pyproject_path, pyproject_content)
        files_created.append(str(pyproject_path))
        
        # Generate .env.example
        env_content = self.render_template("config/.env.example.j2", {
            "service_name": config.service_name.upper(),
            "project_name": config.project_name
        })
        env_path = project_path / ".env.example"
        self.write_file(env_path, env_content)
        files_created.append(str(env_path))
    
    def _generate_docs(self, project_path: Path, config, files_created: List[str]):
        """Generate documentation files"""
        
        # Generate README.md
        readme_content = self.render_template("docs/README.md.j2", {
            "project_name": config.project_name,
            "service_name": config.service_name,
            "description": config.description,
            "author": config.author
        })
        readme_path = project_path / "README.md"
        self.write_file(readme_path, readme_content)
        files_created.append(str(readme_path))

class OpenAPIGenerator(BaseGenerator):
    """Generator for OpenAPI-specific MCP server components 
    - Uses custom client generator to generate the client from the openAPI spec
    """
    
    def analyze_spec(self, openapi_data: Dict[str, Any]) -> OpenAPIAnalysis:
        """
        Analyze OpenAPI specification and return analysis
        
        Args:
            openapi_data: Parsed OpenAPI specification
            
        Returns:
            OpenAPIAnalysis: Detailed analysis of the specification
        """
        paths = openapi_data.get('paths', {})
        components = openapi_data.get('components', {})
        schemas = components.get('schemas', {})
        security_schemes = components.get('securitySchemes', {})
        
        # Analyze endpoints
        endpoints = []
        tools_count = 0
        
        for path, methods in paths.items():
            for method, operation in methods.items():
                # Skip path-level parameters (not HTTP methods)
                if method == 'parameters':
                    continue
                    
                # Check if operation is a dict (actual HTTP method operation)
                if not isinstance(operation, dict):
                    continue
                
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint_data = {
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId'),
                        'summary': operation.get('summary'),
                        'description': operation.get('description'),
                        'parameters': operation.get('parameters', []),
                        'request_body': operation.get('requestBody'),
                        'responses': operation.get('responses', {})
                    }
                    endpoints.append(endpoint_data)
                    tools_count += 1
        
        # Analyze models
        models = []
        for schema_name, schema_def in schemas.items():
            models.append({
                'name': schema_name,
                'type': schema_def.get('type'),
                'properties': schema_def.get('properties', {}),
                'required': schema_def.get('required', [])
            })
        
        # Analyze authentication
        auth_schemes = list(security_schemes.keys())
        
        # Estimate complexity
        complexity = self._estimate_complexity(tools_count, len(models), len(auth_schemes))
        
        # Identify potential issues
        issues = self._identify_issues(openapi_data, endpoints, models)
        
        return OpenAPIAnalysis(
            endpoints=endpoints,
            models=models,
            tools_count=tools_count,
            resources_count=len(models),  # Using models as resources
            authentication_schemes=auth_schemes,
            estimated_complexity=complexity,
            potential_issues=issues
        )
    
    def generate(self, project_path: Path, config: MCPProjectConfig, openapi_data: Dict[str, Any], 
                include_examples: bool = False, max_tools: int = 50) -> GenerationResult:
        """
        Generate MCP server components from OpenAPI specification
        
        Args:
            project_path: Target project directory
            config: Project configuration
            openapi_data: Parsed OpenAPI specification
            include_examples: Whether to generate usage examples
            max_tools: Maximum number of tools to generate
            
        Returns:
            GenerationResult: Generation result with created files
        """
        files_created = []
        errors = []
        warnings = []
        
        try:
            # Analyze the OpenAPI spec
            analysis = self.analyze_spec(openapi_data)
            
            # Check tool limit
            if analysis.tools_count > max_tools:
                warnings.append(f"API has {analysis.tools_count} operations, limiting to {max_tools}")
                analysis.endpoints = analysis.endpoints[:max_tools]
            
            # Generate OpenAPI-specific components
            self._generate_openapi_models(project_path, config, analysis, files_created)
            self._generate_openapi_client(project_path, config, openapi_data, analysis, files_created)
            self._generate_openapi_tools(project_path, config, analysis, files_created)
            self._generate_openapi_server(project_path, config, analysis, files_created)
            self._generate_openapi_tests(project_path, config, analysis, files_created)
            
            if include_examples:
                self._generate_examples(project_path, config, analysis, files_created)
            
            # Generate OpenAPI-specific configuration
            self._generate_openapi_config(project_path, config, openapi_data, files_created)
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            errors.append(f"Failed to generate OpenAPI components: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=files_created,
                errors=errors,
                warnings=warnings
            )
    
    def _estimate_complexity(self, tools_count: int, models_count: int, auth_count: int) -> str:
        """Estimate project complexity based on OpenAPI analysis"""
        score = tools_count + (models_count * 0.5) + (auth_count * 2)
        
        if score < 10:
            return "Simple"
        elif score < 30:
            return "Medium"
        elif score < 100:
            return "Complex"
        else:
            return "Very Complex"
    
    def _identify_issues(self, openapi_data: Dict[str, Any], endpoints: List, models: List) -> List[str]:
        """Identify potential issues with OpenAPI specification"""
        issues = []
        
        # Check for missing operation IDs
        missing_op_ids = [ep for ep in endpoints if not ep.get('operation_id')]
        if missing_op_ids:
            issues.append(f"{len(missing_op_ids)} endpoints missing operationId")
        
        # Check for authentication complexity
        security_schemes = openapi_data.get('components', {}).get('securitySchemes', {})
        if len(security_schemes) > 2:
            issues.append("Multiple authentication schemes may complicate implementation")
        
        # Check for file uploads
        has_file_uploads = any(
            'multipart/form-data' in str(ep.get('request_body', {}))
            for ep in endpoints
        )
        if has_file_uploads:
            issues.append("File upload endpoints require special handling")
        
        # Check for complex nested models
        complex_models = [
            model for model in models 
            if len(model.get('properties', {})) > 20
        ]
        if complex_models:
            issues.append(f"{len(complex_models)} models with >20 properties")
        
        return issues
    
    def _generate_openapi_models(self, project_path: Path, config, analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate Pydantic models from OpenAPI schemas"""
        
        service_dir = project_path / "src" / f"mcp_{config.service_name}"
        
        # Use existing models template for now
        models_content = self.render_template("python/models.py.j2", {
            "service_name": config.service_name,
            "models": analysis.models,
            "project_name": config.project_name
        })
        
        models_path = service_dir / "models.py"
        self.write_file(models_path, models_content)
        files_created.append(str(models_path))
    
    def _generate_openapi_client(self, project_path: Path, config, openapi_data: Dict[str, Any], 
                                analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate API client wrapper for OpenAPI endpoints"""
        
        service_dir = project_path / "src" / f"mcp_{config.service_name}"
        
        # Extract server information
        servers = openapi_data.get('servers', [{'url': 'https://api.example.com'}])
        base_url = servers[0]['url']
        
        # Extract authentication information
        security_schemes = openapi_data.get('components', {}).get('securitySchemes', {})
        
        # Use existing client template for now
        client_content = self.render_template("python/client.py.j2", {
            "service_name": config.service_name,
            "base_url": base_url,
            "endpoints": analysis.endpoints,
            "security_schemes": security_schemes,
            "project_name": config.project_name
        })
        
        client_path = service_dir / "client.py"
        self.write_file(client_path, client_content)
        files_created.append(str(client_path))
    
    def _generate_openapi_tools(self, project_path: Path, config, analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate MCP tools from OpenAPI endpoints"""
        
        service_dir = project_path / "src" / f"mcp_{config.service_name}"
        
        tools_content = self.render_template("openapi/tools.py.j2", {
            "service_name": config.service_name,
            "endpoints": analysis.endpoints,
            "project_name": config.project_name
        })
        
        tools_path = service_dir / "tools.py"
        self.write_file(tools_path, tools_content)
        files_created.append(str(tools_path))
    
    def _generate_openapi_server(self, project_path: Path, config, analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate main MCP server with OpenAPI integration"""
        
        service_dir = project_path / "src" / f"mcp_{config.service_name}"
        
        # Use existing server template for now
        server_content = self.render_template("python/server.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name,
            "description": config.description,
            "tools_count": analysis.tools_count,
            "models_count": len(analysis.models)
        })
        
        server_path = service_dir / "server.py"
        self.write_file(server_path, server_content)
        files_created.append(str(server_path))
    
    def _generate_openapi_tests(self, project_path: Path, config, analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate comprehensive tests for OpenAPI-based MCP server"""
        
        # Skip OpenAPI-specific tests for now - use existing test generation
        # TODO: Create OpenAPI-specific test templates
        pass
    
    def _generate_examples(self, project_path: Path, config, analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate usage examples and documentation"""
        
        # Skip examples for now - focus on core functionality
        # TODO: Create OpenAPI-specific example templates
        pass
    
    def _generate_openapi_config(self, project_path: Path, config, openapi_data: Dict[str, Any], files_created: List[str]):
        """Generate OpenAPI-specific configuration files"""
        
        # Skip OpenAPI config for now - use standard config
        # TODO: Create OpenAPI-specific config template
        pass

class MCSTestSuiteGenerator(BaseGenerator):
    """Generator for comprehensive test suites"""
    
    def generate(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """
        Generate test framework and basic test cases
        
        Args:
            project_path: Target project directory
            config: Project configuration
            
        Returns:
            GenerationResult: Generation result with created files
        """
        files_created = []
        errors = []
        
        try:
            # Generate pytest configuration
            self._generate_pytest_config(project_path, config, files_created)
            
            # Generate test fixtures
            self._generate_test_fixtures(project_path, config, files_created)
            
            # Generate basic test cases
            self._generate_basic_tests(project_path, config, files_created)
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )
            
        except Exception as e:
            errors.append(f"Failed to generate tests: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )
    
    def _generate_pytest_config(self, project_path: Path, config, files_created: List[str]):
        """Generate pytest configuration files"""
        
        # Generate conftest.py
        conftest_content = self.render_template("tests/conftest.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name
        })
        
        conftest_path = project_path / "tests" / "conftest.py"
        self.write_file(conftest_path, conftest_content)
        files_created.append(str(conftest_path))
        
        # Generate pytest.ini
        pytest_ini_content = self.render_template("tests/pytest.ini.j2", {
            "project_name": config.project_name,
            "service_name": config.service_name
        })
        
        pytest_ini_path = project_path / "pytest.ini"
        self.write_file(pytest_ini_path, pytest_ini_content)
        files_created.append(str(pytest_ini_path))
        
        # Generate .coveragerc
        coveragerc_content = self.render_template("tests/.coveragerc.j2", {
            "project_name": config.project_name,
            "service_name": config.service_name
        })
        
        coveragerc_path = project_path / ".coveragerc"
        self.write_file(coveragerc_path, coveragerc_content)
        files_created.append(str(coveragerc_path))
    
    def _generate_test_fixtures(self, project_path: Path, config, files_created: List[str]):
        """Generate test fixtures and mock data"""
        
        fixtures_content = self.render_template("tests/fixtures.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name
        })
        
        fixtures_path = project_path / "tests" / "fixtures" / "test_data.py"
        self.write_file(fixtures_path, fixtures_content)
        files_created.append(str(fixtures_path))
    
    def _generate_basic_tests(self, project_path: Path, config, files_created: List[str]):
        """Generate basic test cases for core components"""
        
        # Test for server module
        test_server_content = self.render_template("tests/test_server.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name
        })
        
        test_server_path = project_path / "tests" / "unit" / "test_server.py"
        self.write_file(test_server_path, test_server_content)
        files_created.append(str(test_server_path))
        
        # Test for config module
        test_config_content = self.render_template("tests/test_config.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name
        })
        
        test_config_path = project_path / "tests" / "unit" / "test_config.py"
        self.write_file(test_config_path, test_config_content)
        files_created.append(str(test_config_path))

class DockerGenerator(BaseGenerator):
    """Generator for Docker deployment configuration"""
    
    def generate(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """
        Generate Docker configuration for deployment
        
        Args:
            project_path: Target project directory
            config: Project configuration
            
        Returns:
            GenerationResult: Generation result with created files
        """
        files_created = []
        errors = []
        
        try:
            # Generate Dockerfile
            dockerfile_content = self.render_template("docker/Dockerfile.j2", {
                "project_name": config.project_name,
                "service_name": config.service_name,
                "python_version": config.python_version
            })
            
            dockerfile_path = project_path / "docker" / "Dockerfile"
            self.write_file(dockerfile_path, dockerfile_content)
            files_created.append(str(dockerfile_path))
            
            # Generate docker-compose.yml
            compose_content = self.render_template("docker/docker-compose.yml.j2", {
                "project_name": config.project_name,
                "service_name": config.service_name
            })
            
            compose_path = project_path / "docker" / "docker-compose.yml"
            self.write_file(compose_path, compose_content)
            files_created.append(str(compose_path))
            
            # Generate .dockerignore
            dockerignore_content = self.render_template("docker/.dockerignore.j2", {})
            
            dockerignore_path = project_path / ".dockerignore"
            self.write_file(dockerignore_path, dockerignore_content)
            files_created.append(str(dockerignore_path))
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )
            
        except Exception as e:
            errors.append(f"Failed to generate Docker configuration: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )

class ConfigGenerator(BaseGenerator):
    """Generator for configuration management"""
    
    def generate(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """
        Generate configuration management files
        
        Args:
            project_path: Target project directory
            config: Project configuration
            
        Returns:
            GenerationResult: Generation result with created files
        """
        files_created = []
        errors = []
        
        try:
            # Generate server configuration
            server_config_content = self.render_template("config/server_config.yaml.j2", {
                "project_name": config.project_name,
                "service_name": config.service_name,
                "version": config.version
            })
            
            server_config_path = project_path / "config" / "server_config.yaml"
            self.write_file(server_config_path, server_config_content)
            files_created.append(str(server_config_path))
            
            # Generate logging configuration
            logging_config_content = self.render_template("config/logging.yaml.j2", {
                "project_name": config.project_name
            })
            
            logging_config_path = project_path / "config" / "logging.yaml"
            self.write_file(logging_config_path, logging_config_content)
            files_created.append(str(logging_config_path))
            
            # Generate startup script
            startup_script_content = self.render_template("scripts/run_server.py.j2", {
                "service_name": config.service_name,
                "project_name": config.project_name
            })
            
            startup_script_path = project_path / "scripts" / "run_server.py"
            self.write_file(startup_script_path, startup_script_content)
            files_created.append(str(startup_script_path))
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )
            
        except Exception as e:
            errors.append(f"Failed to generate configuration: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=files_created,
                errors=errors,
                warnings=[]
            )

class OpenAPIEnhancedGenerator(OpenAPIGenerator):
    """Enhanced OpenAPI generator using openapi-generator
    
    This generator extends OpenAPIGenerator but uses openapi-generator to create
    a more robust Python API client instead of the template-based approach.
    
    The generation process:
    1. Uses OpenAPIClientGenerator to create Python API client
    2. Uses MCPToolMapper to generate enhanced MCPProjectConfig from client analysis
    3. Uses MCPGenerator to generate the complete MCP server project
    4. Overrides client generation to use the openapi-generator approach
    """
    
    def __init__(self):
        super().__init__()
        self.client_generator = OpenAPIClientGenerator()
        self.mcp_generator = None  # Will be instantiated when needed
        self.logger = logging.getLogger(__name__)
        
    def generate(self, project_path: Path, config: MCPProjectConfig, openapi_data: Dict[str, Any], 
                include_examples: bool = False, max_tools: int = 50) -> GenerationResult:
        """Generate MCP server using openapi-generator for client and MCPGenerator for project
        
        New Architecture:
        1. Use OpenAPIClientGenerator to create client code
        2. Use MCPToolMapper to generate enhanced MCPProjectConfig from client analysis  
        3. Use MCPGenerator to generate the complete MCP server project
        
        Args:
            project_path: Target project directory
            config: Project configuration
            openapi_data: Parsed OpenAPI specification
            include_examples: Whether to generate usage examples
            max_tools: Maximum number of tools to generate
            
        Returns:
            GenerationResult: Combined result from all generation phases
        """
        all_files_created = []
        all_errors = []
        all_warnings = []
        
        try:
            print("🔧 OpenAPIEnhancedGenerator: Starting generation phases...")
            
            # Phase 1: Generate API client using openapi-generator
            print("📦 Phase 1: Generating API client with openapi-generator-cli...")
            client_result = self._generate_api_client_with_generator(project_path, config, openapi_data)
            all_files_created.extend(client_result.files_created)
            all_errors.extend(client_result.errors)
            all_warnings.extend(client_result.warnings)
            print(f"✅ Phase 1 complete: {len(client_result.files_created)} files created, success={client_result.success}")
            
            if not client_result.success:
                print("❌ Phase 1 failed - cannot proceed")
                return GenerationResult(
                    success=False,
                    files_created=all_files_created,
                    errors=all_errors + ["API client generation failed - cannot proceed"],
                    warnings=all_warnings
                )
            
            # Phase 2: Analyze generated client
            print("🔍 Phase 2: Analyzing generated client...")
            client_analysis = self._analyze_generated_client(project_path, config)
            if not client_analysis:
                print("❌ Phase 2 failed - client analysis failed")
                return GenerationResult(
                    success=False,
                    files_created=all_files_created,
                    errors=all_errors + ["Failed to analyze generated client"],
                    warnings=all_warnings
                )
            print(f"✅ Phase 2 complete: Found {len(client_analysis.operations)} operations")
            
            # Phase 3: Generate enhanced MCPProjectConfig using MCPToolMapper
            print("⚙️ Phase 3: Generating enhanced configuration...")
            enhanced_config = self._generate_enhanced_config(config, client_analysis, max_tools)
            print("✅ Phase 3 complete: Enhanced configuration generated")
            
            # Phase 4: Use MCPGenerator to generate the complete MCP project
            print("🏗️ Phase 4: Generating complete MCP project...")
            mcp_result = self._generate_mcp_project(project_path, enhanced_config, openapi_data, include_examples)
            all_files_created.extend(mcp_result.files_created)
            all_errors.extend(mcp_result.errors)
            all_warnings.extend(mcp_result.warnings)
            print(f"✅ Phase 4 complete: {len(mcp_result.files_created)} additional files created, success={mcp_result.success}")
            
            # Determine overall success
            overall_success = client_result.success and mcp_result.success
            
            return GenerationResult(
                success=overall_success,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
            
        except Exception as e:
            all_errors.append(f"OpenAPI enhanced generation failed: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
    
    def _generate_api_client_with_generator(self, project_path: Path, config: MCPProjectConfig, openapi_data: Dict[str, Any]) -> GenerationResult:
        """Generate API client using openapi-generator"""
        try:
            print("📦 Setting up client generation...")
            
            # Prepare client output directory - use project_path directly to avoid duplication
            client_dir = project_path / "generated_client"
            print(f"📁 Client output directory: {client_dir}")
            
            # Write OpenAPI spec to temporary file if needed
            if config.openapi_spec:
                spec_path = config.openapi_spec
                print(f"📄 Using provided OpenAPI spec: {spec_path}")
            else:
                # Write openapi_data to temporary file
                import tempfile
                import json
                print("📝 Writing OpenAPI data to temporary file...")
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(openapi_data, f, indent=2)
                    spec_path = f.name
                print(f"📄 Temporary OpenAPI spec: {spec_path}")
            
            # Generate client using openapi-generator
            print("🚀 Calling openapi-generator-cli (this may take 1-2 minutes)...")
            print("⏳ Please wait while openapi-generator-cli processes the specification...")
            
            result = self.client_generator.generate_python_client(
                spec_path=spec_path,
                output_dir=client_dir,
                config=config.openapi_config
            )
            
            print(f"🎯 openapi-generator-cli completed: success={result.success}")
            if result.errors:
                print(f"⚠️ Errors: {result.errors}")
            if result.warnings:
                print(f"📝 Warnings: {len(result.warnings)} warnings")
            
            return result
            
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"API client generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _analyze_generated_client(self, project_path: Path, config: MCPProjectConfig) -> Optional[ClientAnalysis]:
        """Analyze generated client to extract operations and models"""
        try:
            # Use the same path as generation to avoid duplication
            client_dir = project_path / "generated_client"
            
            # Parse the generated client
            client_analysis = self.client_generator.parse_generated_client(client_dir)
            
            # Validate the client
            validation_result = self.client_generator.validate_generated_client(client_dir)
            if not validation_result.is_valid:
                self.logger.warning(f"Generated client validation issues: {validation_result.errors}")
            
            # Filter out excluded methods (like _with_http_info) to avoid duplicate tools
            filtered_analysis = self._filter_excluded_methods(client_analysis, config)
            
            # Store filtered client analysis for later use in tool generation
            self._client_analysis = filtered_analysis
            
            return filtered_analysis
            
        except Exception as e:
            self.logger.error(f"Failed to analyze generated client: {e}")
            return None
    
    def _filter_excluded_methods(self, client_analysis: ClientAnalysis, config: MCPProjectConfig) -> ClientAnalysis:
        """
        Filter out methods that match exclusion patterns from MCPIntegrationConfig
        
        This removes duplicate methods like 'get_posts_with_http_info' when 'get_posts' exists,
        keeping only the main methods for cleaner MCP tools.
        
        Args:
            client_analysis: Original client analysis from openapi-generator
            config: Project configuration with MCP integration settings
            
        Returns:
            ClientAnalysis: Filtered analysis with excluded methods removed
        """
        if not config.mcp_config.excluded_method_patterns:
            return client_analysis
        
        # Create a filtered copy of the client analysis
        filtered_analysis = ClientAnalysis(
            api_classes=[],
            operations=[],
            models=client_analysis.models,  # Models don't need filtering
            client_package_name=client_analysis.client_package_name,
            base_url=client_analysis.base_url,
            auth_schemes=client_analysis.auth_schemes
        )
        
        # Filter operations
        for operation in client_analysis.operations:
            if not config.mcp_config.is_method_excluded(operation.name):
                filtered_analysis.operations.append(operation)
            else:
                self.logger.debug(f"Excluding operation: {operation.name} (matches exclusion pattern)")
        
        # Filter API class methods
        from .openapi_client_generator import ApiClass
        for api_class in client_analysis.api_classes:
            filtered_methods = []
            for method_name in api_class.methods:
                if not config.mcp_config.is_method_excluded(method_name):
                    filtered_methods.append(method_name)
                else:
                    self.logger.debug(f"Excluding method: {api_class.name}.{method_name} (matches exclusion pattern)")
            
            # Only include API class if it has remaining methods
            if filtered_methods:
                filtered_api_class = ApiClass(
                    name=api_class.name,
                    module=api_class.module,
                    methods=filtered_methods,
                    file_path=api_class.file_path
                )
                filtered_analysis.api_classes.append(filtered_api_class)
        
        self.logger.info(f"Filtered methods: {len(client_analysis.operations)} -> {len(filtered_analysis.operations)} operations")
        return filtered_analysis
    
    def _generate_mcp_tools(self, project_path: Path, config: MCPProjectConfig, 
                           client_analysis: ClientAnalysis, max_tools: int) -> GenerationResult:
        """Generate MCP tools from API operations"""
        try:
            from .mcp_tool_mapper import MCPToolMapper
            
            # Create tool mapper
            self.tool_mapper = MCPToolMapper(client_analysis)
            
            # Generate tool definitions
            tool_definitions = self.tool_mapper.generate_tool_definitions()
            
            # Limit number of tools if specified
            if max_tools and len(tool_definitions) > max_tools:
                tool_definitions = tool_definitions[:max_tools]
                self.logger.warning(f"Limited tools to {max_tools} (was {len(tool_definitions)})")
            
            # Enhance operations with tool information for template
            enhanced_operations = []
            for i, operation in enumerate(client_analysis.operations):
                if i < len(tool_definitions):
                    tool_def = tool_definitions[i]
                    enhanced_op = {
                        'tool_name': tool_def.name,
                        'operation_name': operation.name,
                        'api_class': operation.api_class,
                        'method': operation.method,
                        'path': operation.path,
                        'summary': operation.summary,
                        'description': operation.description,
                        'parameters': operation.parameters,
                        'input_schema': tool_def.input_schema,
                        'request_body_type': operation.request_body_type
                    }
                    enhanced_operations.append(enhanced_op)
            
            # Generate class name from service name
            class_name = config.service_name.title().replace('_', '')
            
            # Generate tools.py file
            service_dir = config.get_mcp_package_path()
            
            tools_content = self.render_template("openapi_enhanced/tools.py.j2", {
                "service_name": config.service_name,
                "project_name": config.project_name,
                "class_name": class_name,
                "client_package_name": client_analysis.client_package_name,
                "tool_definitions": tool_definitions,
                "api_classes": client_analysis.api_classes,
                "operations": enhanced_operations,  # Use enhanced operations
                "base_url": client_analysis.base_url,
                "auth_schemes": client_analysis.auth_schemes
            })
            
            tools_path = service_dir / "tools.py"
            self.write_file(tools_path, tools_content)
            
            print(f"🔧 Generated tools.py with {len(enhanced_operations)} OpenAPI tools")
            
            return GenerationResult(
                success=True,
                files_created=[str(tools_path)],
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"MCP tools generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_mcp_server(self, project_path: Path, config: MCPProjectConfig, 
                            client_analysis: ClientAnalysis) -> GenerationResult:
        """Generate MCP server with API client integration"""
        try:
            service_dir = config.get_mcp_package_path()
            
            # Generate server.py file
            server_content = self.render_template("openapi_enhanced/server.py.j2", {
                "service_name": config.service_name,
                "project_name": config.project_name,
                "description": config.description,
                "client_package_name": client_analysis.client_package_name,
                "api_classes": client_analysis.api_classes,
                "base_url": client_analysis.base_url,
                "auth_schemes": client_analysis.auth_schemes,
                "tools_count": len(client_analysis.operations)
            })
            
            server_path = service_dir / "server.py"
            self.write_file(server_path, server_content)
            
            # Generate __init__.py file
            init_content = self.render_template("python/__init__.py.j2", {
                "service_name": config.service_name,
                "project_name": config.project_name
            })
            
            init_path = service_dir / "__init__.py"
            self.write_file(init_path, init_content)
            
            return GenerationResult(
                success=True,
                files_created=[str(server_path), str(init_path)],
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"MCP server generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_documentation(self, project_path: Path, config: MCPProjectConfig, 
                               client_analysis: ClientAnalysis, include_examples: bool) -> GenerationResult:
        """Generate documentation and examples"""
        try:
            files_created = []
            
            # Generate API documentation
            docs_dir = project_path / "docs"
            
            api_docs_content = self.render_template("docs/api_reference.md.j2", {
                "project_name": config.project_name,
                "service_name": config.service_name,
                "client_analysis": client_analysis,
                "operations": client_analysis.operations,
                "models": client_analysis.models
            })
            
            api_docs_path = docs_dir / "api_reference.md"
            self.write_file(api_docs_path, api_docs_content)
            files_created.append(str(api_docs_path))
            
            # Generate usage examples if requested
            if include_examples:
                examples_content = self.render_template("docs/usage_examples.md.j2", {
                    "project_name": config.project_name,
                    "service_name": config.service_name,
                    "operations": client_analysis.operations[:5]  # Limit to first 5 operations
                })
                
                examples_path = docs_dir / "usage_examples.md"
                self.write_file(examples_path, examples_content)
                files_created.append(str(examples_path))
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"Documentation generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_enhanced_config(self, base_config: MCPProjectConfig, client_analysis: ClientAnalysis, max_tools: int) -> MCPProjectConfig:
        """Generate enhanced MCPProjectConfig using MCPToolMapper
        
        Takes the base configuration and enhances it with information derived
        from the client analysis using MCPToolMapper.
        
        Args:
            base_config: Original project configuration
            client_analysis: Analysis of generated API client
            max_tools: Maximum number of tools to generate
            
        Returns:
            MCPProjectConfig: Enhanced configuration
        """
        try:
            from .mcp_tool_mapper import MCPToolMapper
            
            # Create tool mapper from client analysis
            tool_mapper = MCPToolMapper(client_analysis)
            
            # Generate enhanced project config
            enhanced_config = tool_mapper.generate_mcp_project_config(
                project_name=base_config.project_name,
                author=base_config.author,
                description=base_config.description,
                version=base_config.version,
                # Pass through other base config settings
                output_dir=base_config.output_dir,
                include_docker=base_config.include_docker,
                include_ci=base_config.include_ci,
                test_framework=base_config.test_framework,
                openapi_spec=base_config.openapi_spec,
                openapi_url=base_config.openapi_url
            )
            
            # Apply max_tools limit to the enhanced config
            if enhanced_config.mcp_config.max_tools > max_tools:
                enhanced_config.mcp_config.max_tools = max_tools
            
            self.logger.info(f"Enhanced config generated with {enhanced_config.mcp_config.max_tools} max tools")
            return enhanced_config
            
        except Exception as e:
            self.logger.error(f"Failed to generate enhanced config: {e}")
            # Fallback to base config if enhancement fails
            return base_config
    
    def _generate_mcp_project(self, project_path: Path, enhanced_config: MCPProjectConfig, 
                             openapi_data: Dict[str, Any], include_examples: bool) -> GenerationResult:
        """Generate complete MCP project with OpenAPI tools
        
        Generates the complete MCP project including standard project structure
        AND OpenAPI-derived tools using the client analysis.
        
        Args:
            project_path: Target project directory
            enhanced_config: Enhanced project configuration
            openapi_data: Original OpenAPI specification
            include_examples: Whether to generate examples
            
        Returns:
            GenerationResult: Result of MCP project generation
        """
        try:
            all_files_created = []
            all_errors = []
            all_warnings = []
            
            # Import MCPGenerator here to avoid circular imports
            if self.mcp_generator is None:
                self.mcp_generator = MCPGenerator()
            
            # Phase 4a: Generate standard MCP project structure
            print("🏗️ Phase 4a: Generating standard project structure...")
            standard_result = self.mcp_generator.generate(
                project_path=project_path,
                config=enhanced_config
            )
            all_files_created.extend(standard_result.files_created)
            all_errors.extend(standard_result.errors)
            all_warnings.extend(standard_result.warnings)
            print(f"✅ Phase 4a complete: {len(standard_result.files_created)} files created")
            
            # Phase 4b: Generate OpenAPI-specific tools (override the default tools.py)
            print("🔧 Phase 4b: Generating OpenAPI tools...")
            if hasattr(self, '_client_analysis') and self._client_analysis:
                tools_result = self._generate_mcp_tools(
                    project_path, enhanced_config, self._client_analysis, enhanced_config.mcp_config.max_tools
                )
                all_files_created.extend(tools_result.files_created)
                all_errors.extend(tools_result.errors)
                all_warnings.extend(tools_result.warnings)
                print(f"✅ Phase 4b complete: Generated tools from {len(self._client_analysis.operations)} operations")
            else:
                all_warnings.append("No client analysis available - tools.py will contain default tools only")
                print("⚠️ Phase 4b warning: No client analysis available")
            
            # Phase 4c: Generate enhanced server (override the default server.py)
            print("🖥️ Phase 4c: Generating enhanced server...")
            if hasattr(self, '_client_analysis') and self._client_analysis:
                server_result = self._generate_mcp_server(
                    project_path, enhanced_config, self._client_analysis
                )
                all_files_created.extend(server_result.files_created)
                all_errors.extend(server_result.errors)
                all_warnings.extend(server_result.warnings)
                print("✅ Phase 4c complete: Enhanced server generated")
            
            # Phase 4d: Generate documentation
            if include_examples and hasattr(self, '_client_analysis') and self._client_analysis:
                print("📚 Phase 4d: Generating documentation...")
                docs_result = self._generate_documentation(
                    project_path, enhanced_config, self._client_analysis, include_examples
                )
                all_files_created.extend(docs_result.files_created)
                all_errors.extend(docs_result.errors)
                all_warnings.extend(docs_result.warnings)
                print("✅ Phase 4d complete: Documentation generated")
            
            # Determine overall success
            overall_success = standard_result.success
            if all_errors:
                overall_success = False
            
            self.logger.info(f"Complete MCP project generation: success={overall_success}")
            return GenerationResult(
                success=overall_success,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
            
        except Exception as e:
            self.logger.error(f"Failed to generate MCP project: {e}")
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"MCP project generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_openapi_client(self, project_path: Path, config, openapi_data: Dict[str, Any], 
                                analysis: OpenAPIAnalysis, files_created: List[str]):
        """Override parent's client generation to use openapi-generator
        
        This method overrides the parent's template-based client generation
        to use openapi-generator for more robust client code generation.
        """
        try:
            # Phase 1: Generate API client using openapi-generator
            client_result = self._generate_api_client_with_generator(project_path, config, openapi_data)
            if not client_result.success:
                return client_result
            
            files_created.extend(client_result.files_created)
            
            # Phase 2: Analyze the generated client
            client_analysis = self._analyze_generated_client(project_path, config)
            if not client_analysis:
                return GenerationResult(
                    success=False,
                    files_created=files_created,
                    errors=["Failed to analyze generated client"],
                    warnings=[]
                )
            
            # Store client analysis for later use
            self._client_analysis = client_analysis
            
            return GenerationResult(
                success=True,
                files_created=files_created,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=files_created,
                errors=[f"Enhanced client generation failed: {str(e)}"],
                warnings=[]
            )

class MCPGenerator(BaseGenerator):
    """
    Generator for complete MCP server projects
    
    Orchestrates the generation of a standard MCP project by coordinating
    multiple specialized generators. Creates a production-ready MCP server
    with proper project structure, configuration, tests, and optional Docker setup.
    """
    
    def __init__(self):
        """Initialize MCP generator with component generators"""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.structure_generator = ProjectStructureGenerator()
        self.test_generator = TestGenerator()
        self.config_generator = ConfigGenerator()
        self.docker_generator = DockerGenerator()
        self.openapi_enhanced_generator = OpenAPIEnhancedGenerator()
    
    def generate(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """
        Generate complete MCP server project
        
        Creates a comprehensive MCP server project including:
        - Project structure and core Python files
        - Configuration management
        - Test framework and basic test cases
        - Docker deployment setup (optional)
        
        Args:
            project_path: Target project directory
            config: Project configuration containing all generation settings
            
        Returns:
            GenerationResult: Aggregated result from all component generators
            
        Example:
            generator = MCPGenerator()
            config = MCPProjectConfig(
                project_name="my-mcp-server",
                service_name="my_service",
                description="My MCP server",
                author="Developer"
            )
            result = generator.generate(Path("./output"), config)
        """
        all_files_created = []
        all_errors = []
        all_warnings = []
        
        try:
            # Phase 1: Generate project structure and core files
            structure_result = self._generate_project_structure(project_path, config)
            all_files_created.extend(structure_result.files_created)
            all_errors.extend(structure_result.errors)
            all_warnings.extend(structure_result.warnings)
            
            if not structure_result.success:
                all_warnings.append("Project structure generation failed, continuing with other components")
            
            # Phase 2: Generate configuration files
            config_result = self._generate_configuration(project_path, config)
            all_files_created.extend(config_result.files_created)
            all_errors.extend(config_result.errors)
            all_warnings.extend(config_result.warnings)
            
            if not config_result.success:
                all_warnings.append("Configuration generation failed, continuing with other components")
            
            # Phase 3: Generate test framework
            test_result = self._generate_tests(project_path, config)
            all_files_created.extend(test_result.files_created)
            all_errors.extend(test_result.errors)
            all_warnings.extend(test_result.warnings)
            
            if not test_result.success:
                all_warnings.append("Test generation failed, continuing with other components")
            
            # Phase 4: Generate Docker setup (optional)
            docker_result = None
            if config.include_docker:
                docker_result = self._generate_docker(project_path, config)
                all_files_created.extend(docker_result.files_created)
                all_errors.extend(docker_result.errors)
                all_warnings.extend(docker_result.warnings)
                
                if not docker_result.success:
                    all_warnings.append("Docker generation failed")
            
            # Phase 5: Generate project summary
            summary_result = self._generate_project_summary(project_path, config, all_files_created)
            if summary_result:
                all_files_created.append(summary_result)
            
            # Determine overall success
            critical_failures = [
                not structure_result.success,
                not config_result.success,
                not test_result.success
            ]
            
            overall_success = not any(critical_failures)
            
            if not overall_success:
                all_errors.append("One or more critical components failed to generate")
            
            return GenerationResult(
                success=overall_success,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
            
        except Exception as e:
            all_errors.append(f"Failed to generate MCP project: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
    
    def _generate_project_structure(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """Generate project structure using ProjectStructureGenerator"""
        try:
            return self.structure_generator.generate(project_path, config)
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"Project structure generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_configuration(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """Generate configuration files using ConfigGenerator"""
        try:
            return self.config_generator.generate(project_path, config)
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"Configuration generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_tests(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """Generate test framework using TestGenerator"""
        try:
            return self.test_generator.generate(project_path, config)
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"Test generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_docker(self, project_path: Path, config: MCPProjectConfig) -> GenerationResult:
        """Generate Docker configuration using DockerGenerator"""
        try:
            return self.docker_generator.generate(project_path, config)
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"Docker generation failed: {str(e)}"],
                warnings=[]
            )
    
    def _generate_project_summary(self, project_path: Path, config: MCPProjectConfig, files_created: List[str]) -> str:
        """Generate a project summary file with generation details"""
        try:
            summary_content = self.render_template("project/PROJECT_SUMMARY.md.j2", {
                "project_name": config.project_name,
                "service_name": config.service_name,
                "description": config.description,
                "author": config.author,
                "version": config.version,
                "python_version": config.python_version,
                "test_framework": config.test_framework,
                "include_docker": config.include_docker,
                "include_ci": config.include_ci,
                "files_created": files_created,
                "file_count": len(files_created) + 1  # +1 for the summary file itself
            })
            
            summary_path = project_path / "PROJECT_SUMMARY.md"
            self.write_file(summary_path, summary_content)
            return str(summary_path)
            
        except Exception as e:
            # Don't fail the entire generation for summary file issues
            return None
    
    def get_generation_order(self) -> List[str]:
        """
        Get the order in which components are generated
        
        Returns:
            List[str]: Ordered list of generation phases
        """
        return [
            "Project Structure",
            "Configuration Files", 
            "Test Framework",
            "Docker Setup (optional)",
            "Project Summary"
        ]
    
    def validate_config(self, config: MCPProjectConfig) -> List[str]:
        """
        Validate project configuration before generation
        
        Args:
            config: Project configuration to validate
            
        Returns:
            List[str]: List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields validation
        if not config.project_name or not config.project_name.strip():
            errors.append("Project name is required")
        
        if not config.service_name or not config.service_name.strip():
            errors.append("Service name is required")
        
        if not config.description or not config.description.strip():
            errors.append("Project description is required")
        
        if not config.author or not config.author.strip():
            errors.append("Author is required")
        
        # Format validation
        if config.project_name and not re.match(r'^[a-zA-Z0-9\-_]+$', config.project_name):
            errors.append("Project name can only contain letters, numbers, hyphens, and underscores")
        
        if config.service_name and not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', config.service_name):
            errors.append("Service name must be a valid Python identifier")
        
        # Python version validation
        if config.python_version and not re.match(r'^\d+\.\d+$', config.python_version):
            errors.append("Python version must be in format 'X.Y' (e.g., '3.11')")
        
        return errors
    
    def generate_from_openapi(self, project_path: Path, config: MCPProjectConfig, 
                             openapi_data: Dict[str, Any], include_examples: bool = False, 
                             max_tools: int = 50) -> GenerationResult:
        """
        Generate complete MCP server project from OpenAPI specification
        
        Creates a comprehensive MCP server project that includes:
        - Standard project structure and configuration
        - Generated API client from OpenAPI spec
        - MCP tools mapped from API operations
        - Enhanced server with API integration
        - Comprehensive tests and documentation
        
        Args:
            project_path: Target project directory
            config: Project configuration containing all generation settings
            openapi_data: Parsed OpenAPI specification
            include_examples: Whether to generate usage examples
            max_tools: Maximum number of tools to generate from API operations
            
        Returns:
            GenerationResult: Aggregated result from all component generators
            
        Example:
            generator = MCPGenerator()
            config = MCPProjectConfig.from_openapi_spec("api.json", author="Developer")
            
            with open("api.json") as f:
                openapi_data = json.load(f)
                
            result = generator.generate_from_openapi(
                Path("./output"), 
                config, 
                openapi_data,
                include_examples=True,
                max_tools=25
            )
        """
        all_files_created = []
        all_errors = []
        all_warnings = []
        
        try:
            # Phase 1: Generate standard project structure first
            # Direct call to avoid recursion - don't use self.generate()
            structure_result = self._generate_project_structure(project_path, config)
            all_files_created.extend(structure_result.files_created)
            all_errors.extend(structure_result.errors)
            all_warnings.extend(structure_result.warnings)
            
            # Generate configuration
            config_result = self._generate_configuration(project_path, config)
            all_files_created.extend(config_result.files_created)
            all_errors.extend(config_result.errors)
            all_warnings.extend(config_result.warnings)
            
            # Generate tests
            test_result = self._generate_tests(project_path, config)
            all_files_created.extend(test_result.files_created)
            all_errors.extend(test_result.errors)
            all_warnings.extend(test_result.warnings)
            
            # Generate Docker (optional)
            if config.include_docker:
                docker_result = self._generate_docker(project_path, config)
                all_files_created.extend(docker_result.files_created)
                all_errors.extend(docker_result.errors)
                all_warnings.extend(docker_result.warnings)
            
            standard_success = structure_result.success and config_result.success and test_result.success
            if not standard_success:
                all_warnings.append("Standard project generation had issues, continuing with OpenAPI generation")
            
            # Phase 2: Generate OpenAPI-enhanced components
            openapi_result = self.openapi_enhanced_generator.generate(
                project_path, 
                config, 
                openapi_data,
                include_examples=include_examples,
                max_tools=max_tools
            )
            all_files_created.extend(openapi_result.files_created)
            all_errors.extend(openapi_result.errors)
            all_warnings.extend(openapi_result.warnings)
            
            # Phase 3: Update project summary with OpenAPI information
            summary_result = self._generate_openapi_project_summary(
                project_path, config, all_files_created, openapi_data
            )
            if summary_result:
                all_files_created.append(summary_result)
            
            # Determine overall success
            overall_success = standard_success and openapi_result.success
            
            if not overall_success:
                all_errors.append("One or more components failed during OpenAPI project generation")
            
            return GenerationResult(
                success=overall_success,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
            
        except Exception as e:
            all_errors.append(f"Failed to generate OpenAPI MCP project: {str(e)}")
            return GenerationResult(
                success=False,
                files_created=all_files_created,
                errors=all_errors,
                warnings=all_warnings
            )
    
    def _generate_openapi_project_summary(self, project_path: Path, config: MCPProjectConfig, 
                                         files_created: List[str], openapi_data: Dict[str, Any]) -> str:
        """Generate enhanced project summary with OpenAPI information"""
        try:
            # Extract OpenAPI info
            info = openapi_data.get('info', {})
            paths = openapi_data.get('paths', {})
            components = openapi_data.get('components', {})
            
            # Count operations
            operations_count = sum(len(methods) for methods in paths.values() if isinstance(methods, dict))
            
            # Count models
            models_count = len(components.get('schemas', {}))
            
            summary_content = self.render_template("project/PROJECT_SUMMARY.md.j2", {
                "project_name": config.project_name,
                "service_name": config.service_name,
                "description": config.description,
                "author": config.author,
                "version": config.version,
                "python_version": config.python_version,
                "test_framework": config.test_framework,
                "include_docker": config.include_docker,
                "include_ci": config.include_ci,
                "files_created": files_created,
                "file_count": len(files_created) + 1,  # +1 for the summary file itself
                "openapi_info": {
                    "title": info.get('title', 'Unknown API'),
                    "version": info.get('version', '1.0.0'),
                    "description": info.get('description', ''),
                    "operations_count": operations_count,
                    "models_count": models_count,
                    "base_url": openapi_data.get('servers', [{}])[0].get('url', '') if openapi_data.get('servers') else ''
                }
            })
            
            summary_path = project_path / "PROJECT_SUMMARY.md"
            self.write_file(summary_path, summary_content)
            return str(summary_path)
            
        except Exception as e:
            # Don't fail the entire generation for summary file issues
            self.logger.warning(f"Failed to generate OpenAPI project summary: {e}")
            return None