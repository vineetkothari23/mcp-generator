"""
Utilities for OpenAPI integration and client analysis
"""

def extract_operations_from_client(client_dir: Path) -> List[OperationInfo]:
    """Extract operation information from generated client"""
    
def generate_tool_name(operation: dict, naming_convention: str) -> str:
    """Generate MCP tool name from OpenAPI operation"""
    
def convert_openapi_schema_to_mcp_schema(openapi_schema: dict) -> dict:
    """Convert OpenAPI parameter schema to MCP tool input schema"""
    
def analyze_authentication_schemes(openapi_spec: dict) -> List[AuthScheme]:
    """Analyze authentication requirements from OpenAPI spec"""