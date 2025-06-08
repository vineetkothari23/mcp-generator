"""
MCP Tool Mapper - Maps OpenAPI operations to MCP tools

Analyzes generated API client and creates MCP tool definitions
that wrap the client methods.
"""
from .openapi_client_generator import ClientAnalysis, Operation
from typing import List, Dict, Any
from dataclasses import dataclass, field
import re

@dataclass
class ToolDefinition:
    """
    Represents an MCP tool definition that wraps an API operation.
    
    Attributes:
        name: The unique identifier for the tool (e.g., "list_pets")
        description: Human-readable description of what the tool does
        input_schema: JSON schema defining the expected input parameters
        operation: The original OpenAPI operation this tool wraps
        
    Example:
        tool = ToolDefinition(
            name="get_pet_by_id",
            description="Retrieve a specific pet by its ID",
            input_schema={
                "type": "object",
                "properties": {
                    "pet_id": {
                        "type": "integer",
                        "description": "The ID of the pet to retrieve"
                    }
                },
                "required": ["pet_id"]
            },
            operation=operation_obj
        )
    """
    name: str
    description: str
    input_schema: Dict[str, Any] = field(default_factory=dict)
    operation: Operation = None

class MCPToolMapper:
    """
    Maps OpenAPI operations to MCP tool definitions.
    
    Takes a ClientAnalysis object containing parsed API operations
    and generates corresponding MCP tool definitions with proper
    JSON schemas for input validation.
    """
    
    def __init__(self, client_analysis: ClientAnalysis):
        """
        Initialize the tool mapper with client analysis data.
        
        Args:
            client_analysis: Analysis of generated API client containing operations
        """
        self.client_analysis = client_analysis
        
    def generate_tool_definitions(self) -> List[ToolDefinition]:
        """
        Create MCP tool definitions from API operations.
        
        Converts each API operation into an MCP tool with:
        - Sanitized tool name derived from operation name
        - Human-readable description from operation summary/description
        - JSON schema for input parameters based on operation parameters
        
        Returns:
            List[ToolDefinition]: List of MCP tool definitions
            
        Example:
            mapper = MCPToolMapper(client_analysis)
            tools = mapper.generate_tool_definitions()
            
            for tool in tools:
                print(f"Tool: {tool.name}")
                print(f"Description: {tool.description}")
                print(f"Schema: {tool.input_schema}")
        """
        tool_definitions = []
        
        for operation in self.client_analysis.operations:
            # Generate tool name from operation name
            tool_name = self._generate_tool_name(operation)
            
            # Generate description from operation summary/description
            description = self._generate_tool_description(operation)
            
            # Generate JSON schema for input parameters
            input_schema = self._generate_input_schema(operation)
            
            # Create tool definition
            tool_def = ToolDefinition(
                name=tool_name,
                description=description,
                input_schema=input_schema,
                operation=operation
            )
            
            tool_definitions.append(tool_def)
        
        return tool_definitions
    
    def _generate_tool_name(self, operation: Operation) -> str:
        """
        Generate a valid MCP tool name from operation name.
        
        Converts operation names to snake_case and ensures they are valid
        Python identifiers. Falls back to HTTP method + path if operation
        name is not available.
        
        Args:
            operation: API operation to generate name for
            
        Returns:
            str: Valid tool name in snake_case
            
        Example:
            _generate_tool_name(operation) -> "get_user_by_id"
        """
        if operation.name:
            # Use operation name if available
            name = operation.name
        else:
            # Fall back to method + path
            path_parts = [part for part in operation.path.split('/') if part and not part.startswith('{')]
            if path_parts:
                name = f"{operation.method.lower()}_{('_'.join(path_parts))}"
            else:
                name = f"{operation.method.lower()}_operation"
        
        # Convert to snake_case
        name = self._to_snake_case(name)
        
        # Ensure it's a valid Python identifier
        if name and name[0].isdigit():
            name = '_' + name  # Can't start with number
        
        return name or "unknown_operation"
    
    def _generate_tool_description(self, operation: Operation) -> str:
        """
        Generate human-readable description for MCP tool.
        
        Uses operation summary if available, falls back to description,
        or generates a description from HTTP method and path.
        
        Args:
            operation: API operation to generate description for
            
        Returns:
            str: Human-readable tool description
        """
        # Use summary if available (preferred)
        if operation.summary and operation.summary.strip():
            return operation.summary.strip()
        
        # Fall back to description
        if operation.description and operation.description.strip():
            # Truncate long descriptions and take first sentence
            desc = operation.description.strip()
            first_sentence = desc.split('.')[0]
            if len(first_sentence) < 200:
                return first_sentence + ('.' if not first_sentence.endswith('.') else '')
            else:
                return desc[:200] + "..." if len(desc) > 200 else desc
        
        # Generate description from method and path
        method_desc = {
            'GET': 'Retrieve',
            'POST': 'Create',
            'PUT': 'Update',
            'DELETE': 'Delete',
            'PATCH': 'Partially update'
        }.get(operation.method.upper(), operation.method.upper())
        
        # Extract resource name from path
        path_parts = [part for part in operation.path.split('/') if part and not part.startswith('{')]
        if path_parts:
            resource = path_parts[-1].replace('_', ' ').replace('-', ' ')
            return f"{method_desc} {resource}"
        else:
            return f"{method_desc} resource using {operation.path}"
    
    def _generate_input_schema(self, operation: Operation) -> Dict[str, Any]:
        """
        Generate JSON schema for tool input parameters.
        
        Creates a JSON schema object that defines the expected input
        structure for the MCP tool, including:
        - Path parameters (required)
        - Query parameters (optional unless marked required)
        - Request body properties (if applicable)
        
        Args:
            operation: API operation to generate schema for
            
        Returns:
            Dict[str, Any]: JSON schema object for tool input
        """
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        # Process operation parameters
        for param in operation.parameters:
            param_name = param.get('name', 'unknown_param')
            param_type = param.get('type', 'string')
            param_desc = param.get('description', f"Parameter {param_name}")
            param_required = param.get('required', False)
            param_location = param.get('in', 'query')  # path, query, header, cookie
            
            # Convert OpenAPI types to JSON Schema types
            json_type = self._convert_openapi_type_to_json_schema(param_type)
            
            # Add parameter to schema
            schema["properties"][param_name] = {
                "type": json_type,
                "description": param_desc
            }
            
            # Path parameters are always required
            if param_location == 'path' or param_required:
                schema["required"].append(param_name)
        
        # Handle request body if present
        if operation.request_body_type:
            # For request body, we'll add a generic 'body' parameter
            # In a real implementation, this would need to be more sophisticated
            # and parse the actual request body schema
            schema["properties"]["body"] = {
                "type": "object",
                "description": f"Request body of type {operation.request_body_type}",
                "additionalProperties": True
            }
            # Request body is typically required for POST/PUT/PATCH
            if operation.method.upper() in ['POST', 'PUT', 'PATCH']:
                schema["required"].append("body")
        
        # If no properties were added, make it an empty object schema
        if not schema["properties"]:
            schema = {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            }
        
        return schema
    
    def _convert_openapi_type_to_json_schema(self, openapi_type: str) -> str:
        """
        Convert OpenAPI parameter type to JSON Schema type.
        
        Args:
            openapi_type: OpenAPI type string
            
        Returns:
            str: Corresponding JSON Schema type
        """
        type_mapping = {
            'string': 'string',
            'integer': 'integer', 
            'number': 'number',
            'boolean': 'boolean',
            'array': 'array',
            'object': 'object',
            'file': 'string',  # Files are typically handled as strings in MCP
        }
        
        return type_mapping.get(openapi_type.lower(), 'string')
    
    def _to_snake_case(self, text: str) -> str:
        """
        Convert text to snake_case.
        
        Args:
            text: Input text to convert
            
        Returns:
            str: Text converted to snake_case
        """
        if not text:
            return text
            
        # First, insert underscores before uppercase letters (camelCase -> camel_Case)
        text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
        
        # Replace spaces and hyphens with underscores
        text = re.sub(r'[\s\-]+', '_', text)
        
        # Remove special characters (keep only alphanumeric and underscores)
        text = re.sub(r'[^\w]', '_', text)
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove duplicate underscores
        text = re.sub(r'_+', '_', text)
        
        # Remove leading/trailing underscores
        text = text.strip('_')
        
        return text
        
    def generate_tool_implementations(self) -> str:
        """
        Generate Python code for MCP tool implementations
        
        Creates complete Python code that implements MCP tools for each
        API operation, including:
        - Tool registration with proper schemas
        - Implementation methods that call the API client
        - Error handling and response formatting
        - Type hints and documentation
        
        Returns:
            str: Complete Python code for tool implementations
            
        Example:
            mapper = MCPToolMapper(client_analysis)
            code = mapper.generate_tool_implementations()
            
            # Generated code includes:
            # - Tool registration decorators
            # - Implementation methods
            # - Error handling
            # - Response formatting
        """
        from jinja2 import Environment, FileSystemLoader
        import os
        
        # Get tool definitions
        tool_definitions = self.generate_tool_definitions()
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Load the tool implementations template
        template = env.get_template('tool_implementations.py.j2')
        
        # Prepare template context
        context = {
            'tool_definitions': tool_definitions,
            'client_analysis': self.client_analysis,
            'api_classes': self.client_analysis.api_classes,
            'operations': self.client_analysis.operations,
            'models': self.client_analysis.models,
            'client_package_name': self.client_analysis.client_package_name or 'generated_client'
        }
        
        # Render the template
        generated_code = template.render(**context)
        
        return generated_code
    
    def generate_tools_for_template(self, template_type: str = "openapi_enhanced", 
                                   project_name: str = "Generated API", 
                                   class_name: str = "GeneratedAPI") -> str:
        """
        Generate Python code for MCP tools using the tools.py.j2 template
        
        This method is compatible with the tools.py.j2 template structure and
        generates code that follows the expected pattern for MCP tools.
        
        Args:
            template_type: Type of template to use ("openapi_enhanced", "openapi", "python")
            project_name: Name of the project for documentation
            class_name: Name of the tools class to generate
            
        Returns:
            str: Complete Python code for MCP tools
            
        Raises:
            ValueError: If template type is not supported
            FileNotFoundError: If template files are not found
            
        Example:
            mapper = MCPToolMapper(client_analysis)
            code = mapper.generate_tools_for_template(
                template_type="openapi_enhanced",
                project_name="Pet Store API",
                class_name="PetStore"
            )
        """
        from jinja2 import Environment, FileSystemLoader
        import os
        
        # Validate template compatibility
        if not self.validate_template_compatibility(template_type):
            supported_types = self.get_supported_template_types()
            raise ValueError(
                f"Template type '{template_type}' is not supported. "
                f"Supported types: {', '.join(supported_types)}"
            )
        
        # Get tool definitions
        tool_definitions = self.generate_tool_definitions()
        
        # Setup Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), 'templates', template_type)
        env = Environment(loader=FileSystemLoader(template_dir))
        
        # Load the tools template
        try:
            template = env.get_template('tools.py.j2')
        except Exception as e:
            raise FileNotFoundError(f"Could not load tools.py.j2 template from {template_dir}: {e}")
        
        # Convert tool definitions to operations format expected by template
        operations = []
        for tool_def in tool_definitions:
            operation = {
                'tool_name': tool_def.name,
                'summary': tool_def.description,
                'description': tool_def.description,
                'input_schema': tool_def.input_schema,
                'method': tool_def.operation.method if tool_def.operation else 'GET',
                'path': tool_def.operation.path if tool_def.operation else '/',
                'operation_id': tool_def.name,
                'parameters': self._convert_operation_parameters(tool_def.operation) if tool_def.operation else [],
                'api_class': tool_def.operation.api_class if tool_def.operation else 'DefaultApi',
                'operation_name': tool_def.operation.name if tool_def.operation else tool_def.name
            }
            operations.append(operation)
        
        # Prepare template context
        context = {
            'project_name': project_name,
            'class_name': class_name,
            'api_classes': self.client_analysis.api_classes,
            'operations': operations,
            'models': self.client_analysis.models,
            'client_package_name': self.client_analysis.client_package_name or 'generated_client'
        }
        
        # Render the template
        generated_code = template.render(**context)
        
        return generated_code
    
    def _convert_operation_parameters(self, operation: Operation) -> List[Dict[str, Any]]:
        """
        Convert operation parameters to format expected by templates
        
        Args:
            operation: API operation with parameters
            
        Returns:
            List[Dict[str, Any]]: Parameters in template-expected format
        """
        if not operation or not operation.parameters:
            return []
        
        converted_params = []
        for param in operation.parameters:
            converted_param = {
                'name': param.get('name', 'unknown'),
                'in': param.get('in', 'query'),
                'description': param.get('description', ''),
                'required': param.get('required', False),
                'type': param.get('type', 'string'),
                'schema': {
                    'type': param.get('type', 'string')
                }
            }
            converted_params.append(converted_param)
        
        return converted_params
    
    def generate_tool_tests(self) -> str:
        """Generate tests for MCP tools"""
        # TODO: Implement tool test generation
        pass
    
    def validate_template_compatibility(self, template_type: str) -> bool:
        """
        Validate that the specified template type is supported
        
        Args:
            template_type: Template type to validate
            
        Returns:
            bool: True if template type is supported
        """
        import os
        
        supported_templates = ["openapi_enhanced", "openapi", "python"]
        if template_type not in supported_templates:
            return False
        
        # Check if template directory exists
        template_dir = os.path.join(os.path.dirname(__file__), 'templates', template_type)
        if not os.path.exists(template_dir):
            return False
        
        # Check if tools.py.j2 exists in the template directory
        tools_template = os.path.join(template_dir, 'tools.py.j2')
        return os.path.exists(tools_template)
    
    def get_supported_template_types(self) -> List[str]:
        """
        Get list of supported template types
        
        Returns:
            List[str]: List of supported template type names
        """
        import os
        
        template_base_dir = os.path.join(os.path.dirname(__file__), 'templates')
        if not os.path.exists(template_base_dir):
            return []
        
        supported_types = []
        for item in os.listdir(template_base_dir):
            template_dir = os.path.join(template_base_dir, item)
            if os.path.isdir(template_dir):
                tools_template = os.path.join(template_dir, 'tools.py.j2')
                if os.path.exists(tools_template):
                    supported_types.append(item)
        
        return supported_types