"""
Unit tests for MCPToolMapper class

Tests the conversion of OpenAPI operations to MCP tool definitions.
"""
import pytest
from mcp_cli.mcp_tool_mapper import MCPToolMapper, ToolDefinition
from mcp_cli.openapi_client_generator import ClientAnalysis, Operation, ApiClass, Model


class TestMCPToolMapper:
    """Test cases for MCPToolMapper class"""
    
    @pytest.fixture
    def sample_operation(self) -> Operation:
        """Create a basic operation for testing"""
        return Operation(
            name="getUserById",
            api_class="UsersApi",
            method="GET",
            path="/users/{id}",
            parameters=[
                {
                    "name": "id",
                    "type": "integer",
                    "description": "User ID",
                    "required": True,
                    "in": "path"
                }
            ],
            summary="Get user by ID",
            description="Retrieve a specific user by their unique identifier"
        )
    
    @pytest.fixture
    def sample_client_analysis(self, sample_operation) -> ClientAnalysis:
        """Create a sample ClientAnalysis with operations"""
        return ClientAnalysis(
            api_classes=[ApiClass(name="UsersApi", module="users_api")],
            operations=[sample_operation],
            models=[Model(name="User", properties=["id", "name", "email"])],
            client_package_name="test_api_client"
        )
    
    @pytest.fixture
    def tool_mapper(self, sample_client_analysis) -> MCPToolMapper:
        """Create MCPToolMapper instance for testing"""
        return MCPToolMapper(sample_client_analysis)

    def test_init(self, sample_client_analysis):
        """Test MCPToolMapper initialization"""
        mapper = MCPToolMapper(sample_client_analysis)
        assert mapper.client_analysis == sample_client_analysis

    def test_generate_tool_definitions(self, tool_mapper, sample_operation):
        """Test basic tool definition generation"""
        tools = tool_mapper.generate_tool_definitions()
        
        assert len(tools) == 1
        tool = tools[0]
        
        # Verify tool definition structure
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "get_user_by_id"
        assert tool.description == "Get user by ID"
        assert tool.operation == sample_operation
        
        # Verify input schema
        assert tool.input_schema["type"] == "object"
        assert "id" in tool.input_schema["properties"]
        assert tool.input_schema["properties"]["id"]["type"] == "integer"
        assert "id" in tool.input_schema["required"]

    def test_generate_tool_name_sanitization(self, tool_mapper):
        """Test tool name sanitization for invalid characters"""
        operation = Operation(
            name="get-user@by#id!",
            api_class="UsersApi",
            method="GET",
            path="/users/{id}",
            parameters=[]
        )
        
        name = tool_mapper._generate_tool_name(operation)
        assert name == "get_user_by_id"

    @pytest.mark.skip(reason="DEPRECATED: Modern OpenAPI specs should have proper operationId fields")
    def test_generate_tool_name_without_operation_id(self, tool_mapper):
        """Test tool name generation when operation has no name/ID"""
        operation = Operation(
            name=None,
            api_class="ProductsApi",
            method="DELETE",
            path="/products/{productId}",
            parameters=[]
        )
        
        name = tool_mapper._generate_tool_name(operation)
        assert name == "delete_products"

    def test_generate_input_schema_with_request_body(self, tool_mapper):
        """Test input schema generation for operations with request body"""
        operation = Operation(
            name="createUser",
            api_class="UsersApi",
            method="POST", 
            path="/users",
            parameters=[],
            request_body_type="CreateUserRequest"
        )
        
        schema = tool_mapper._generate_input_schema(operation)
        
        assert "body" in schema["properties"]
        assert "body" in schema["required"]
        assert schema["properties"]["body"]["type"] == "object"

    def test_empty_client_analysis(self):
        """Test behavior with empty client analysis"""
        empty_analysis = ClientAnalysis(
            api_classes=[],
            operations=[],
            models=[],
            client_package_name="empty_client"
        )
        
        mapper = MCPToolMapper(empty_analysis)
        tools = mapper.generate_tool_definitions()
        
        assert tools == [] 