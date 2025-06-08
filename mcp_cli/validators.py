"""
MCP Server Validators - Validation utilities for OpenAPI specs and projects

This module provides comprehensive validation for:
- OpenAPI specification compliance
- MCP server project structure
- Configuration files
- Test coverage and quality

All validators follow a consistent pattern and provide detailed error reporting.
"""

import json
import yaml
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
import importlib.util
import ast

@dataclass
class ValidationResult:
    """Result of validation operation with detailed feedback"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    suggestions: List[str]

class OpenAPIValidator:
    """Validator for OpenAPI specifications"""
    
    def __init__(self):
        """Initialize OpenAPI validator with required fields and patterns"""
        self.required_root_fields = ['openapi', 'info', 'paths']
        self.required_info_fields = ['title', 'version']
        self.supported_versions = ['3.0.0', '3.0.1', '3.0.2', '3.0.3', '3.1.0']
        self.http_methods = {'get', 'post', 'put', 'delete', 'patch', 'head', 'options', 'trace'}
    
    def validate(self, openapi_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate OpenAPI specification for MCP server generation
        
        Args:
            openapi_data: Parsed OpenAPI specification
            
        Returns:
            ValidationResult: Comprehensive validation result
            
        Example:
            validator = OpenAPIValidator()
            result = validator.validate(openapi_spec)
            if not result.is_valid:
                for error in result.errors:
                    print(f"Error: {error}")
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Validate root structure
            self._validate_root_structure(openapi_data, errors, warnings)
            
            # Validate OpenAPI version
            self._validate_version(openapi_data, errors, warnings)
            
            # Validate info section
            self._validate_info_section(openapi_data, errors, warnings)
            
            # Validate paths
            self._validate_paths(openapi_data, errors, warnings, suggestions)
            
            # Validate components (if present)
            if 'components' in openapi_data:
                self._validate_components(openapi_data['components'], errors, warnings, suggestions)
            
            # Validate servers (if present)
            if 'servers' in openapi_data:
                self._validate_servers(openapi_data['servers'], errors, warnings)
            
            # Check for MCP-specific recommendations
            self._check_mcp_recommendations(openapi_data, warnings, suggestions)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
    
    def _validate_root_structure(self, spec: Dict[str, Any], errors: List[str], warnings: List[str]):
        """Validate required root-level fields"""
        for field in self.required_root_fields:
            if field not in spec:
                errors.append(f"Missing required root field: {field}")
    
    def _validate_version(self, spec: Dict[str, Any], errors: List[str], warnings: List[str]):
        """Validate OpenAPI version"""
        version = spec.get('openapi')
        if version not in self.supported_versions:
            if version:
                warnings.append(f"OpenAPI version {version} may not be fully supported")
            else:
                errors.append("OpenAPI version is required")
    
    def _validate_info_section(self, spec: Dict[str, Any], errors: List[str], warnings: List[str]):
        """Validate info section"""
        info = spec.get('info', {})
        
        for field in self.required_info_fields:
            if field not in info:
                errors.append(f"Missing required info field: {field}")
        
        # Check for description
        if 'description' not in info:
            warnings.append("Info section missing description - recommended for MCP servers")
    
    def _validate_paths(self, spec: Dict[str, Any], errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate paths and operations"""
        paths = spec.get('paths', {})
        
        if not paths:
            errors.append("No paths defined in specification")
            return
        
        operation_ids = set()
        
        for path, path_item in paths.items():
            if not path.startswith('/'):
                warnings.append(f"Path should start with '/': {path}")
            
            for method, operation in path_item.items():
                if method.lower() not in self.http_methods:
                    continue
                
                # Check operation ID
                op_id = operation.get('operationId')
                if not op_id:
                    warnings.append(f"Missing operationId for {method.upper()} {path}")
                elif op_id in operation_ids:
                    errors.append(f"Duplicate operationId: {op_id}")
                else:
                    operation_ids.add(op_id)
                
                # Check for summary/description
                if not operation.get('summary') and not operation.get('description'):
                    warnings.append(f"No summary or description for {method.upper()} {path}")
                
                # Validate parameters
                self._validate_parameters(operation.get('parameters', []), path, method, warnings)
                
                # Validate responses
                self._validate_responses(operation.get('responses', {}), path, method, errors, warnings)
    
    def _validate_parameters(self, parameters: List[Dict], path: str, method: str, warnings: List[str]):
        """Validate operation parameters"""
        param_names = set()
        
        for param in parameters:
            name = param.get('name')
            if not name:
                warnings.append(f"Parameter missing name in {method.upper()} {path}")
                continue
            
            if name in param_names:
                warnings.append(f"Duplicate parameter '{name}' in {method.upper()} {path}")
            param_names.add(name)
            
            if 'schema' not in param and 'content' not in param:
                warnings.append(f"Parameter '{name}' missing schema in {method.upper()} {path}")
    
    def _validate_responses(self, responses: Dict[str, Any], path: str, method: str, errors: List[str], warnings: List[str]):
        """Validate operation responses"""
        if not responses:
            warnings.append(f"No responses defined for {method.upper()} {path}")
            return
        
        # Check for success response
        success_codes = [code for code in responses.keys() if code.startswith('2')]
        if not success_codes:
            warnings.append(f"No success response (2xx) defined for {method.upper()} {path}")
    
    def _validate_components(self, components: Dict[str, Any], errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate components section"""
        schemas = components.get('schemas', {})
        
        # Check schema definitions
        for schema_name, schema_def in schemas.items():
            if 'type' not in schema_def and '$ref' not in schema_def:
                warnings.append(f"Schema '{schema_name}' missing type definition")
            
            # Check for circular references (basic check)
            if self._has_circular_reference(schema_def, schemas, {schema_name}):
                warnings.append(f"Potential circular reference in schema '{schema_name}'")
    
    def _validate_servers(self, servers: List[Dict], errors: List[str], warnings: List[str]):
        """Validate server definitions"""
        if not servers:
            warnings.append("No servers defined - using default server")
            return
        
        for i, server in enumerate(servers):
            if 'url' not in server:
                errors.append(f"Server {i} missing URL")
            else:
                url = server['url']
                if not (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
                    warnings.append(f"Server URL may be invalid: {url}")
    
    def _check_mcp_recommendations(self, spec: Dict[str, Any], warnings: List[str], suggestions: List[str]):
        """Check for MCP-specific recommendations"""
        paths = spec.get('paths', {})
        
        # Count total operations
        total_ops = sum(
            len([m for m in methods.keys() if m.lower() in self.http_methods])
            for methods in paths.values()
        )
        
        if total_ops > 100:
            suggestions.append("Consider splitting large APIs into multiple MCP servers")
        
        # Check for authentication
        components = spec.get('components', {})
        security_schemes = components.get('securitySchemes', {})
        
        if not security_schemes:
            suggestions.append("Consider adding authentication schemes for production APIs")
        
        # Check for rate limiting info
        has_rate_limit_headers = any(
            'x-ratelimit' in str(response).lower()
            for path_item in paths.values()
            for operation in path_item.values()
            if isinstance(operation, dict)
            for response in operation.get('responses', {}).values()
        )
        
        if not has_rate_limit_headers:
            suggestions.append("Consider documenting rate limiting in API responses")
    
    def _has_circular_reference(self, schema: Dict[str, Any], all_schemas: Dict[str, Any], visited: Set[str]) -> bool:
        """Basic circular reference detection"""
        if 'properties' not in schema:
            return False
        
        for prop_def in schema['properties'].values():
            ref = prop_def.get('$ref')
            if ref and ref.startswith('#/components/schemas/'):
                schema_name = ref.split('/')[-1]
                if schema_name in visited:
                    return True
                
                if schema_name in all_schemas:
                    new_visited = visited.copy()
                    new_visited.add(schema_name)
                    if self._has_circular_reference(all_schemas[schema_name], all_schemas, new_visited):
                        return True
        
        return False

class ProjectValidator:
    """Validator for MCP server project structure and quality"""
    
    def __init__(self):
        """Initialize project validator with required files and patterns"""
        self.required_files = [
            'pyproject.toml',
            'requirements.txt',
            'README.md',
            'src/',
            'tests/',
            'config/'
        ]
        
        self.required_python_files = [
            'server.py',
            'config.py',
            'models.py',
            'client.py',
            'tools.py'
        ]
    
    def validate_project(self, project_path: Path) -> ValidationResult:
        """
        Validate MCP server project structure and quality
        
        Args:
            project_path: Path to project directory
            
        Returns:
            ValidationResult: Comprehensive validation result
            
        Example:
            validator = ProjectValidator()
            result = validator.validate_project(Path("./my-mcp-server"))
            if result.is_valid:
                print("Project structure is valid")
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            if not project_path.exists():
                errors.append(f"Project directory does not exist: {project_path}")
                return ValidationResult(False, errors, warnings, suggestions)
            
            # Validate basic project structure
            self._validate_project_structure(project_path, errors, warnings)
            
            # Validate configuration files
            self._validate_config_files(project_path, errors, warnings, suggestions)
            
            # Validate Python source code
            self._validate_python_source(project_path, errors, warnings, suggestions)
            
            # Validate test structure
            self._validate_test_structure(project_path, errors, warnings, suggestions)
            
            # Validate documentation
            self._validate_documentation(project_path, warnings, suggestions)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            errors.append(f"Project validation error: {str(e)}")
            return ValidationResult(False, errors, warnings, suggestions)
    
    def _validate_project_structure(self, project_path: Path, errors: List[str], warnings: List[str]):
        """Validate basic project directory structure"""
        for required_file in self.required_files:
            file_path = project_path / required_file
            if not file_path.exists():
                errors.append(f"Missing required file/directory: {required_file}")
    
    def _validate_config_files(self, project_path: Path, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate configuration files"""
        # Check pyproject.toml
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            try:
                import tomli
                with open(pyproject_path, 'rb') as f:
                    pyproject_data = tomli.load(f)
                
                # Check required sections
                if 'project' not in pyproject_data:
                    errors.append("pyproject.toml missing [project] section")
                else:
                    project_data = pyproject_data['project']
                    required_fields = ['name', 'version', 'description']
                    for field in required_fields:
                        if field not in project_data:
                            warnings.append(f"pyproject.toml missing project.{field}")
                            
            except ImportError:
                warnings.append("Cannot validate pyproject.toml - tomli not installed")
            except Exception as e:
                errors.append(f"Invalid pyproject.toml: {str(e)}")
        
        # Check requirements files
        req_path = project_path / "requirements.txt"
        if req_path.exists():
            self._validate_requirements_file(req_path, warnings, suggestions)
    
    def _validate_requirements_file(self, req_path: Path, warnings: List[str], suggestions: List[str]):
        """Validate requirements.txt file"""
        try:
            with open(req_path, 'r') as f:
                requirements = f.read().strip().split('\n')
            
            required_packages = ['mcp', 'pydantic', 'httpx']
            found_packages = set()
            
            for req in requirements:
                if req.strip() and not req.strip().startswith('#'):
                    package_name = req.split('==')[0].split('>=')[0].split('<=')[0].strip()
                    found_packages.add(package_name.lower())
            
            for package in required_packages:
                if package not in found_packages:
                    warnings.append(f"Missing recommended package in requirements.txt: {package}")
                    
        except Exception as e:
            warnings.append(f"Cannot validate requirements.txt: {str(e)}")
    
    def _validate_python_source(self, project_path: Path, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate Python source code structure and quality"""
        src_dirs = list(project_path.glob("src/mcp_*"))
        
        if not src_dirs:
            errors.append("No MCP service directory found in src/")
            return
        
        for src_dir in src_dirs:
            if not src_dir.is_dir():
                continue
            
            # Check required Python files
            for required_file in self.required_python_files:
                file_path = src_dir / required_file
                if not file_path.exists():
                    warnings.append(f"Missing recommended file: {src_dir.name}/{required_file}")
                else:
                    # Validate Python syntax
                    self._validate_python_syntax(file_path, errors, warnings)
    
    def _validate_python_syntax(self, file_path: Path, errors: List[str], warnings: List[str]):
        """Validate Python file syntax and basic structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse AST to check syntax
            tree = ast.parse(content, filename=str(file_path))
            
            # Check for docstrings
            if not ast.get_docstring(tree):
                warnings.append(f"Missing module docstring: {file_path.name}")
            
            # Check for basic imports
            imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
            if not imports and file_path.name != '__init__.py':
                warnings.append(f"No imports found in {file_path.name} - may be incomplete")
                
        except SyntaxError as e:
            errors.append(f"Syntax error in {file_path.name}: {str(e)}")
        except Exception as e:
            warnings.append(f"Cannot validate {file_path.name}: {str(e)}")
    
    def _validate_test_structure(self, project_path: Path, errors: List[str], warnings: List[str], suggestions: List[str]):
        """Validate test directory structure and coverage"""
        tests_dir = project_path / "tests"
        
        if not tests_dir.exists():
            errors.append("Tests directory missing")
            return
        
        # Check for test subdirectories
        unit_dir = tests_dir / "unit"
        integration_dir = tests_dir / "integration"
        
        if not unit_dir.exists():
            warnings.append("Unit tests directory missing")
        
        if not integration_dir.exists():
            warnings.append("Integration tests directory missing")
        
        # Check for conftest.py
        conftest_path = tests_dir / "conftest.py"
        if not conftest_path.exists():
            suggestions.append("Consider adding conftest.py for shared test fixtures")
        
        # Count test files
        test_files = list(tests_dir.glob("**/test_*.py"))
        if len(test_files) < 3:
            suggestions.append("Consider adding more comprehensive test coverage")
    
    def _validate_documentation(self, project_path: Path, warnings: List[str], suggestions: List[str]):
        """Validate documentation completeness"""
        readme_path = project_path / "README.md"
        
        if readme_path.exists():
            try:
                with open(readme_path, 'r', encoding='utf-8') as f:
                    readme_content = f.read().lower()
                
                required_sections = ['installation', 'usage', 'configuration']
                for section in required_sections:
                    if section not in readme_content:
                        suggestions.append(f"Consider adding {section} section to README.md")
                        
            except Exception as e:
                warnings.append(f"Cannot validate README.md: {str(e)}")
        
        docs_dir = project_path / "docs"
        if not docs_dir.exists():
            suggestions.append("Consider adding docs/ directory for detailed documentation") 

class EnhancedOpenAPIValidator(OpenAPIValidator):
    """Enhanced validator that can leverage openapi-generator validation"""
    
    def validate_with_generator(self, spec_path: str) -> ValidationResult:
        """Use openapi-generator to validate spec"""
        try:
            result = subprocess.run([
                "openapi-generator", "validate", "-i", spec_path
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                return ValidationResult(True, [], [], [])
            else:
                errors = result.stderr.split('\n')
                return ValidationResult(False, errors, [], [])
        except FileNotFoundError:
            return ValidationResult(False, ["openapi-generator not found"], [], [])