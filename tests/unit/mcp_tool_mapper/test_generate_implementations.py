"""
Unit tests for MCPToolMapper.generate_tool_implementations method

Tests the generation of Python code for MCP tool implementations.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from mcp_cli.mcp_tool_mapper import MCPToolMapper, ToolDefinition
from mcp_cli.openapi_client_generator import ClientAnalysis, Operation, ApiClass, Model


class TestMCPToolMapperImplementations:
    """Test cases for MCPToolMapper.generate_tool_implementations method"""
    
    @pytest.fixture
    def sample_operations(self) -> list[Operation]:
        """Create sample operations for testing"""
        return [
            Operation(
                name="list_pets",
                api_class="PetsApi",
                method="GET",
                path="/pets",
                parameters=[
                    {
                        "name": "limit",
                        "type": "integer",
                        "description": "Maximum number of pets to return",
                        "required": False,
                        "in": "query"
                    }
                ],
                summary="List all pets",
                description="Retrieve a list of pets with optional limit"
            ),
            Operation(
                name="get_pet_by_id",
                api_class="PetsApi",
                method="GET",
                path="/pets/{petId}",
                parameters=[
                    {
                        "name": "pet_id",
                        "type": "integer",
                        "description": "ID of pet to return",
                        "required": True,
                        "in": "path"
                    }
                ],
                summary="Get pet by ID",
                description="Retrieve a specific pet by its ID"
            ),
            Operation(
                name="create_pet",
                api_class="PetsApi",
                method="POST",
                path="/pets",
                parameters=[],
                request_body_type="Pet",
                summary="Create a pet",
                description="Create a new pet in the store"
            )
        ]
    
    @pytest.fixture
    def sample_client_analysis(self, sample_operations) -> ClientAnalysis:
        """Create a sample ClientAnalysis with operations"""
        return ClientAnalysis(
            api_classes=[
                ApiClass(name="PetsApi", module="pets_api", methods=["list_pets", "get_pet_by_id", "create_pet"])
            ],
            operations=sample_operations,
            models=[
                Model(name="Pet", properties=["id", "name", "status"]),
                Model(name="Error", properties=["code", "message"])
            ],
            client_package_name="petstore_client"
        )
    
    @pytest.fixture
    def tool_mapper(self, sample_client_analysis) -> MCPToolMapper:
        """Create MCPToolMapper instance for testing"""
        return MCPToolMapper(sample_client_analysis)
    
    def test_generate_tool_implementations_basic(self, tool_mapper):
        """Test basic tool implementations generation"""
        # Create temporary template directory
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Create the template file
            template_content = """# Test template
class TestTools:
    def __init__(self):
        pass
{% for tool in tool_definitions %}
    def {{ tool.name }}(self):
        return "{{ tool.description }}"
{% endfor %}"""
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            # Mock the template directory path
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = tool_mapper.generate_tool_implementations()
                
                # Verify the generated code contains expected elements
                assert "class TestTools:" in result
                assert "def list_pets(self):" in result
                assert "def get_pet_by_id(self):" in result
                assert "def create_pet(self):" in result
                assert "List all pets" in result
                assert "Get pet by ID" in result
                assert "Create a pet" in result
    
    def test_generate_tool_implementations_with_real_template(self, tool_mapper):
        """Test tool implementations generation with the actual template"""
        # Create temporary template directory with real template
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Copy the real template content
            real_template_path = Path(__file__).parent.parent.parent / "mcp_cli" / "templates" / "tool_implementations.py.j2"
            if real_template_path.exists():
                template_content = real_template_path.read_text()
            else:
                # Fallback template content for testing
                template_content = """
class GeneratedMCPTools:
    def __init__(self, server, api_client):
        self.server = server
        self.api_client = api_client
        {% for api_class in api_classes %}
        self.{{ api_class.name|lower }} = {{ api_class.name }}(api_client)
        {% endfor %}
    
    async def execute_tool(self, name, arguments):
        {% for tool in tool_definitions %}
        if name == "{{ tool.name }}":
            return await self._{{ tool.name }}(arguments)
        {% endfor %}
        raise ValueError(f"Unknown tool: {name}")
    
    {% for tool in tool_definitions %}
    async def _{{ tool.name }}(self, arguments):
        # {{ tool.description }}
        try:
            {% for param_name in tool.input_schema.get('required', []) %}
            if "{{ param_name }}" not in arguments:
                raise ValueError("Required parameter '{{ param_name }}' is missing")
            {% endfor %}
            
            api_instance = self.{{ tool.operation.api_class|lower }}
            result = api_instance.{{ tool.operation.name }}(**arguments)
            return result
        except Exception as e:
            return {"error": str(e), "tool": "{{ tool.name }}"}
    {% endfor %}
"""
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            # Mock the template directory path
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = tool_mapper.generate_tool_implementations()
                
                # Verify the generated code structure
                assert "class GeneratedMCPTools:" in result
                assert "def __init__(self, server" in result and "api_client):" in result
                assert "self.petsapi = PetsApi(api_client)" in result
                assert "async def execute_tool(self, name" in result and "arguments" in result
                
                # Verify individual tool methods
                assert "async def _list_pets(self, arguments" in result
                assert "async def _get_pet_by_id(self, arguments" in result
                assert "async def _create_pet(self, arguments" in result
                
                # Verify parameter validation
                assert 'if "pet_id" not in arguments:' in result
                assert 'raise ValueError("Required parameter \'pet_id\' is missing")' in result
                
                # Verify API calls
                assert "api_instance = self.petsapi" in result
                assert "result = api_instance.list_pets(**api_params)" in result
                assert "result = api_instance.get_pet_by_id(**api_params)" in result
                assert "result = api_instance.create_pet(**api_params)" in result
    
    def test_generate_tool_implementations_empty_operations(self):
        """Test tool implementations generation with no operations"""
        empty_analysis = ClientAnalysis(
            api_classes=[],
            operations=[],
            models=[],
            client_package_name="empty_client"
        )
        
        mapper = MCPToolMapper(empty_analysis)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            template_content = """
class GeneratedMCPTools:
    def __init__(self, server, api_client):
        self.server = server
        self.api_client = api_client
    
    async def execute_tool(self, name, arguments):
        {% for tool in tool_definitions %}
        if name == "{{ tool.name }}":
            return await self._{{ tool.name }}(arguments)
        {% endfor %}
        raise ValueError(f"Unknown tool: {name}")
"""
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = mapper.generate_tool_implementations()
                
                # Should generate basic structure even with no tools
                assert "class GeneratedMCPTools:" in result
                assert "def __init__(self, server, api_client):" in result
                assert "async def execute_tool(self, name, arguments):" in result
                assert 'raise ValueError(f"Unknown tool: {name}")' in result
    
    def test_generate_tool_implementations_complex_parameters(self):
        """Test tool implementations with complex parameter scenarios"""
        complex_operation = Operation(
            name="search_pets",
            api_class="PetsApi",
            method="GET",
            path="/pets/search",
            parameters=[
                {
                    "name": "query",
                    "type": "string",
                    "description": "Search query",
                    "required": True,
                    "in": "query"
                },
                {
                    "name": "category_id",
                    "type": "integer",
                    "description": "Category ID filter",
                    "required": False,
                    "in": "query"
                },
                {
                    "name": "status",
                    "type": "string",
                    "description": "Pet status filter",
                    "required": False,
                    "in": "query"
                }
            ],
            summary="Search pets",
            description="Search for pets with various filters"
        )
        
        analysis = ClientAnalysis(
            api_classes=[ApiClass(name="PetsApi", module="pets_api", methods=["search_pets"])],
            operations=[complex_operation],
            models=[],
            client_package_name="test_client"
        )
        
        mapper = MCPToolMapper(analysis)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            template_content = """
{% for tool in tool_definitions %}
async def _{{ tool.name }}(self, arguments):
    # Validate required parameters
    {% for param_name in tool.input_schema.get('required', []) %}
    if "{{ param_name }}" not in arguments:
        raise ValueError("Required parameter '{{ param_name }}' is missing")
    {% endfor %}
    
    # Extract parameters
    {% for param in tool.operation.parameters %}
    {{ param.get('name') }}_param = arguments.get("{{ param.get('name') }}")
    {% endfor %}
    
    return "success"
{% endfor %}
"""
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = mapper.generate_tool_implementations()
                
                # Verify parameter handling
                assert 'if "query" not in arguments:' in result
                assert 'raise ValueError("Required parameter \'query\' is missing")' in result
                assert "query_param = arguments.get(\"query\")" in result
                assert "category_id_param = arguments.get(\"category_id\")" in result
                assert "status_param = arguments.get(\"status\")" in result
    
    def test_generate_tool_implementations_with_request_body(self):
        """Test tool implementations for operations with request body"""
        post_operation = Operation(
            name="create_user",
            api_class="UsersApi",
            method="POST",
            path="/users",
            parameters=[],
            request_body_type="CreateUserRequest",
            summary="Create user",
            description="Create a new user account"
        )
        
        analysis = ClientAnalysis(
            api_classes=[ApiClass(name="UsersApi", module="users_api", methods=["create_user"])],
            operations=[post_operation],
            models=[Model(name="CreateUserRequest", properties=["username", "email"])],
            client_package_name="users_client"
        )
        
        mapper = MCPToolMapper(analysis)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            template_content = """
{% for tool in tool_definitions %}
async def _{{ tool.name }}(self, arguments):
    {% if tool.operation.request_body_type %}
    if "body" in arguments:
        request_body = arguments["body"]
    {% endif %}
    return "created"
{% endfor %}
"""
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = mapper.generate_tool_implementations()
                
                # Verify request body handling
                assert 'if "body" in arguments:' in result
                assert 'request_body = arguments["body"]' in result
    
    def test_generate_tool_implementations_template_not_found(self, tool_mapper):
        """Test behavior when template file is not found"""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            # Don't create the template file
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                with pytest.raises(Exception):  # Should raise TemplateNotFound or similar
                    tool_mapper.generate_tool_implementations()
    
    def test_generate_tool_implementations_template_context(self, tool_mapper):
        """Test that template receives correct context variables"""
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Template that uses all context variables
            template_content = """
# Client package: {{ client_package_name }}
# API classes: {% for api_class in api_classes %}{{ api_class.name }}{% if not loop.last %}, {% endif %}{% endfor %}
# Operations: {% for operation in operations %}{{ operation.name }}{% if not loop.last %}, {% endif %}{% endfor %}
# Models: {% for model in models %}{{ model.name }}{% if not loop.last %}, {% endif %}{% endfor %}
# Tools: {% for tool in tool_definitions %}{{ tool.name }}{% if not loop.last %}, {% endif %}{% endfor %}
"""
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = tool_mapper.generate_tool_implementations()
                
                # Verify context variables are properly passed
                assert "Client package: petstore_client" in result
                assert "API classes: PetsApi" in result
                assert "Operations: list_pets, get_pet_by_id, create_pet" in result
                assert "Models: Pet, Error" in result
                assert "Tools: list_pets, get_pet_by_id, create_pet" in result
    
    def test_generate_tool_implementations_integration(self, tool_mapper):
        """Integration test that verifies the complete flow"""
        # This test uses the actual template structure and verifies
        # that the generated code would be syntactically valid Python
        
        with tempfile.TemporaryDirectory() as temp_dir:
            template_dir = Path(temp_dir)
            
            # Minimal but complete template
            template_content = '''
import logging
from typing import Dict, Any, List, Union
from mcp.server import Server

{% for api_class in api_classes %}
from {{ client_package_name }}.api.{{ api_class.module }} import {{ api_class.name }}
{% endfor %}

logger = logging.getLogger(__name__)

class GeneratedMCPTools:
    def __init__(self, server: Server, api_client):
        self.server = server
        self.api_client = api_client
        {% for api_class in api_classes %}
        self.{{ api_class.name|lower }} = {{ api_class.name }}(api_client)
        {% endfor %}
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        {% for tool in tool_definitions %}
        if name == "{{ tool.name }}":
            return await self._{{ tool.name }}(arguments)
        {% endfor %}
        raise ValueError(f"Unknown tool: {name}")
    
    {% for tool in tool_definitions %}
    async def _{{ tool.name }}(self, arguments: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """{{ tool.description }}"""
        try:
            {% for param_name in tool.input_schema.get('required', []) %}
            if "{{ param_name }}" not in arguments:
                raise ValueError("Required parameter '{{ param_name }}' is missing")
            {% endfor %}
            
            api_instance = self.{{ tool.operation.api_class|lower }}
            result = api_instance.{{ tool.operation.name }}(**arguments)
            return result if result is not None else "Operation completed successfully"
        except Exception as e:
            return {"error": str(e), "tool": "{{ tool.name }}"}
    {% endfor %}
'''
            
            template_file = template_dir / "tool_implementations.py.j2"
            template_file.write_text(template_content)
            
            with patch('os.path.join') as mock_join:
                mock_join.return_value = str(template_dir)
                
                result = tool_mapper.generate_tool_implementations()
                
                # Verify the generated code is syntactically valid
                try:
                    compile(result, '<generated>', 'exec')
                    syntax_valid = True
                except SyntaxError:
                    syntax_valid = False
                
                assert syntax_valid, "Generated code should be syntactically valid Python"
                
                # Verify key components are present
                assert "class GeneratedMCPTools:" in result
                assert "from petstore_client.api.pets_api import PetsApi" in result
                assert "self.petsapi = PetsApi(api_client)" in result
                assert "async def _list_pets(self, arguments:" in result
                assert "async def _get_pet_by_id(self, arguments:" in result
                assert "async def _create_pet(self, arguments:" in result
                
                # Verify error handling
                assert 'return {"error": str(e), "tool":' in result
                
                # Verify parameter validation for required parameters
                assert 'if "pet_id" not in arguments:' in result
                assert 'raise ValueError("Required parameter \'pet_id\' is missing")' in result
    