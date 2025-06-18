"""
Unit tests for MCPToolMapper tool generation from OpenAPI specifications

Tests comprehensive OpenAPI → MCP tool mapping including:
- Path parameters (required)
- Query parameters (optional)  
- Request body mapping
- Authentication schemes
- Array/object parameters

These tests validate the tool generation accuracy and completeness.
"""
import pytest
from mcp_cli.mcp_tool_mapper import MCPToolMapper, ToolDefinition
from mcp_cli.openapi_client_generator import ClientAnalysis, Operation, ApiClass, Model


class TestToolGenerationFromOpenAPI:
    """Test comprehensive tool generation from OpenAPI specifications"""

    @pytest.fixture
    def sample_openapi_with_path_params(self):
        """
        OpenAPI spec with path parameters for testing
        
        Example: GET /users/{userId}/posts/{postId}
        Tests that path parameters become required tool parameters
        """
        return {
            "openapi": "3.0.0",
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {
                "/users/{userId}/posts/{postId}": {
                    "get": {
                        "operationId": "getUserPost",
                        "summary": "Get a specific user's post",
                        "description": "Retrieve a specific post from a specific user",
                        "parameters": [
                            {
                                "name": "userId",
                                "in": "path",
                                "required": True,
                                "description": "The unique identifier of the user",
                                "schema": {"type": "integer", "format": "int64"}
                            },
                            {
                                "name": "postId", 
                                "in": "path",
                                "required": True,
                                "description": "The unique identifier of the post",
                                "schema": {"type": "string"}
                            }
                        ]
                    }
                }
            }
        }

    @pytest.fixture
    def path_params_operation(self):
        """Create Operation with path parameters for testing"""
        return Operation(
            name="getUserPost",
            api_class="UsersApi",
            method="GET",
            path="/users/{userId}/posts/{postId}",
            parameters=[
                {
                    "name": "userId",
                    "type": "integer",
                    "description": "The unique identifier of the user",
                    "required": True,
                    "in": "path"
                },
                {
                    "name": "postId",
                    "type": "string", 
                    "description": "The unique identifier of the post",
                    "required": True,
                    "in": "path"
                }
            ],
            summary="Get a specific user's post",
            description="Retrieve a specific post from a specific user"
        )

    @pytest.fixture
    def path_params_client_analysis(self, path_params_operation):
        """Create ClientAnalysis with path parameters operation"""
        return ClientAnalysis(
            api_classes=[ApiClass(name="UsersApi", module="users_api")],
            operations=[path_params_operation],
            models=[Model(name="Post", properties=["id", "title", "content", "userId"])],
            client_package_name="test_path_params_client"
        )

    def test_path_parameters_mapping_to_required_tool_params(self, path_params_client_analysis):
        """
        Test that OpenAPI path parameters correctly map to required MCP tool parameters
        
        Validates:
        - Path parameters become required in tool schema
        - Parameter types are correctly converted (integer → integer, string → string)
        - Parameter descriptions are preserved
        - Tool name is correctly generated from operationId
        """
        # Create tool mapper and generate definitions
        mapper = MCPToolMapper(path_params_client_analysis)
        tool_definitions = mapper.generate_tool_definitions()
        
        # Should have one tool definition
        assert len(tool_definitions) == 1
        tool = tool_definitions[0]
        
        # Verify tool basic properties
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "get_user_post"
        assert tool.description == "Get a specific user's post"
        
        # Verify input schema structure
        assert tool.input_schema["type"] == "object"
        assert "properties" in tool.input_schema
        assert "required" in tool.input_schema
        
        # Verify path parameters are included as properties
        properties = tool.input_schema["properties"]
        assert "userId" in properties
        assert "postId" in properties
        
        # Verify userId parameter mapping
        user_id_param = properties["userId"]
        assert user_id_param["type"] == "integer"
        assert user_id_param["description"] == "The unique identifier of the user"
        
        # Verify postId parameter mapping  
        post_id_param = properties["postId"]
        assert post_id_param["type"] == "string"
        assert post_id_param["description"] == "The unique identifier of the post"
        
        # Verify both path parameters are required
        required_params = tool.input_schema["required"]
        assert "userId" in required_params
        assert "postId" in required_params
        assert len(required_params) == 2  # Only path parameters should be required
        
        # Verify operation reference is preserved
        assert tool.operation.name == "getUserPost"
        assert tool.operation.method == "GET"
        assert tool.operation.path == "/users/{userId}/posts/{postId}"

    @pytest.fixture
    def query_params_operation(self):
        """Create Operation with query parameters for testing"""
        return Operation(
            name="searchPosts",
            api_class="PostsApi",
            method="GET",
            path="/posts",
            parameters=[
                {
                    "name": "limit",
                    "type": "integer",
                    "description": "Maximum number of posts to return",
                    "required": False,
                    "in": "query"
                },
                {
                    "name": "category",
                    "type": "string",
                    "description": "Filter posts by category",
                    "required": False,
                    "in": "query"
                },
                {
                    "name": "published",
                    "type": "boolean",
                    "description": "Filter by published status",
                    "required": True,  # Required query parameter
                    "in": "query"
                }
            ],
            summary="Search posts with filters",
            description="Search and filter posts using query parameters"
        )

    @pytest.fixture
    def query_params_client_analysis(self, query_params_operation):
        """Create ClientAnalysis with query parameters operation"""
        return ClientAnalysis(
            api_classes=[ApiClass(name="PostsApi", module="posts_api")],
            operations=[query_params_operation],
            models=[Model(name="Post", properties=["id", "title", "content", "category"])],
            client_package_name="test_query_params_client"
        )

    def test_query_parameters_mapping_to_optional_tool_params(self, query_params_client_analysis):
        """
        Test that OpenAPI query parameters correctly map to MCP tool parameters
        
        Validates:
        - Optional query parameters are NOT in required list
        - Required query parameters ARE in required list  
        - Parameter types are correctly converted (boolean, integer, string)
        - Parameter descriptions are preserved
        - Tool schema allows optional parameters
        """
        # Create tool mapper and generate definitions
        mapper = MCPToolMapper(query_params_client_analysis)
        tool_definitions = mapper.generate_tool_definitions()
        
        # Should have one tool definition
        assert len(tool_definitions) == 1
        tool = tool_definitions[0]
        
        # Verify tool basic properties
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "search_posts"
        assert tool.description == "Search posts with filters"
        
        # Verify input schema structure
        assert tool.input_schema["type"] == "object"
        assert "properties" in tool.input_schema
        assert "required" in tool.input_schema
        
        # Verify all query parameters are included as properties
        properties = tool.input_schema["properties"]
        assert "limit" in properties
        assert "category" in properties
        assert "published" in properties
        
        # Verify limit parameter (optional integer)
        limit_param = properties["limit"]
        assert limit_param["type"] == "integer"
        assert limit_param["description"] == "Maximum number of posts to return"
        
        # Verify category parameter (optional string)
        category_param = properties["category"]
        assert category_param["type"] == "string" 
        assert category_param["description"] == "Filter posts by category"
        
        # Verify published parameter (required boolean)
        published_param = properties["published"]
        assert published_param["type"] == "boolean"
        assert published_param["description"] == "Filter by published status"
        
        # Verify required parameters - only 'published' should be required
        required_params = tool.input_schema["required"]
        assert "published" in required_params
        assert "limit" not in required_params  # Optional
        assert "category" not in required_params  # Optional
        assert len(required_params) == 1  # Only 'published' is required
        
        # Verify operation reference is preserved
        assert tool.operation.name == "searchPosts"
        assert tool.operation.method == "GET"
        assert tool.operation.path == "/posts"

    @pytest.fixture
    def request_body_operation(self):
        """Create Operation with request body for testing"""
        return Operation(
            name="createPost",
            api_class="PostsApi",
            method="POST",
            path="/posts",
            parameters=[
                {
                    "name": "x-request-id",
                    "type": "string",
                    "description": "Unique request identifier",
                    "required": False,
                    "in": "header"
                }
            ],
            request_body_type="CreatePostRequest",
            summary="Create a new post",
            description="Create a new blog post with title and content"
        )

    @pytest.fixture 
    def request_body_client_analysis(self, request_body_operation):
        """Create ClientAnalysis with request body operation"""
        return ClientAnalysis(
            api_classes=[ApiClass(name="PostsApi", module="posts_api")],
            operations=[request_body_operation],
            models=[
                Model(name="Post", properties=["id", "title", "content", "createdAt"]),
                Model(name="CreatePostRequest", properties=["title", "content", "tags"])
            ],
            client_package_name="test_request_body_client"
        )

    def test_request_body_mapping_to_tool_body_param(self, request_body_client_analysis):
        """
        Test that OpenAPI request body correctly maps to MCP tool body parameter
        
        Validates:
        - Request body creates a 'body' parameter in tool schema
        - Body parameter is required for POST/PUT/PATCH operations
        - Body parameter type is 'object' with additionalProperties
        - Header parameters are included alongside body
        - Tool description and naming work correctly for body operations
        """
        # Create tool mapper and generate definitions
        mapper = MCPToolMapper(request_body_client_analysis)
        tool_definitions = mapper.generate_tool_definitions()
        
        # Should have one tool definition
        assert len(tool_definitions) == 1
        tool = tool_definitions[0]
        
        # Verify tool basic properties
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "create_post"
        assert tool.description == "Create a new post"
        
        # Verify input schema structure
        assert tool.input_schema["type"] == "object"
        assert "properties" in tool.input_schema
        assert "required" in tool.input_schema
        
        # Verify properties include both header param and body
        properties = tool.input_schema["properties"]
        assert "x-request-id" in properties  # Header parameter
        assert "body" in properties  # Request body
        
        # Verify header parameter (optional)
        header_param = properties["x-request-id"]
        assert header_param["type"] == "string"
        assert header_param["description"] == "Unique request identifier"
        
        # Verify body parameter
        body_param = properties["body"]
        assert body_param["type"] == "object"
        assert body_param["description"] == "Request body of type CreatePostRequest"
        assert body_param["additionalProperties"] == True
        
        # Verify required parameters - body should be required for POST operations
        required_params = tool.input_schema["required"]
        assert "body" in required_params
        assert "x-request-id" not in required_params  # Header is optional
        assert len(required_params) == 1  # Only body is required
        
        # Verify operation reference is preserved
        assert tool.operation.name == "createPost"
        assert tool.operation.method == "POST"
        assert tool.operation.path == "/posts"
        assert tool.operation.request_body_type == "CreatePostRequest"

    @pytest.fixture
    def auth_operation(self):
        """Create Operation with authentication requirements for testing"""
        return Operation(
            name="getSecureData",
            api_class="SecureApi",
            method="GET",
            path="/secure/data/{dataId}",
            parameters=[
                {
                    "name": "dataId",
                    "type": "string",
                    "description": "The ID of the secure data to retrieve",
                    "required": True,
                    "in": "path"
                }
            ],
            auth_required=True,
            summary="Get secure data with authentication",
            description="Retrieve secure data that requires basic authentication"
        )

    @pytest.fixture
    def auth_client_analysis(self, auth_operation):
        """Create ClientAnalysis with authentication schemes"""
        return ClientAnalysis(
            api_classes=[ApiClass(name="SecureApi", module="secure_api")],
            operations=[auth_operation],
            models=[Model(name="SecureData", properties=["id", "content", "classification"])],
            client_package_name="test_auth_client",
            auth_schemes=["basicAuth", "bearerAuth"]  # Multiple auth schemes
        )

    def test_authentication_schemes_in_client_analysis(self, auth_client_analysis):
        """
        Test that authentication schemes are properly included in ClientAnalysis and tool generation
        
        Validates:
        - Authentication schemes are preserved in ClientAnalysis
        - Auth-required operations are marked correctly
        - Tool generation works with authenticated operations
        - Tool metadata includes authentication information
        - Multiple auth schemes are handled properly
        """
        # Verify ClientAnalysis includes auth schemes
        assert auth_client_analysis.auth_schemes is not None
        assert len(auth_client_analysis.auth_schemes) == 2
        assert "basicAuth" in auth_client_analysis.auth_schemes
        assert "bearerAuth" in auth_client_analysis.auth_schemes
        
        # Create tool mapper and generate definitions
        mapper = MCPToolMapper(auth_client_analysis)
        tool_definitions = mapper.generate_tool_definitions()
        
        # Should have one tool definition
        assert len(tool_definitions) == 1
        tool = tool_definitions[0]
        
        # Verify tool basic properties
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "get_secure_data"
        assert tool.description == "Get secure data with authentication"
        
        # Verify input schema includes path parameter
        properties = tool.input_schema["properties"]
        assert "dataId" in properties
        
        # Verify dataId parameter
        data_id_param = properties["dataId"]
        assert data_id_param["type"] == "string"
        assert data_id_param["description"] == "The ID of the secure data to retrieve"
        
        # Verify required parameters
        required_params = tool.input_schema["required"]
        assert "dataId" in required_params
        
        # Verify operation reference preserves auth information
        assert tool.operation.name == "getSecureData"
        assert tool.operation.auth_required == True
        assert tool.operation.method == "GET"
        assert tool.operation.path == "/secure/data/{dataId}"

    @pytest.fixture
    def complex_params_operation(self):
        """Create Operation with array and object parameters for testing"""
        return Operation(
            name="updateUserPreferences",
            api_class="UsersApi",
            method="PUT",
            path="/users/{userId}/preferences",
            parameters=[
                {
                    "name": "userId",
                    "type": "string",
                    "description": "User identifier",
                    "required": True,
                    "in": "path"
                },
                {
                    "name": "tags",
                    "type": "array",
                    "description": "Array of preference tags",
                    "required": False,
                    "in": "query"
                },
                {
                    "name": "metadata",
                    "type": "object",
                    "description": "Additional metadata object",
                    "required": False,
                    "in": "query"
                }
            ],
            request_body_type="UserPreferences",
            summary="Update user preferences with complex data",
            description="Update user preferences using arrays and objects"
        )

    @pytest.fixture
    def complex_params_client_analysis(self, complex_params_operation):
        """Create ClientAnalysis with complex parameter types"""
        return ClientAnalysis(
            api_classes=[ApiClass(name="UsersApi", module="users_api")],
            operations=[complex_params_operation],
            models=[
                Model(name="UserPreferences", properties=["theme", "notifications", "privacy"]),
                Model(name="User", properties=["id", "email", "preferences"])
            ],
            client_package_name="test_complex_params_client"
        )

    def test_array_and_object_parameters_mapping(self, complex_params_client_analysis):
        """
        Test that OpenAPI array and object parameters correctly map to MCP tool parameters
        
        Validates:
        - Array parameters map to "array" type in JSON schema
        - Object parameters map to "object" type in JSON schema
        - Complex types preserve descriptions and optional status
        - Mixed parameter types (path, query, body) work together
        - Tool generation handles complex type combinations
        """
        # Create tool mapper and generate definitions
        mapper = MCPToolMapper(complex_params_client_analysis)
        tool_definitions = mapper.generate_tool_definitions()
        
        # Should have one tool definition
        assert len(tool_definitions) == 1
        tool = tool_definitions[0]
        
        # Verify tool basic properties
        assert isinstance(tool, ToolDefinition)
        assert tool.name == "update_user_preferences"
        assert tool.description == "Update user preferences with complex data"
        
        # Verify input schema structure
        assert tool.input_schema["type"] == "object"
        assert "properties" in tool.input_schema
        assert "required" in tool.input_schema
        
        # Verify all parameters are included
        properties = tool.input_schema["properties"]
        assert "userId" in properties  # Path parameter
        assert "tags" in properties    # Array parameter
        assert "metadata" in properties  # Object parameter  
        assert "body" in properties    # Request body
        
        # Verify userId parameter (path - required)
        user_id_param = properties["userId"]
        assert user_id_param["type"] == "string"
        assert user_id_param["description"] == "User identifier"
        
        # Verify tags parameter (array - optional)
        tags_param = properties["tags"]
        assert tags_param["type"] == "array"
        assert tags_param["description"] == "Array of preference tags"
        
        # Verify metadata parameter (object - optional)
        metadata_param = properties["metadata"]
        assert metadata_param["type"] == "object"
        assert metadata_param["description"] == "Additional metadata object"
        
        # Verify body parameter (object - required for PUT)
        body_param = properties["body"]
        assert body_param["type"] == "object"
        assert body_param["description"] == "Request body of type UserPreferences"
        
        # Verify required parameters - only path param and body should be required
        required_params = tool.input_schema["required"]
        assert "userId" in required_params  # Path parameter
        assert "body" in required_params    # Request body for PUT
        assert "tags" not in required_params  # Optional query param
        assert "metadata" not in required_params  # Optional query param
        assert len(required_params) == 2
        
        # Verify operation reference is preserved
        assert tool.operation.name == "updateUserPreferences"
        assert tool.operation.method == "PUT"
        assert tool.operation.path == "/users/{userId}/preferences"
        assert tool.operation.request_body_type == "UserPreferences"


if __name__ == "__main__":
    pytest.main([__file__]) 