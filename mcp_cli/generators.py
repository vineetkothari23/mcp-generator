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
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from jinja2 import Environment, FileSystemLoader, Template
import re
from urllib.parse import urlparse

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
    
    def generate(self, project_path: Path, config) -> GenerationResult:
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
    """Generator for OpenAPI-specific MCP server components"""
    
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
                if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoints.append({
                        'path': path,
                        'method': method.upper(),
                        'operation_id': operation.get('operationId'),
                        'summary': operation.get('summary'),
                        'description': operation.get('description'),
                        'parameters': operation.get('parameters', []),
                        'request_body': operation.get('requestBody'),
                        'responses': operation.get('responses', {})
                    })
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
    
    def generate(self, project_path: Path, config, openapi_data: Dict[str, Any], 
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
        
        models_content = self.render_template("openapi/models.py.j2", {
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
        
        client_content = self.render_template("openapi/client.py.j2", {
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
        
        server_content = self.render_template("openapi/server.py.j2", {
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
        
        # Generate unit tests for tools
        test_tools_content = self.render_template("openapi/test_tools.py.j2", {
            "service_name": config.service_name,
            "endpoints": analysis.endpoints[:5],  # Sample of endpoints for testing
            "project_name": config.project_name
        })
        
        test_tools_path = project_path / "tests" / "unit" / "test_tools.py"
        self.write_file(test_tools_path, test_tools_content)
        files_created.append(str(test_tools_path))
        
        # Generate integration tests
        test_integration_content = self.render_template("openapi/test_integration.py.j2", {
            "service_name": config.service_name,
            "project_name": config.project_name
        })
        
        test_integration_path = project_path / "tests" / "integration" / "test_api_integration.py"
        self.write_file(test_integration_path, test_integration_content)
        files_created.append(str(test_integration_path))
    
    def _generate_examples(self, project_path: Path, config, analysis: OpenAPIAnalysis, files_created: List[str]):
        """Generate usage examples and documentation"""
        
        examples_content = self.render_template("openapi/examples.py.j2", {
            "service_name": config.service_name,
            "endpoints": analysis.endpoints[:3],  # Show first 3 endpoints as examples
            "project_name": config.project_name
        })
        
        examples_path = project_path / "examples" / "usage_examples.py"
        self.write_file(examples_path, examples_content)
        files_created.append(str(examples_path))
        
        # Generate usage documentation
        usage_doc_content = self.render_template("openapi/USAGE.md.j2", {
            "project_name": config.project_name,
            "service_name": config.service_name,
            "endpoints": analysis.endpoints,
            "tools_count": analysis.tools_count
        })
        
        usage_doc_path = project_path / "docs" / "USAGE_EXAMPLES.md"
        self.write_file(usage_doc_path, usage_doc_content)
        files_created.append(str(usage_doc_path))
    
    def _generate_openapi_config(self, project_path: Path, config, openapi_data: Dict[str, Any], files_created: List[str]):
        """Generate OpenAPI-specific configuration files"""
        
        # Extract server and security information for configuration
        servers = openapi_data.get('servers', [])
        security_schemes = openapi_data.get('components', {}).get('securitySchemes', {})
        
        config_content = self.render_template("openapi/api_config.yaml.j2", {
            "project_name": config.project_name,
            "service_name": config.service_name,
            "servers": servers,
            "security_schemes": security_schemes,
            "api_info": openapi_data.get('info', {})
        })
        
        config_path = project_path / "config" / "api_config.yaml"
        self.write_file(config_path, config_content)
        files_created.append(str(config_path))

class TestGenerator(BaseGenerator):
    """Generator for comprehensive test suites"""
    
    def generate(self, project_path: Path, config) -> GenerationResult:
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
            "project_name": config.project_name
        })
        
        pytest_ini_path = project_path / "pytest.ini"
        self.write_file(pytest_ini_path, pytest_ini_content)
        files_created.append(str(pytest_ini_path))
    
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
    
    def generate(self, project_path: Path, config) -> GenerationResult:
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
    
    def generate(self, project_path: Path, config) -> GenerationResult:
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