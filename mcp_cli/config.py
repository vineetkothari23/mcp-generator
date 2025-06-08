# mcp_cli/config.py
"""
Configuration management for openapi-generator integration

Provides configuration classes for controlling openapi-generator behavior
and MCP-specific generation options.

Author: MCP CLI Team
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

@dataclass
class OpenAPIGeneratorConfig:
    """
    Configuration for openapi-generator tool
    
    Controls how the openapi-generator CLI tool generates Python clients
    from OpenAPI specifications.
    """
    
    # Core generator settings
    generator_type: str = "python"
    package_name: str = "api_client" 
    client_type: str = "sync"  # "sync", "asyncio"
    
    # Generation options
    generate_models: bool = True
    generate_apis: bool = True
    generate_docs: bool = True
    generate_tests: bool = False
    
    # Additional properties passed to openapi-generator
    additional_properties: Dict[str, str] = field(default_factory=dict)
    
    # Output customization
    template_dir: Optional[Path] = None
    ignore_file_override: Optional[Path] = None
    
    def __post_init__(self):
        """Set up default additional properties based on client type"""
        if not self.additional_properties:
            self.additional_properties = {}
        
        # Set default properties
        defaults = {
            "packageVersion": "1.0.0",
            "projectName": self.package_name.replace("_", "-"),
            "packageUrl": "https://github.com/example/api-client"
        }
        
        # Add client-type specific properties
        if self.client_type == "asyncio":
            defaults.update({
                "library": "asyncio",
                "asyncio": "true"
            })
        elif self.client_type == "sync":
            defaults.update({
                "library": "urllib3"
            })
        
        # Merge with user-provided properties (user properties take precedence)
        for key, value in defaults.items():
            if key not in self.additional_properties:
                self.additional_properties[key] = value
    
    def to_cli_args(self) -> List[str]:
        """
        Convert configuration to openapi-generator CLI arguments
        
        Returns:
            List[str]: CLI arguments for openapi-generator
            
        Example:
            config = OpenAPIGeneratorConfig(client_type="asyncio")
            args = config.to_cli_args()
            # Returns: ["--package-name", "api_client", "--additional-properties", "library=asyncio,asyncio=true"]
        """
        args = []
        
        # Package name
        if self.package_name:
            args.extend(["--package-name", self.package_name])
        
        # Skip options
        if not self.generate_docs:
            args.append("--skip-validate-spec")
        
        # Template directory
        if self.template_dir:
            args.extend(["-t", str(self.template_dir)])
        
        # Ignore file
        if self.ignore_file_override:
            args.extend(["--ignore-file-override", str(self.ignore_file_override)])
        
        # Additional properties
        if self.additional_properties:
            props = [f"{key}={value}" for key, value in self.additional_properties.items()]
            args.extend(["--additional-properties", ",".join(props)])
        
        return args
    
    @classmethod
    def for_sync_client(cls, package_name: str = "api_client", **kwargs) -> "OpenAPIGeneratorConfig":
        """
        Create configuration for synchronous client generation
        
        Args:
            package_name: Name of the generated package
            **kwargs: Additional configuration options
            
        Returns:
            OpenAPIGeneratorConfig: Configuration for sync client
        """
        return cls(
            client_type="sync",
            package_name=package_name,
            **kwargs
        )
    
    @classmethod
    def for_async_client(cls, package_name: str = "api_client", **kwargs) -> "OpenAPIGeneratorConfig":
        """
        Create configuration for asynchronous client generation
        
        Args:
            package_name: Name of the generated package
            **kwargs: Additional configuration options
            
        Returns:
            OpenAPIGeneratorConfig: Configuration for async client
        """
        return cls(
            client_type="asyncio",
            package_name=package_name,
            **kwargs
        )

@dataclass
class MCPIntegrationConfig:
    """
    Configuration for MCP-specific generation options
    
    Controls how OpenAPI operations are mapped to MCP tools and
    what additional features are included in the generated server.
    """
    
    # Tool generation limits
    max_tools: int = 50
    max_parameters_per_tool: int = 20
    
    # Tool naming and organization
    tool_naming_convention: str = "operation_id"  # "operation_id", "path_method", "custom"
    tool_prefix: str = ""
    tool_suffix: str = ""
    group_tools_by_tag: bool = True
    
    # Authentication and security
    include_auth_tools: bool = True
    generate_auth_helpers: bool = True
    supported_auth_types: List[str] = field(default_factory=lambda: ["apiKey", "http", "oauth2"])
    
    # Advanced features
    generate_pagination_helpers: bool = True
    include_file_upload_tools: bool = True
    generate_webhook_tools: bool = False
    include_batch_operations: bool = False
    
    # Error handling
    generate_error_handlers: bool = True
    include_retry_logic: bool = True
    default_timeout: int = 30
    
    # Documentation and examples
    generate_tool_examples: bool = True
    include_usage_docs: bool = True
    generate_postman_collection: bool = False
    
    def get_tool_name(self, operation_id: str, method: str, path: str) -> str:
        """
        Generate tool name based on naming convention
        
        Args:
            operation_id: OpenAPI operationId
            method: HTTP method
            path: API path
            
        Returns:
            str: Generated tool name
            
        Example:
            config = MCPIntegrationConfig(tool_naming_convention="operation_id")
            name = config.get_tool_name("listPets", "GET", "/pets")
            # Returns: "listPets" or "list_pets" depending on configuration
        """
        if self.tool_naming_convention == "operation_id" and operation_id:
            base_name = operation_id
        elif self.tool_naming_convention == "path_method":
            # Convert path to snake_case and combine with method
            path_parts = [part for part in path.split("/") if part and not part.startswith("{")]
            if path_parts:
                base_name = f"{method.lower()}_{('_'.join(path_parts)).lower()}"
            else:
                base_name = method.lower()
        else:
            # Fallback to operation_id or path_method
            base_name = operation_id or f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}"
        
        # Apply prefix and suffix
        name = f"{self.tool_prefix}{base_name}{self.tool_suffix}"
        
        # Ensure valid Python identifier
        name = self._sanitize_tool_name(name)
        
        return name
    
    def _sanitize_tool_name(self, name: str) -> str:
        """Sanitize tool name to be a valid Python identifier"""
        import re
        
        # Convert to snake_case
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        name = name.lower()
        
        # Replace invalid characters with underscore
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = f"tool_{name}"
        
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        return name or "unnamed_tool"
    
    def should_include_operation(self, operation: Dict[str, Any]) -> bool:
        """
        Determine if an operation should be included as an MCP tool
        
        Args:
            operation: OpenAPI operation definition
            
        Returns:
            bool: True if operation should be included
        """
        # Check if operation is deprecated
        if operation.get("deprecated", False):
            return False
        
        # Check method is supported
        method = operation.get("method", "").upper()
        if method not in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
            return False
        
        # Check parameter count
        parameters = operation.get("parameters", [])
        if len(parameters) > self.max_parameters_per_tool:
            return False
        
        # Check for file uploads if not supported
        if not self.include_file_upload_tools:
            request_body = operation.get("requestBody", {})
            content = request_body.get("content", {})
            if "multipart/form-data" in content:
                return False
        
        return True
    
    @classmethod
    def minimal(cls) -> "MCPIntegrationConfig":
        """Create minimal configuration with basic features only"""
        return cls(
            max_tools=10,
            include_auth_tools=False,
            generate_pagination_helpers=False,
            include_file_upload_tools=False,
            generate_tool_examples=False
        )
    
    @classmethod
    def comprehensive(cls) -> "MCPIntegrationConfig":
        """Create comprehensive configuration with all features enabled"""
        return cls(
            max_tools=100,
            include_auth_tools=True,
            generate_pagination_helpers=True,
            include_file_upload_tools=True,
            generate_webhook_tools=True,
            include_batch_operations=True,
            generate_tool_examples=True,
            include_usage_docs=True,
            generate_postman_collection=True
        )

@dataclass
class MCPProjectConfig:
    """
    Overall configuration for MCP project generation
    
    Combines OpenAPI generator settings with MCP integration options
    and project-level configuration.
    """
    
    # Project metadata
    project_name: str
    service_name: str
    description: str
    author: str
    version: str = "1.0.0"
    python_version: str = "3.11"
    
    # Generation settings
    openapi_config: OpenAPIGeneratorConfig = field(default_factory=OpenAPIGeneratorConfig)
    mcp_config: MCPIntegrationConfig = field(default_factory=MCPIntegrationConfig)
    
    # Output configuration
    output_dir: str = "."
    include_docker: bool = True
    include_ci: bool = True
    test_framework: str = "pytest"
    
    # OpenAPI source
    openapi_spec: Optional[str] = None
    openapi_url: Optional[str] = None
    
    def __post_init__(self):
        """Initialize dependent configurations"""
        # Set package name based on service name if not already set
        if self.openapi_config.package_name == "api_client":
            self.openapi_config.package_name = f"{self.service_name}_client"
        
        # Ensure service name is valid Python identifier
        self.service_name = self._sanitize_service_name(self.service_name)
    
    def _sanitize_service_name(self, name: str) -> str:
        """Sanitize service name to be a valid Python identifier"""
        import re
        
        # Convert to snake_case
        name = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', name)
        name = name.lower()
        
        # Replace invalid characters with underscore
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        
        # Ensure it doesn't start with a number
        if name and name[0].isdigit():
            name = f"service_{name}"
        
        # Remove multiple consecutive underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        return name or "api_service"
    
    @classmethod
    def from_openapi_spec(
        cls,
        spec_path: str,
        project_name: Optional[str] = None,
        author: str = "Developer",
        **kwargs
    ) -> "MCPProjectConfig":
        """
        Create project configuration from OpenAPI specification
        
        Args:
            spec_path: Path to OpenAPI specification
            project_name: Project name (auto-generated if not provided)
            author: Project author
            **kwargs: Additional configuration options
            
        Returns:
            MCPProjectConfig: Project configuration
        """
        import json
        import yaml
        from pathlib import Path
        
        # Load and parse OpenAPI spec to extract metadata
        spec_file = Path(spec_path)
        if spec_file.suffix.lower() in ['.yaml', '.yml']:
            with open(spec_file, 'r') as f:
                spec_data = yaml.safe_load(f)
        else:
            with open(spec_file, 'r') as f:
                spec_data = json.load(f)
        
        # Extract project information from spec
        info = spec_data.get('info', {})
        
        if not project_name:
            project_name = info.get('title', spec_file.stem).lower().replace(' ', '-')
        
        service_name = project_name.replace('-', '_')
        description = info.get('description', f"MCP server for {project_name}")
        version = info.get('version', '1.0.0')
        
        return cls(
            project_name=project_name,
            service_name=service_name,
            description=description,
            author=author,
            version=version,
            openapi_spec=spec_path,
            **kwargs
        )
    
    def get_output_path(self) -> Path:
        """Get the full output path for the project"""
        return Path(self.output_dir) / self.project_name
    
    def get_client_package_path(self) -> Path:
        """Get the path where the generated client will be located"""
        return self.get_output_path() / "generated_client"
    
    def get_mcp_package_path(self) -> Path:
        """Get the path where the MCP server code will be located"""
        return self.get_output_path() / "src" / f"mcp_{self.service_name}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "project_name": self.project_name,
            "service_name": self.service_name,
            "description": self.description,
            "author": self.author,
            "version": self.version,
            "python_version": self.python_version,
            "output_dir": self.output_dir,
            "include_docker": self.include_docker,
            "include_ci": self.include_ci,
            "test_framework": self.test_framework,
            "openapi_spec": self.openapi_spec,
            "openapi_url": self.openapi_url,
            "openapi_config": {
                "generator_type": self.openapi_config.generator_type,
                "package_name": self.openapi_config.package_name,
                "client_type": self.openapi_config.client_type,
                "generate_models": self.openapi_config.generate_models,
                "generate_apis": self.openapi_config.generate_apis,
                "generate_docs": self.openapi_config.generate_docs,
                "additional_properties": self.openapi_config.additional_properties
            },
            "mcp_config": {
                "max_tools": self.mcp_config.max_tools,
                "tool_naming_convention": self.mcp_config.tool_naming_convention,
                "include_auth_tools": self.mcp_config.include_auth_tools,
                "generate_pagination_helpers": self.mcp_config.generate_pagination_helpers,
                "include_file_upload_tools": self.mcp_config.include_file_upload_tools,
                "generate_tool_examples": self.mcp_config.generate_tool_examples
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPProjectConfig":
        """Create configuration from dictionary"""
        openapi_config_data = data.get("openapi_config", {})
        mcp_config_data = data.get("mcp_config", {})
        
        return cls(
            project_name=data["project_name"],
            service_name=data["service_name"],
            description=data["description"],
            author=data["author"],
            version=data.get("version", "1.0.0"),
            python_version=data.get("python_version", "3.11"),
            output_dir=data.get("output_dir", "."),
            include_docker=data.get("include_docker", True),
            include_ci=data.get("include_ci", True),
            test_framework=data.get("test_framework", "pytest"),
            openapi_spec=data.get("openapi_spec"),
            openapi_url=data.get("openapi_url"),
            openapi_config=OpenAPIGeneratorConfig(
                generator_type=openapi_config_data.get("generator_type", "python"),
                package_name=openapi_config_data.get("package_name", "api_client"),
                client_type=openapi_config_data.get("client_type", "sync"),
                generate_models=openapi_config_data.get("generate_models", True),
                generate_apis=openapi_config_data.get("generate_apis", True),
                generate_docs=openapi_config_data.get("generate_docs", True),
                additional_properties=openapi_config_data.get("additional_properties", {})
            ),
            mcp_config=MCPIntegrationConfig(
                max_tools=mcp_config_data.get("max_tools", 50),
                tool_naming_convention=mcp_config_data.get("tool_naming_convention", "operation_id"),
                include_auth_tools=mcp_config_data.get("include_auth_tools", True),
                generate_pagination_helpers=mcp_config_data.get("generate_pagination_helpers", True),
                include_file_upload_tools=mcp_config_data.get("include_file_upload_tools", True),
                generate_tool_examples=mcp_config_data.get("generate_tool_examples", True)
            )
        )

# Utility functions for configuration management

def load_config_from_file(file_path: Union[str, Path]) -> MCPProjectConfig:
    """
    Load project configuration from file
    
    Args:
        file_path: Path to configuration file (JSON or YAML)
        
    Returns:
        MCPProjectConfig: Loaded configuration
        
    Example:
        config = load_config_from_file("./mcp-config.yaml")
    """
    import json
    import yaml
    
    file_path = Path(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        else:
            data = json.load(f)
    
    return MCPProjectConfig.from_dict(data)

def save_config_to_file(config: MCPProjectConfig, file_path: Union[str, Path]) -> None:
    """
    Save project configuration to file
    
    Args:
        config: Configuration to save
        file_path: Output file path
        
    Example:
        save_config_to_file(config, "./mcp-config.yaml")
    """
    import json
    import yaml
    
    file_path = Path(file_path)
    data = config.to_dict()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if file_path.suffix.lower() in ['.yaml', '.yml']:
            yaml.dump(data, f, default_flow_style=False, indent=2)
        else:
            json.dump(data, f, indent=2)

def create_default_config(
    project_name: str,
    author: str = "Developer",
    client_type: str = "sync"
) -> MCPProjectConfig:
    """
    Create a default configuration with sensible defaults
    
    Args:
        project_name: Name of the project
        author: Project author
        client_type: Type of client to generate ("sync" or "asyncio")
        
    Returns:
        MCPProjectConfig: Default configuration
        
    Example:
        config = create_default_config("my-api-server", "John Doe", "asyncio")
    """
    openapi_config = (
        OpenAPIGeneratorConfig.for_async_client(f"{project_name}_client")
        if client_type == "asyncio"
        else OpenAPIGeneratorConfig.for_sync_client(f"{project_name}_client")
    )
    
    return MCPProjectConfig(
        project_name=project_name,
        service_name=project_name.replace('-', '_'),
        description=f"MCP server for {project_name}",
        author=author,
        openapi_config=openapi_config,
        mcp_config=MCPIntegrationConfig()
    )