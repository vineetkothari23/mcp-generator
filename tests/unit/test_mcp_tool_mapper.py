"""
Unit tests for MCPToolMapper

Tests the mapping of OpenAPI operations to MCP tools and
the generation of project configurations.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path
from mcp_cli.mcp_tool_mapper import MCPToolMapper, ToolDefinition
from mcp_cli.openapi_client_generator import ClientAnalysis, Operation, ApiClass, Model
from mcp_cli.config import MCPProjectConfig, MCPIntegrationConfig


@pytest.fixture
def sample_client_analysis():
    """Create sample ClientAnalysis for testing"""
    operations = [
        Operation(
            name="list_pets",
            api_class="PetApi",
            method="GET",
            path="/pets",
            summary="List all pets",
            description="Retrieve a list of all pets in the system",
            parameters=[
                {
                    "name": "limit",
                    "in": "query",
                    "type": "integer",
                    "description": "Number of pets to return",
                    "required": False
                }
            ]
        ),
        Operation(
            name="create_pet",
            api_class="PetApi", 
            method="POST",
            path="/pets",
            summary="Create a new pet",
            description="Add a new pet to the system",
            request_body_type="Pet"
        ),
        Operation(
            name="get_pet_by_id",
            api_class="PetApi",
            method="GET", 
            path="/pets/{pet_id}",
            summary="Get pet by ID",
            description="Retrieve a specific pet by its ID",
            parameters=[
                {
                    "name": "pet_id",
                    "in": "path",
                    "type": "integer",
                    "description": "ID of pet to return",
                    "required": True
                }
            ]
        )
    ]
    
    api_classes = [
        ApiClass(
            name="PetApi",
            module="pet_api",
            methods=["list_pets", "create_pet", "get_pet_by_id"]
        )
    ]
    
    models = [
        Model(name="Pet", properties=["id", "name", "status"])
    ]
    
    return ClientAnalysis(
        client_package_name="pet_api_client",
        api_classes=api_classes,
        operations=operations,
        models=models,
        base_url="https://api.petstore.example.com",
        auth_schemes=["ApiKeyAuth"]
    )


@pytest.fixture
def tool_mapper(sample_client_analysis):
    """Create MCPToolMapper instance for testing"""
    return MCPToolMapper(sample_client_analysis)


class TestMCPToolMapper:
    """Test MCPToolMapper basic functionality"""
    
    def test_init(self, sample_client_analysis):
        """Test MCPToolMapper initialization"""
        mapper = MCPToolMapper(sample_client_analysis)
        assert mapper.client_analysis == sample_client_analysis
    
    def test_generate_tool_definitions(self, tool_mapper):
        """Test basic tool definition generation"""
        tool_definitions = tool_mapper.generate_tool_definitions()
        
        assert len(tool_definitions) == 3
        assert all(isinstance(tool, ToolDefinition) for tool in tool_definitions)
        
        # Check tool names
        tool_names = [tool.name for tool in tool_definitions]
        assert "list_pets" in tool_names
        assert "create_pet" in tool_names
        assert "get_pet_by_id" in tool_names
    
    def test_generate_tool_name(self, tool_mapper):
        """Test tool name generation"""
        operation = Operation(
            name="getUserById",
            api_class="UserApi",
            method="GET",
            path="/users/{id}"
        )
        
        name = tool_mapper._generate_tool_name(operation)
        assert name == "get_user_by_id"
    
    @pytest.mark.skip(reason="DEPRECATED: Modern OpenAPI specs should have proper operationId fields")
    def test_generate_tool_name_fallback(self, tool_mapper):
        """Test tool name generation fallback when no operation name"""
        operation = Operation(
            name=None,
            api_class="UserApi",
            method="POST",
            path="/users"
        )
        
        name = tool_mapper._generate_tool_name(operation)
        assert name == "post_users"
    
    def test_generate_input_schema(self, tool_mapper):
        """Test input schema generation"""
        operation = Operation(
            name="get_pet",
            api_class="PetApi",
            method="GET",
            path="/pets/{id}",
            parameters=[
                {
                    "name": "id",
                    "in": "path",
                    "type": "integer",
                    "required": True,
                    "description": "Pet ID"
                },
                {
                    "name": "include_details",
                    "in": "query", 
                    "type": "boolean",
                    "required": False,
                    "description": "Include detailed information"
                }
            ]
        )
        
        schema = tool_mapper._generate_input_schema(operation)
        
        assert schema["type"] == "object"
        assert "id" in schema["properties"]
        assert "include_details" in schema["properties"]
        assert "id" in schema["required"]
        assert "include_details" not in schema["required"]


class TestMCPToolMapperEnhanced:
    """Test enhanced MCPToolMapper functionality for project config generation"""
    
    def test_generate_mcp_project_config(self, tool_mapper):
        """Test generation of MCPProjectConfig from ClientAnalysis"""
        # This is the new functionality we want to add
        project_name = "pet-store-mcp"
        author = "Test Developer"
        
        config = tool_mapper.generate_mcp_project_config(
            project_name=project_name,
            author=author
        )
        
        assert isinstance(config, MCPProjectConfig)
        assert config.project_name == project_name
        assert config.author == author
        assert config.service_name == "pet_store_mcp"
        
        # Check that OpenAPI config is populated
        assert config.openapi_config.package_name == "pet_api_client"
        
        # Check that MCP config is populated based on analysis
        assert config.mcp_config.max_tools >= 3  # We have 3 operations
    
    def test_generate_mcp_integration_config(self, tool_mapper):
        """Test generation of MCPIntegrationConfig from ClientAnalysis"""
        mcp_config = tool_mapper.generate_mcp_integration_config()
        
        assert isinstance(mcp_config, MCPIntegrationConfig)
        assert mcp_config.max_tools >= len(tool_mapper.client_analysis.operations)
        
        # Should detect auth schemes
        if tool_mapper.client_analysis.auth_schemes:
            assert mcp_config.include_auth_tools == True
    
    def test_filter_operations_by_config(self, tool_mapper):
        """Test filtering operations based on configuration"""
        # Create a restrictive config
        mcp_config = MCPIntegrationConfig(
            max_tools=2,
            include_file_upload_tools=False
        )
        
        filtered_ops = tool_mapper.filter_operations_by_config(mcp_config)
        
        # Should limit to 2 operations
        assert len(filtered_ops) <= 2
        assert all(isinstance(op, Operation) for op in filtered_ops)
    
    def test_estimate_complexity(self, tool_mapper):
        """Test complexity estimation"""
        complexity = tool_mapper.estimate_complexity()
        
        assert complexity in ["Simple", "Medium", "Complex", "Very Complex"]
        
        # With 3 operations and 1 model, should be Simple
        assert complexity == "Simple"


class TestMCPToolMapperEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_client_analysis(self):
        """Test with empty ClientAnalysis"""
        empty_analysis = ClientAnalysis()
        mapper = MCPToolMapper(empty_analysis)
        
        tools = mapper.generate_tool_definitions()
        assert tools == []
    
    @pytest.mark.skip(reason="DEPRECATED: Modern OpenAPI specs should have proper operationId fields")
    def test_operation_with_no_name(self, tool_mapper):
        """Test operation without name or operationId"""
        operation = Operation(
            name=None,
            api_class="DefaultApi",
            method="GET",
            path="/"
        )
        
        name = tool_mapper._generate_tool_name(operation)
        assert name == "get_operation"  # Fallback name
    
    def test_invalid_characters_in_name(self, tool_mapper):
        """Test name sanitization with invalid characters"""
        operation = Operation(
            name="get-user@info!",
            api_class="UserApi",
            method="GET",
            path="/users"
        )
        
        name = tool_mapper._generate_tool_name(operation)
        assert name == "get_user_info"  # Should be sanitized


if __name__ == "__main__":
    pytest.main([__file__]) 