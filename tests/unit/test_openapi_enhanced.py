# tests/unit/test_openapi_enhanced.py
"""
Tests for enhanced OpenAPI generation using openapi-generator

These tests define the expected behavior of the enhanced OpenAPI generator
that uses openapi-generator CLI tool for robust API client generation.
"""

import pytest
import tempfile
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

# Import the classes we'll be implementing
from mcp_cli.openapi_client_generator import OpenAPIClientGenerator, ClientAnalysis
from mcp_cli.mcp_tool_mapper import MCPToolMapper, ToolDefinition
from mcp_cli.generators import OpenAPIEnhancedGenerator
from mcp_cli.config import OpenAPIGeneratorConfig, MCPIntegrationConfig
from mcp_cli.validators import ValidationResult, GenerationResult

# Sample OpenAPI specification for testing
SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Pet Store API",
        "version": "1.0.0",
        "description": "A simple pet store API"
    },
    "servers": [
        {"url": "https://petstore.example.com/api/v1"}
    ],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer"
            }
        },
        "schemas": {
            "Pet": {
                "type": "object",
                "required": ["id", "name"],
                "properties": {
                    "id": {"type": "integer", "format": "int64"},
                    "name": {"type": "string"},
                    "status": {"type": "string", "enum": ["available", "pending", "sold"]}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "code": {"type": "integer"},
                    "message": {"type": "string"}
                }
            }
        }
    },
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "description": "How many items to return at one time",
                        "required": False,
                        "schema": {"type": "integer", "maximum": 100}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A paged array of pets",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/Pet"}
                                }
                            }
                        }
                    }
                },
                "security": [{"ApiKeyAuth": []}]
            },
            "post": {
                "operationId": "createPet",
                "summary": "Create a pet",
                "tags": ["pets"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Pet"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Pet created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        }
                    }
                },
                "security": [{"BearerAuth": []}]
            }
        },
        "/pets/{petId}": {
            "get": {
                "operationId": "getPetById",
                "summary": "Get a pet by ID",
                "tags": ["pets"],
                "parameters": [
                    {
                        "name": "petId",
                        "in": "path",
                        "required": True,
                        "description": "The id of the pet to retrieve",
                        "schema": {"type": "integer", "format": "int64"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "A pet",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Pet"}
                            }
                        }
                    },
                    "404": {
                        "description": "Pet not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Error"}
                            }
                        }
                    }
                }
            }
        }
    }
}

# Mock project config for testing
@dataclass
class MockProjectConfig:
    project_name: str = "pet-store-mcp"
    service_name: str = "pet_store"
    description: str = "Pet Store MCP Server"
    author: str = "Test Author"
    version: str = "1.0.0"
    python_version: str = "3.11"
    output_dir: str = "."

class TestOpenAPIClientGenerator:
    """Test the OpenAPIClientGenerator class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.generator = OpenAPIClientGenerator()
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        self.config = MockProjectConfig()
    
    def test_check_openapi_generator_installed(self):
        """Test checking if openapi-generator is installed"""
        # Test when openapi-generator is available
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            assert self.generator.check_openapi_generator_installed() is True
            mock_run.assert_called_once_with(
                ['openapi-generator', 'version'], 
                capture_output=True, 
                text=True
            )
        
        # Test when openapi-generator is not available
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError()
            assert self.generator.check_openapi_generator_installed() is False
    
    def test_generate_python_client_sync(self):
        """Test generating synchronous Python client"""
        spec_path = self.project_path / "spec.json"
        with open(spec_path, 'w') as f:
            json.dump(SAMPLE_OPENAPI_SPEC, f)
        
        output_dir = self.project_path / "generated"
        
        config = OpenAPIGeneratorConfig(
            generator_type="python",
            package_name="pet_store_client",
            client_type="sync",
            additional_properties={"packageVersion": "1.0.0"}
        )
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Successfully generated"
            mock_run.return_value.stderr = ""
            
            # Mock the generated files
            client_dir = output_dir / "pet_store_client"
            client_dir.mkdir(parents=True, exist_ok=True)
            (client_dir / "__init__.py").touch()
            (client_dir / "api_client.py").touch()
            (client_dir / "configuration.py").touch()
            
            result = self.generator.generate_python_client(str(spec_path), output_dir, config)
            
            assert result.success is True
            assert len(result.files_created) > 0
            assert str(client_dir) in result.files_created
            
            # Verify openapi-generator was called with correct arguments
            expected_args = [
                "openapi-generator", "generate",
                "-i", str(spec_path),
                "-g", "python",
                "-o", str(output_dir),
                "--package-name", "pet_store_client",
                "--additional-properties", "packageVersion=1.0.0"
            ]
            mock_run.assert_called_once()
            actual_args = mock_run.call_args[0][0]
            assert all(arg in actual_args for arg in expected_args)
    
    def test_generate_python_client_async(self):
        """Test generating asynchronous Python client"""
        spec_path = self.project_path / "spec.json"
        with open(spec_path, 'w') as f:
            json.dump(SAMPLE_OPENAPI_SPEC, f)
        
        output_dir = self.project_path / "generated"
        
        config = OpenAPIGeneratorConfig(
            generator_type="python",
            package_name="pet_store_client",
            client_type="asyncio",
            additional_properties={"packageVersion": "1.0.0"}
        )
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            
            result = self.generator.generate_python_client(str(spec_path), output_dir, config)
            
            # Verify async-specific configuration
            actual_args = mock_run.call_args[0][0]
            assert "--additional-properties" in actual_args
            props_index = actual_args.index("--additional-properties")
            props_value = actual_args[props_index + 1]
            assert "asyncio=true" in props_value or "library=asyncio" in props_value
    
    def test_generate_client_failure(self):
        """Test handling of openapi-generator failures"""
        spec_path = self.project_path / "invalid_spec.json"
        with open(spec_path, 'w') as f:
            json.dump({"invalid": "spec"}, f)
        
        output_dir = self.project_path / "generated"
        config = OpenAPIGeneratorConfig()
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "Validation failed: Invalid OpenAPI spec"
            
            result = self.generator.generate_python_client(str(spec_path), output_dir, config)
            
            assert result.success is False
            assert "Validation failed" in str(result.errors)
    
    def test_parse_generated_client(self):
        """Test parsing generated client to extract API information"""
        # Create mock generated client structure
        client_dir = self.project_path / "generated_client"
        api_dir = client_dir / "api"
        models_dir = client_dir / "models"
        
        for directory in [client_dir, api_dir, models_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create mock API files
        (api_dir / "__init__.py").touch()
        (api_dir / "pets_api.py").write_text('''
class PetsApi:
    def list_pets(self, limit=None):
        """List all pets"""
        pass
    
    def create_pet(self, pet):
        """Create a pet"""
        pass
    
    def get_pet_by_id(self, pet_id):
        """Get a pet by ID"""
        pass
''')
        
        # Create mock model files
        (models_dir / "__init__.py").touch()
        (models_dir / "pet.py").write_text('''
class Pet:
    def __init__(self, id=None, name=None, status=None):
        self.id = id
        self.name = name
        self.status = status
''')
        
        analysis = self.generator.parse_generated_client(client_dir)
        
        assert isinstance(analysis, ClientAnalysis)
        assert len(analysis.api_classes) >= 1
        assert any(api.name == "PetsApi" for api in analysis.api_classes)
        assert len(analysis.operations) >= 3
        assert any(op.name == "list_pets" for op in analysis.operations)
        assert any(op.name == "create_pet" for op in analysis.operations)
        assert any(op.name == "get_pet_by_id" for op in analysis.operations)
    
    def test_validate_generated_client(self):
        """Test validation of generated client"""
        # Test valid client
        client_dir = self.project_path / "valid_client"
        client_dir.mkdir(parents=True, exist_ok=True)
        (client_dir / "__init__.py").touch()
        (client_dir / "api_client.py").touch()
        (client_dir / "configuration.py").touch()
        
        result = self.generator.validate_generated_client(client_dir)
        assert result.is_valid is True
        
        # Test invalid client (missing files)
        invalid_dir = self.project_path / "invalid_client"
        invalid_dir.mkdir(parents=True, exist_ok=True)
        
        result = self.generator.validate_generated_client(invalid_dir)
        assert result.is_valid is False
        assert any("missing" in error.lower() for error in result.errors)

class TestMCPToolMapper:
    """Test the MCPToolMapper class"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Create mock client analysis
        self.client_analysis = ClientAnalysis(
            api_classes=[
                Mock(name="PetsApi", module="pets_api", methods=["list_pets", "create_pet", "get_pet_by_id"])
            ],
            operations=[
                Mock(
                    name="list_pets",
                    api_class="PetsApi", 
                    method="GET",
                    path="/pets",
                    parameters=[{"name": "limit", "type": "integer", "required": False}],
                    summary="List all pets",
                    description="Retrieve a list of pets with optional limit"
                ),
                Mock(
                    name="create_pet",
                    api_class="PetsApi",
                    method="POST", 
                    path="/pets",
                    parameters=[{"name": "pet", "type": "Pet", "required": True}],
                    summary="Create a pet",
                    description="Create a new pet in the store"
                ),
                Mock(
                    name="get_pet_by_id",
                    api_class="PetsApi",
                    method="GET",
                    path="/pets/{petId}",
                    parameters=[{"name": "pet_id", "type": "integer", "required": True}],
                    summary="Get a pet by ID",
                    description="Retrieve a specific pet by its ID"
                )
            ],
            models=[
                Mock(name="Pet", properties=["id", "name", "status"]),
                Mock(name="Error", properties=["code", "message"])
            ]
        )
        
        self.tool_mapper = MCPToolMapper(self.client_analysis)
        self.config = MCPIntegrationConfig(max_tools=50, tool_naming_convention="operation_id")
    
    def test_generate_tool_definitions(self):
        """Test generating MCP tool definitions from API operations"""
        tool_definitions = self.tool_mapper.generate_tool_definitions()
        
        assert len(tool_definitions) == 3
        
        # Test list_pets tool
        list_pets_tool = next(tool for tool in tool_definitions if tool.name == "list_pets")
        assert list_pets_tool.description == "List all pets"
        assert list_pets_tool.input_schema["type"] == "object"
        assert "limit" in list_pets_tool.input_schema["properties"]
        assert list_pets_tool.input_schema["properties"]["limit"]["type"] == "integer"
        assert "limit" not in list_pets_tool.input_schema.get("required", [])
        
        # Test create_pet tool
        create_pet_tool = next(tool for tool in tool_definitions if tool.name == "create_pet")
        assert create_pet_tool.description == "Create a pet"
        assert "pet" in create_pet_tool.input_schema["properties"]
        assert "pet" in create_pet_tool.input_schema["required"]
        
        # Test get_pet_by_id tool
        get_pet_tool = next(tool for tool in tool_definitions if tool.name == "get_pet_by_id")
        assert get_pet_tool.description == "Get a pet by ID"
        assert "pet_id" in get_pet_tool.input_schema["properties"]
        assert "pet_id" in get_pet_tool.input_schema["required"]
    
    def test_generate_tool_implementations(self):
        """Test generating Python code for MCP tool implementations"""
        implementation_code = self.tool_mapper.generate_tool_implementations()
        
        assert isinstance(implementation_code, str)
        assert "class" in implementation_code
        assert "async def execute_tool" in implementation_code
        assert "list_pets" in implementation_code
        assert "create_pet" in implementation_code
        assert "get_pet_by_id" in implementation_code
        
        # Verify that the code includes proper API client calls
        assert "self.pets_api.list_pets" in implementation_code
        assert "self.pets_api.create_pet" in implementation_code
        assert "self.pets_api.get_pet_by_id" in implementation_code
        
        # Verify error handling
        assert "try:" in implementation_code
        assert "except" in implementation_code
    
    def test_generate_tool_tests(self):
        """Test generating tests for MCP tools"""
        test_code = self.tool_mapper.generate_tool_tests()
        
        assert isinstance(test_code, str)
        assert "class Test" in test_code
        assert "async def test_" in test_code
        assert "test_list_pets" in test_code
        assert "test_create_pet" in test_code
        assert "test_get_pet_by_id" in test_code
        
        # Verify mock usage in tests
        assert "mock" in test_code.lower()
        assert "assert" in test_code
    
    def test_tool_naming_conventions(self):
        """Test different tool naming conventions"""
        # Test operation_id naming
        config_op_id = MCPIntegrationConfig(tool_naming_convention="operation_id")
        mapper_op_id = MCPToolMapper(self.client_analysis)
        mapper_op_id.config = config_op_id
        
        tools_op_id = mapper_op_id.generate_tool_definitions()
        tool_names_op_id = [tool.name for tool in tools_op_id]
        assert "list_pets" in tool_names_op_id
        assert "create_pet" in tool_names_op_id
        
        # Test path_method naming
        config_path = MCPIntegrationConfig(tool_naming_convention="path_method")
        mapper_path = MCPToolMapper(self.client_analysis)
        mapper_path.config = config_path
        
        tools_path = mapper_path.generate_tool_definitions()
        tool_names_path = [tool.name for tool in tools_path]
        assert "get_pets" in tool_names_path
        assert "post_pets" in tool_names_path

class TestOpenAPIEnhancedGenerator:
    """Test the main OpenAPIEnhancedGenerator class"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.generator = OpenAPIEnhancedGenerator()
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir)
        self.config = MockProjectConfig()
    
    @patch('mcp_cli.openapi_client_generator.OpenAPIClientGenerator')
    @patch('mcp_cli.mcp_tool_mapper.MCPToolMapper')
    def test_client_generation(self, mock_tool_mapper, mock_client_generator):
        """Test that openapi-generator client is created correctly"""
        # Setup mocks
        mock_client_gen_instance = mock_client_generator.return_value
        mock_client_gen_instance.check_openapi_generator_installed.return_value = True
        mock_client_gen_instance.generate_python_client.return_value = GenerationResult(
            success=True,
            files_created=["generated_client/__init__.py", "generated_client/api_client.py"],
            errors=[],
            warnings=[]
        )
        
        mock_analysis = ClientAnalysis(
            api_classes=[Mock(name="PetsApi")],
            operations=[Mock(name="list_pets")],
            models=[Mock(name="Pet")]
        )
        mock_client_gen_instance.parse_generated_client.return_value = mock_analysis
        
        mock_tool_mapper_instance = mock_tool_mapper.return_value
        mock_tool_mapper_instance.generate_tool_definitions.return_value = [
            ToolDefinition(name="list_pets", description="List pets", input_schema={})
        ]
        
        # Test generation
        result = self.generator.generate(
            self.project_path, 
            self.config, 
            SAMPLE_OPENAPI_SPEC,
            include_examples=False,
            max_tools=50
        )
        
        assert result.success is True
        assert len(result.files_created) > 0
        
        # Verify client generator was called
        mock_client_gen_instance.check_openapi_generator_installed.assert_called_once()
        mock_client_gen_instance.generate_python_client.assert_called_once()
        mock_client_gen_instance.parse_generated_client.assert_called_once()
        
        # Verify tool mapper was used
        mock_tool_mapper.assert_called_once_with(mock_analysis)
        mock_tool_mapper_instance.generate_tool_definitions.assert_called_once()
    
    def test_tool_mapping(self):
        """Test that API operations are mapped to MCP tools correctly"""
        with patch.object(self.generator, '_generate_api_client') as mock_gen_client, \
             patch.object(self.generator, '_analyze_generated_client') as mock_analyze, \
             patch.object(self.generator, '_generate_mcp_tools') as mock_gen_tools:
            
            # Setup mock returns
            mock_gen_client.return_value = GenerationResult(True, [], [], [])
            mock_analyze.return_value = ClientAnalysis(
                api_classes=[Mock(name="PetsApi")],
                operations=[
                    Mock(name="list_pets", summary="List all pets"),
                    Mock(name="create_pet", summary="Create a pet"),
                    Mock(name="get_pet_by_id", summary="Get pet by ID")
                ],
                models=[]
            )
            mock_gen_tools.return_value = GenerationResult(True, ["tools.py"], [], [])
            
            result = self.generator.generate(
                self.project_path,
                self.config, 
                SAMPLE_OPENAPI_SPEC
            )
            
            # Verify all operations were processed
            analysis = mock_analyze.return_value
            assert len(analysis.operations) == 3
            assert any(op.name == "list_pets" for op in analysis.operations)
            assert any(op.name == "create_pet" for op in analysis.operations)
            assert any(op.name == "get_pet_by_id" for op in analysis.operations)
    
    def test_authentication_integration(self):
        """Test that authentication schemes are properly integrated"""
        # OpenAPI spec with multiple auth schemes
        auth_spec = SAMPLE_OPENAPI_SPEC.copy()
        auth_spec["components"]["securitySchemes"]["OAuth2"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": "https://example.com/oauth/authorize",
                    "tokenUrl": "https://example.com/oauth/token",
                    "scopes": {"read:pets": "Read pets", "write:pets": "Write pets"}
                }
            }
        }
        
        with patch.object(self.generator.client_generator, 'generate_python_client') as mock_gen:
            mock_gen.return_value = GenerationResult(True, [], [], [])
            
            result = self.generator.generate(
                self.project_path,
                self.config,
                auth_spec
            )
            
            # Verify generator was called with auth configuration
            call_args = mock_gen.call_args
            assert call_args is not None
            
            # Check that authentication schemes are detected
            auth_schemes = self.generator._extract_auth_schemes(auth_spec)
            assert "ApiKeyAuth" in auth_schemes
            assert "BearerAuth" in auth_schemes
            assert "OAuth2" in auth_schemes
    
    def test_async_client_generation(self):
        """Test async client generation"""
        async_config = OpenAPIGeneratorConfig(
            client_type="asyncio",
            additional_properties={"asyncio": "true"}
        )
        
        with patch.object(self.generator.client_generator, 'generate_python_client') as mock_gen:
            mock_gen.return_value = GenerationResult(True, [], [], [])
            
            result = self.generator.generate_with_config(
                self.project_path,
                self.config,
                SAMPLE_OPENAPI_SPEC,
                async_config
            )
            
            # Verify async configuration was used
            call_args = mock_gen.call_args[0]
            config_arg = call_args[2]  # Third argument should be config
            assert config_arg.client_type == "asyncio"
            assert "asyncio" in config_arg.additional_properties
    
    def test_error_handling_missing_openapi_generator(self):
        """Test error handling when openapi-generator is not installed"""
        with patch.object(self.generator.client_generator, 'check_openapi_generator_installed') as mock_check:
            mock_check.return_value = False
            
            result = self.generator.generate(
                self.project_path,
                self.config,
                SAMPLE_OPENAPI_SPEC
            )
            
            assert result.success is False
            assert any("openapi-generator not found" in error for error in result.errors)
    
    def test_max_tools_limit(self):
        """Test that max_tools limit is respected"""
        # Create spec with many operations
        large_spec = SAMPLE_OPENAPI_SPEC.copy()
        large_spec["paths"] = {}
        
        # Add 60 operations
        for i in range(60):
            large_spec["paths"][f"/items/{i}"] = {
                "get": {
                    "operationId": f"getItem{i}",
                    "summary": f"Get item {i}",
                    "responses": {"200": {"description": "Success"}}
                }
            }
        
        with patch.object(self.generator, '_analyze_generated_client') as mock_analyze:
            # Mock 60 operations
            operations = [Mock(name=f"get_item_{i}") for i in range(60)]
            mock_analyze.return_value = ClientAnalysis(
                api_classes=[Mock(name="ItemsApi")],
                operations=operations,
                models=[]
            )
            
            result = self.generator.generate(
                self.project_path,
                self.config,
                large_spec,
                max_tools=30
            )
            
            # Verify warning about too many tools
            assert any("limiting to 30" in warning for warning in result.warnings)
    
    def test_include_examples_generation(self):
        """Test that examples are generated when requested"""
        with patch.object(self.generator, '_generate_examples') as mock_gen_examples:
            mock_gen_examples.return_value = GenerationResult(
                True, 
                ["examples/usage.py", "docs/examples.md"], 
                [], 
                []
            )
            
            result = self.generator.generate(
                self.project_path,
                self.config,
                SAMPLE_OPENAPI_SPEC,
                include_examples=True
            )
            
            mock_gen_examples.assert_called_once()
            assert any("examples" in file for file in result.files_created)
    
    def test_integration_with_existing_project_structure(self):
        """Test integration when adding to existing project structure"""
        # Create existing project structure
        existing_src = self.project_path / "src" / f"mcp_{self.config.service_name}"
        existing_src.mkdir(parents=True, exist_ok=True)
        (existing_src / "__init__.py").write_text("# Existing file")
        
        result = self.generator.generate(
            self.project_path,
            self.config,
            SAMPLE_OPENAPI_SPEC
        )
        
        # Verify existing files are preserved and new files are added
        assert (existing_src / "__init__.py").exists()
        init_content = (existing_src / "__init__.py").read_text()
        assert "# Existing file" in init_content