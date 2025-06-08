"""
Configuration management for openapi-generator integration
"""
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class OpenAPIGeneratorConfig:
    """Configuration for openapi-generator tool"""
    generator_type: str = "python"
    package_name: str = "api_client"
    client_type: str = "asyncio"  # or "sync"
    generate_models: bool = True
    generate_apis: bool = True
    generate_docs: bool = True
    additional_properties: Dict[str, str] = None
    
    def to_cli_args(self) -> List[str]:
        """Convert config to openapi-generator CLI arguments"""
        
class MCPIntegrationConfig:
    """Configuration for MCP-specific generation"""
    max_tools: int = 50
    include_auth_tools: bool = True
    generate_pagination_helpers: bool = True
    include_file_upload_tools: bool = True
    tool_naming_convention: str = "operation_id"  # or "path_method"