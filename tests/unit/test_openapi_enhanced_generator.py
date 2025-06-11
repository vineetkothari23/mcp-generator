"""
Tests for OpenAPIEnhancedGenerator

Tests the enhanced OpenAPI generator that uses openapi-generator
to create API clients and integrates them with MCP servers.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mcp_cli.generators import OpenAPIEnhancedGenerator
from mcp_cli.config import MCPProjectConfig, OpenAPIGeneratorConfig
from mcp_cli.openapi_client_generator import ClientAnalysis, ApiClass, Operation, Model


@pytest.fixture
def sample_openapi_spec():
    """Sample OpenAPI specification for testing"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store API",
            "version": "1.0.0",
            "description": "A simple pet store API"
        },
        "servers": [
            {"url": "https://api.petstore.com/v1"}
        ],
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "summary": "List all pets",
                    "responses": {
                        "200": {
                            "description": "A list of pets"
                        }
                    }
                },
                "post": {
                    "operationId": "createPet",
                    "summary": "Create a pet",
                    "responses": {
                        "201": {
                            "description": "Pet created"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Pet": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                }
            }
        }
    }


@pytest.fixture
def sample_client_analysis():
    """Sample ClientAnalysis for testing"""
    return ClientAnalysis(
        api_classes=[
            ApiClass(
                name="PetsApi",
                module="pets_api",
                methods=["list_pets", "create_pet"]
            )
        ],
        operations=[
            Operation(
                name="listPets",
                api_class="PetsApi",
                method="GET",
                path="/pets",
                summary="List all pets"
            ),
            Operation(
                name="createPet",
                api_class="PetsApi",
                method="POST",
                path="/pets",
                summary="Create a pet"
            )
        ],
        models=[
            Model(
                name="Pet",
                properties=["id", "name"]
            )
        ],
        client_package_name="pet_store_client",
        base_url="https://api.petstore.com/v1"
    )


@pytest.fixture
def sample_config():
    """Sample MCPProjectConfig for testing"""
    return MCPProjectConfig(
        project_name="pet-store-mcp",
        service_name="pet_store",
        description="MCP server for Pet Store API",
        author="Test Author",
        openapi_config=OpenAPIGeneratorConfig(
            package_name="pet_store_client"
        )
    )


class TestOpenAPIEnhancedGenerator:
    """Test cases for OpenAPIEnhancedGenerator"""
    
    def test_init(self):
        """Test generator initialization"""
        generator = OpenAPIEnhancedGenerator()
        
        assert generator.client_generator is not None
        assert generator.tool_mapper is None
        assert hasattr(generator, 'render_template')
    
    @patch('mcp_cli.generators.OpenAPIClientGenerator')
    def test_generate_api_client_success(self, mock_client_gen_class, sample_config, sample_openapi_spec, tmp_path):
        """Test successful API client generation"""
        # Setup mocks
        mock_client_gen = Mock()
        mock_client_gen_class.return_value = mock_client_gen
        mock_client_gen.generate_python_client.return_value = Mock(
            success=True,
            files_created=["client.py", "models.py"],
            errors=[],
            warnings=[]
        )
        
        generator = OpenAPIEnhancedGenerator()
        generator.client_generator = mock_client_gen
        
        # Test
        result = generator._generate_api_client(tmp_path, sample_config, sample_openapi_spec)
        
        # Assertions
        assert result.success is True
        assert len(result.files_created) == 2
        assert len(result.errors) == 0
        mock_client_gen.generate_python_client.assert_called_once()
    
    @patch('mcp_cli.generators.OpenAPIClientGenerator')
    def test_generate_api_client_failure(self, mock_client_gen_class, sample_config, sample_openapi_spec, tmp_path):
        """Test API client generation failure"""
        # Setup mocks
        mock_client_gen = Mock()
        mock_client_gen_class.return_value = mock_client_gen
        mock_client_gen.generate_python_client.return_value = Mock(
            success=False,
            files_created=[],
            errors=["Generation failed"],
            warnings=[]
        )
        
        generator = OpenAPIEnhancedGenerator()
        generator.client_generator = mock_client_gen
        
        # Test
        result = generator._generate_api_client(tmp_path, sample_config, sample_openapi_spec)
        
        # Assertions
        assert result.success is False
        assert len(result.errors) == 1
        assert "Generation failed" in result.errors
    
    @patch('mcp_cli.generators.OpenAPIClientGenerator')
    def test_analyze_generated_client_success(self, mock_client_gen_class, sample_config, sample_client_analysis, tmp_path):
        """Test successful client analysis"""
        # Setup mocks
        mock_client_gen = Mock()
        mock_client_gen_class.return_value = mock_client_gen
        mock_client_gen.parse_generated_client.return_value = sample_client_analysis
        mock_client_gen.validate_generated_client.return_value = Mock(
            is_valid=True,
            errors=[],
            warnings=[]
        )
        
        generator = OpenAPIEnhancedGenerator()
        generator.client_generator = mock_client_gen
        
        # Test
        result = generator._analyze_generated_client(tmp_path, sample_config)
        
        # Assertions
        assert result is not None
        assert result.client_package_name == "pet_store_client"
        assert len(result.operations) == 2
        mock_client_gen.parse_generated_client.assert_called_once()
        mock_client_gen.validate_generated_client.assert_called_once()
    
    @patch('mcp_cli.generators.MCPToolMapper')
    def test_generate_mcp_tools_success(self, mock_mapper_class, sample_config, sample_client_analysis, tmp_path):
        """Test successful MCP tools generation"""
        # Setup mocks
        mock_mapper = Mock()
        mock_mapper_class.return_value = mock_mapper = Mock()
        mock_mapper.generate_tool_definitions.return_value = [
            Mock(name="list_pets", description="List all pets"),
            Mock(name="create_pet", description="Create a pet")
        ]
        
        generator = OpenAPIEnhancedGenerator()
        
        # Mock template rendering
        generator.render_template = Mock(return_value="# Generated tools code")
        generator.write_file = Mock()
        
        # Test
        result = generator._generate_mcp_tools(tmp_path, sample_config, sample_client_analysis, max_tools=50)
        
        # Assertions
        assert result.success is True
        assert len(result.files_created) == 1
        generator.render_template.assert_called_once()
        generator.write_file.assert_called_once()
    
    def test_generate_mcp_tools_max_tools_limit(self, sample_config, sample_client_analysis, tmp_path):
        """Test MCP tools generation with max_tools limit"""
        # Create more operations than max_tools
        many_operations = [
            Operation(name=f"operation_{i}", api_class="TestApi", method="GET", path=f"/test/{i}")
            for i in range(10)
        ]
        sample_client_analysis.operations = many_operations
        
        with patch('mcp_cli.generators.MCPToolMapper') as mock_mapper_class:
            mock_mapper = Mock()
            mock_mapper_class.return_value = mock_mapper
            mock_mapper.generate_tool_definitions.return_value = [
                Mock(name=f"operation_{i}") for i in range(10)
            ]
            
            generator = OpenAPIEnhancedGenerator()
            generator.render_template = Mock(return_value="# Generated tools code")
            generator.write_file = Mock()
            
            # Test with max_tools=5
            result = generator._generate_mcp_tools(tmp_path, sample_config, sample_client_analysis, max_tools=5)
            
            # Should limit to 5 tools
            assert result.success is True
            # Verify the template was called with limited tools
            call_args = generator.render_template.call_args
            template_context = call_args[0][1]  # Second argument is the context dict
            assert len(template_context['tool_definitions']) == 5
    
    def test_generate_mcp_server_success(self, sample_config, sample_client_analysis, tmp_path):
        """Test successful MCP server generation"""
        generator = OpenAPIEnhancedGenerator()
        
        # Mock template rendering
        generator.render_template = Mock(side_effect=["# Server code", "# Init code"])
        generator.write_file = Mock()
        
        # Test
        result = generator._generate_mcp_server(tmp_path, sample_config, sample_client_analysis)
        
        # Assertions
        assert result.success is True
        assert len(result.files_created) == 2
        assert generator.render_template.call_count == 2
        assert generator.write_file.call_count == 2
    
    def test_generate_documentation_success(self, sample_config, sample_client_analysis, tmp_path):
        """Test successful documentation generation"""
        generator = OpenAPIEnhancedGenerator()
        
        # Mock template rendering
        generator.render_template = Mock(side_effect=["# API docs", "# Usage examples"])
        generator.write_file = Mock()
        
        # Test with examples
        result = generator._generate_documentation(tmp_path, sample_config, sample_client_analysis, include_examples=True)
        
        # Assertions
        assert result.success is True
        assert len(result.files_created) == 2
        assert generator.render_template.call_count == 2
        assert generator.write_file.call_count == 2
    
    def test_generate_documentation_no_examples(self, sample_config, sample_client_analysis, tmp_path):
        """Test documentation generation without examples"""
        generator = OpenAPIEnhancedGenerator()
        
        # Mock template rendering
        generator.render_template = Mock(return_value="# API docs")
        generator.write_file = Mock()
        
        # Test without examples
        result = generator._generate_documentation(tmp_path, sample_config, sample_client_analysis, include_examples=False)
        
        # Assertions
        assert result.success is True
        assert len(result.files_created) == 1
        assert generator.render_template.call_count == 1
        assert generator.write_file.call_count == 1
    
    @patch('mcp_cli.generators.OpenAPIClientGenerator')
    @patch('mcp_cli.generators.MCPToolMapper')
    def test_full_generate_success(self, mock_mapper_class, mock_client_gen_class, 
                                  sample_config, sample_openapi_spec, sample_client_analysis, tmp_path):
        """Test full generation process success"""
        # Setup mocks
        mock_client_gen = Mock()
        mock_client_gen_class.return_value = mock_client_gen
        mock_client_gen.generate_python_client.return_value = Mock(
            success=True, files_created=["client.py"], errors=[], warnings=[]
        )
        mock_client_gen.parse_generated_client.return_value = sample_client_analysis
        mock_client_gen.validate_generated_client.return_value = Mock(
            is_valid=True, errors=[], warnings=[]
        )
        
        mock_mapper = Mock()
        mock_mapper_class.return_value = mock_mapper
        mock_mapper.generate_tool_definitions.return_value = [Mock(name="test_tool")]
        
        generator = OpenAPIEnhancedGenerator()
        generator.client_generator = mock_client_gen
        generator.render_template = Mock(return_value="# Generated code")
        generator.write_file = Mock()
        
        # Test
        result = generator.generate(tmp_path, sample_config, sample_openapi_spec, 
                                  include_examples=True, max_tools=50)
        
        # Assertions
        assert result.success is True
        assert len(result.files_created) > 0
        assert len(result.errors) == 0
    
    @patch('mcp_cli.generators.OpenAPIClientGenerator')
    def test_full_generate_client_failure(self, mock_client_gen_class, 
                                         sample_config, sample_openapi_spec, tmp_path):
        """Test full generation process with client generation failure"""
        # Setup mocks
        mock_client_gen = Mock()
        mock_client_gen_class.return_value = mock_client_gen
        mock_client_gen.generate_python_client.return_value = Mock(
            success=False, files_created=[], errors=["Client generation failed"], warnings=[]
        )
        
        generator = OpenAPIEnhancedGenerator()
        generator.client_generator = mock_client_gen
        
        # Test
        result = generator.generate(tmp_path, sample_config, sample_openapi_spec)
        
        # Assertions
        assert result.success is False
        assert "API client generation failed - cannot proceed" in result.errors
    
    def test_combine_results(self):
        """Test combining multiple generation results"""
        from mcp_cli.generators import GenerationResult
        
        generator = OpenAPIEnhancedGenerator()
        
        results = [
            GenerationResult(True, ["file1.py"], [], ["warning1"]),
            GenerationResult(True, ["file2.py"], [], []),
            GenerationResult(False, [], ["error1"], ["warning2"])
        ]
        
        combined = generator._combine_results(results)
        
        assert combined.success is False  # One result failed
        assert len(combined.files_created) == 2
        assert len(combined.errors) == 1
        assert len(combined.warnings) == 2 