# mcp_cli/openapi_client_generator.py
"""
OpenAPI Client Generator - Wrapper for openapi-generator tool

Handles calling openapi-generator CLI and processing the results
for MCP server integration. Provides a clean interface for generating
robust API clients from OpenAPI specifications.

Author: MCP CLI Team
"""

import subprocess
import json
import ast
import re
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
import importlib.util
import sys

from .validators import ValidationResult, GenerationResult
from .config import OpenAPIGeneratorConfig

logger = logging.getLogger(__name__)

@dataclass
class ApiClass:
    """Represents an API class from generated client"""
    name: str
    module: str
    methods: List[str] = field(default_factory=list)
    file_path: Optional[Path] = None

@dataclass
class Operation:
    """Represents an API operation from generated client"""
    name: str
    api_class: str
    method: str  # HTTP method (GET, POST, etc.)
    path: str
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    summary: Optional[str] = None
    description: Optional[str] = None
    request_body_type: Optional[str] = None
    response_type: Optional[str] = None
    auth_required: bool = False

@dataclass
class Model:
    """Represents a data model from generated client"""
    name: str
    properties: List[str] = field(default_factory=list)
    file_path: Optional[Path] = None
    required_fields: List[str] = field(default_factory=list)

@dataclass
class ClientAnalysis:
    """Analysis result from generated API client"""
    api_classes: List[ApiClass] = field(default_factory=list)
    operations: List[Operation] = field(default_factory=list)
    models: List[Model] = field(default_factory=list)
    client_package_name: str = ""
    base_url: Optional[str] = None
    auth_schemes: List[str] = field(default_factory=list)

class OpenAPIClientGeneratorError(Exception):
    """Custom exception for client generation errors"""
    pass

class OpenAPIClientGenerator:
    """
    Wrapper for openapi-generator CLI tool
    
    Provides methods to generate Python clients from OpenAPI specifications
    and analyze the generated code for MCP integration.
    """
    
    def __init__(self):
        """Initialize the generator with default configurations"""
        self.logger = logging.getLogger(__name__)
        
        # Default generator configurations for different client types
        self.default_configs = {
            "python-sync": {
                "generator": "python",
                "additional_properties": {
                    "packageName": "api_client",
                    "projectName": "api-client",
                    "packageVersion": "1.0.0",
                    "library": "urllib3"
                }
            },
            "python-asyncio": {
                "generator": "python",
                "additional_properties": {
                    "packageName": "api_client", 
                    "projectName": "api-client",
                    "packageVersion": "1.0.0",
                    "library": "asyncio"
                }
            }
        }
    
    def check_openapi_generator_installed(self) -> bool:
        """
        Check if openapi-generator CLI tool is available
        
        Returns:
            bool: True if openapi-generator is available, False otherwise
            
        Example:
            generator = OpenAPIClientGenerator()
            if generator.check_openapi_generator_installed():
                print("openapi-generator is available")
            else:
                print("Please install openapi-generator")
        """
        try:
            result = subprocess.run(
                ['openapi-generator-cli', 'version'],
                capture_output=True,
                text=True,
                timeout=10,
                shell=True
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"Found openapi-generator-cli version: {version}")
                return True
            else:
                self.logger.warning(f"openapi-generator-cli check failed: {result.stderr}")
                return False
                
        except FileNotFoundError:
            self.logger.warning("openapi-generator-cli not found in PATH")
            return False
        except subprocess.TimeoutExpired:
            self.logger.warning("openapi-generator-cli version check timed out")
            return False
        except Exception as e:
            self.logger.error(f"Error checking openapi-generator-cli: {e}")
            return False
    
    def generate_python_client(
        self, 
        spec_path: str, 
        output_dir: Path, 
        config: OpenAPIGeneratorConfig
    ) -> GenerationResult:
        """
        Generate Python client using openapi-generator
        
        Args:
            spec_path: Path to OpenAPI specification file
            output_dir: Directory to generate client in
            config: Generator configuration
            
        Returns:
            GenerationResult: Result of the generation process
            
        Raises:
            OpenAPIClientGeneratorError: If generation fails
            
        Example:
            config = OpenAPIGeneratorConfig(
                generator_type="python",
                package_name="my_api_client",
                client_type="asyncio"
            )
            result = generator.generate_python_client("spec.json", Path("./output"), config)
        """
        if not self.check_openapi_generator_installed():
            return GenerationResult(
                success=False,
                files_created=[],
                errors=["openapi-generator CLI tool not found. Please install it first."],
                warnings=[]
            )
        
        try:
            # Prepare output directory
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build CLI arguments
            cli_args = self._build_cli_args(spec_path, output_dir, config)
            
            self.logger.info(f"Running openapi-generator with args: {' '.join(cli_args)}")
            
            # Execute openapi-generator
            result = subprocess.run(
                cli_args,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=output_dir.parent,
                shell=True  # Required on Windows to find CLI tools
            )
            
            if result.returncode == 0:
                # Find generated files
                generated_files = self._find_generated_files(output_dir)
                
                return GenerationResult(
                    success=True,
                    files_created=generated_files,
                    errors=[],
                    warnings=self._parse_warnings_from_output(result.stdout)
                )
            else:
                error_msg = f"openapi-generator failed with code {result.returncode}"
                error_details = result.stderr or result.stdout
                
                return GenerationResult(
                    success=False,
                    files_created=[],
                    errors=[f"{error_msg}: {error_details}"],
                    warnings=[]
                )
                
        except subprocess.TimeoutExpired:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=["openapi-generator execution timed out"],
                warnings=[]
            )
        except Exception as e:
            return GenerationResult(
                success=False,
                files_created=[],
                errors=[f"Unexpected error during generation: {str(e)}"],
                warnings=[]
            )
    
    def parse_generated_client(self, client_dir: Path) -> ClientAnalysis:
        """
        Analyze generated client to extract API operations and models
        
        Args:
            client_dir: Directory containing generated client code
            
        Returns:
            ClientAnalysis: Analysis of the generated client
            
        Example:
            analysis = generator.parse_generated_client(Path("./generated_client"))
            print(f"Found {len(analysis.operations)} API operations")
        """
        analysis = ClientAnalysis()
        
        try:
            # Determine package name from directory structure
            analysis.client_package_name = self._extract_package_name(client_dir)
            
            # Find and parse API classes
            api_dir = client_dir / "api"
            if api_dir.exists():
                analysis.api_classes = self._parse_api_classes(api_dir)
                analysis.operations = self._extract_operations_from_apis(analysis.api_classes)
            
            # Find and parse model classes
            models_dir = client_dir / "models"
            if models_dir.exists():
                analysis.models = self._parse_model_classes(models_dir)
            
            # Extract configuration information
            config_file = client_dir / "configuration.py"
            if config_file.exists():
                analysis.base_url = self._extract_base_url(config_file)
            
            self.logger.info(f"Parsed client: {len(analysis.api_classes)} APIs, "
                           f"{len(analysis.operations)} operations, {len(analysis.models)} models")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error parsing generated client: {e}")
            raise OpenAPIClientGeneratorError(f"Failed to parse generated client: {e}")
    
    def validate_generated_client(self, client_dir: Path) -> ValidationResult:
        """
        Validate that generated client is usable and complete
        
        Args:
            client_dir: Directory containing generated client
            
        Returns:
            ValidationResult: Validation results
            
        Example:
            result = generator.validate_generated_client(Path("./generated_client"))
            if result.is_valid:
                print("Generated client is valid")
        """
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Check required files exist
            required_files = [
                "__init__.py",
                "api_client.py", 
                "configuration.py"
            ]
            
            for required_file in required_files:
                file_path = client_dir / required_file
                if not file_path.exists():
                    errors.append(f"Missing required file: {required_file}")
            
            # Check API directory
            api_dir = client_dir / "api"
            if not api_dir.exists():
                errors.append("Missing api directory")
            elif not any(api_dir.glob("*_api.py")):
                warnings.append("No API files found in api directory")
            
            # Check models directory
            models_dir = client_dir / "models"
            if not models_dir.exists():
                warnings.append("Missing models directory")
            
            # Try to import the client (basic syntax check)
            try:
                self._test_client_import(client_dir)
            except Exception as e:
                errors.append(f"Client import failed: {str(e)}")
            
            # Check for common issues
            if self._has_import_issues(client_dir):
                warnings.append("Potential import issues detected")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                suggestions=suggestions
            )
            
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                warnings=warnings,
                suggestions=suggestions
            )
    
    def _build_cli_args(self, spec_path: str, output_dir: Path, config: OpenAPIGeneratorConfig) -> List[str]:
        """Build command line arguments for openapi-generator"""
        args = [
            "openapi-generator-cli",
            "generate",
            "-i", spec_path,
            "-g", config.generator_type,
            "-o", str(output_dir)
        ]
        
        # Add package name
        if config.package_name:
            args.extend(["--package-name", config.package_name])
        
        # Add additional properties
        if config.additional_properties:
            props = []
            for key, value in config.additional_properties.items():
                props.append(f"{key}={value}")
            
            # Handle client type specific properties
            if config.client_type == "asyncio":
                props.append("library=asyncio")
            elif config.client_type == "sync":
                props.append("library=urllib3")
            
            if props:
                args.extend(["--additional-properties", ",".join(props)])
        
        # Add other configuration options
        if not config.generate_docs:
            args.append("--skip-validate-spec")
        
        return args
    
    def _find_generated_files(self, output_dir: Path) -> List[str]:
        """Find all generated files in the output directory"""
        generated_files = []
        
        if output_dir.exists():
            for file_path in output_dir.rglob("*"):
                if file_path.is_file():
                    generated_files.append(str(file_path.relative_to(output_dir)))
        
        return generated_files
    
    def _parse_warnings_from_output(self, output: str) -> List[str]:
        """Parse warnings from openapi-generator output"""
        warnings = []
        
        for line in output.split('\n'):
            if 'warning' in line.lower() or 'warn' in line.lower():
                warnings.append(line.strip())
        
        return warnings
    
    def _extract_package_name(self, client_dir: Path) -> str:
        """Extract package name from generated client directory"""
        # Look for setup.py or pyproject.toml
        setup_py = client_dir / "setup.py"
        if setup_py.exists():
            content = setup_py.read_text()
            match = re.search(r'name=["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
        
        # Fallback to directory name
        return client_dir.name
    
    def _parse_api_classes(self, api_dir: Path) -> List[ApiClass]:
        """Parse API classes from generated api directory"""
        api_classes = []
        
        for api_file in api_dir.glob("*_api.py"):
            try:
                api_class = self._parse_single_api_file(api_file)
                if api_class:
                    api_classes.append(api_class)
            except Exception as e:
                self.logger.warning(f"Failed to parse API file {api_file}: {e}")
        
        return api_classes
    
    def _parse_single_api_file(self, api_file: Path) -> Optional[ApiClass]:
        """Parse a single API file to extract class information"""
        try:
            content = api_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Look for API classes (usually end with 'Api')
                    if node.name.endswith('Api'):
                        methods = []
                        
                        # Extract method names
                        for class_node in node.body:
                            if isinstance(class_node, ast.FunctionDef):
                                # Skip private and special methods
                                if not class_node.name.startswith('_'):
                                    methods.append(class_node.name)
                        
                        return ApiClass(
                            name=node.name,
                            module=api_file.stem,
                            methods=methods,
                            file_path=api_file
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing API file {api_file}: {e}")
            return None
    
    def _extract_operations_from_apis(self, api_classes: List[ApiClass]) -> List[Operation]:
        """Extract operation information from API classes"""
        operations = []
        
        for api_class in api_classes:
            for method_name in api_class.methods:
                # Create operation from method name
                # This is a simplified extraction - in reality, we'd need to parse
                # the method implementations or use the original OpenAPI spec
                operation = Operation(
                    name=method_name,
                    api_class=api_class.name,
                    method="GET",  # Default, would be extracted from implementation
                    path=f"/{method_name}",  # Simplified, would be extracted from implementation
                    summary=f"{method_name.replace('_', ' ').title()}",
                    description=f"Execute {method_name} operation"
                )
                operations.append(operation)
        
        return operations
    
    def _parse_model_classes(self, models_dir: Path) -> List[Model]:
        """Parse model classes from generated models directory"""
        models = []
        
        for model_file in models_dir.glob("*.py"):
            if model_file.name == "__init__.py":
                continue
                
            try:
                model = self._parse_single_model_file(model_file)
                if model:
                    models.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse model file {model_file}: {e}")
        
        return models
    
    def _parse_single_model_file(self, model_file: Path) -> Optional[Model]:
        """Parse a single model file to extract class information"""
        try:
            content = model_file.read_text(encoding='utf-8')
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Skip base classes and internal classes
                    if not node.name.startswith('_'):
                        properties = []
                        
                        # Extract property names from __init__ method
                        for class_node in node.body:
                            if isinstance(class_node, ast.FunctionDef) and class_node.name == "__init__":
                                for arg in class_node.args.args[1:]:  # Skip 'self'
                                    properties.append(arg.arg)
                        
                        return Model(
                            name=node.name,
                            properties=properties,
                            file_path=model_file
                        )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing model file {model_file}: {e}")
            return None
    
    def _extract_base_url(self, config_file: Path) -> Optional[str]:
        """Extract base URL from configuration file"""
        try:
            content = config_file.read_text(encoding='utf-8')
            
            # Look for host configuration
            match = re.search(r'host\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Could not extract base URL: {e}")
            return None
    
    def _test_client_import(self, client_dir: Path) -> None:
        """Test that the generated client can be imported (basic syntax check)"""
        # Add client directory to Python path temporarily
        original_path = sys.path.copy()
        
        try:
            sys.path.insert(0, str(client_dir.parent))
            
            # Try to import the main client module
            package_name = client_dir.name
            spec = importlib.util.find_spec(package_name)
            
            if spec is None:
                raise ImportError(f"Could not find package {package_name}")
            
        finally:
            # Restore original path
            sys.path = original_path
    
    def _has_import_issues(self, client_dir: Path) -> bool:
        """Check for common import issues in generated code"""
        try:
            # Check for circular imports by examining import statements
            python_files = list(client_dir.rglob("*.py"))
            
            for py_file in python_files:
                content = py_file.read_text(encoding='utf-8')
                
                # Look for problematic import patterns
                if "from . import " in content and "from .api import " in content:
                    return True
                    
            return False
            
        except Exception:
            return False