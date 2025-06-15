"""
Unit tests for OpenAPIEnhancedGenerator (Refactored)

Tests the new architecture where OpenAPIEnhancedGenerator uses:
1. OpenAPIClientGenerator to create client code
2. MCPToolMapper to generate MCPProjectConfig
3. MCPGenerator to generate the complete MCP project
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import tempfile
import json

from mcp_cli.generators import OpenAPIEnhancedGenerator, GenerationResult
from mcp_cli.openapi_client_generator import ClientAnalysis, Operation, ApiClass, Model
from mcp_cli.config import MCPProjectConfig, MCPIntegrationConfig
from mcp_cli.mcp_tool_mapper import MCPToolMapper


@pytest.fixture
def sample_openapi_data():
    """Sample OpenAPI specification data"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Pet Store API",
            "description": "A simple pet store API",
            "version": "1.0.0"
        },
        "servers": [
            {"url": "https://api.petstore.example.com"}
        ],
        "paths": {
            "/pets": {
                "get": {
                    "operationId": "listPets",
                    "summary": "List all pets",
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer"}
                        }
                    ]
                },
                "post": {
                    "operationId": "createPet",
                    "summary": "Create a pet"
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
    """Sample ClientAnalysis result"""
    operations = [
        Operation(
            name="list_pets",
            api_class="PetApi",
            method="GET",
            path="/pets",
            summary="List all pets"
        ),
        Operation(
            name="create_pet",
            api_class="PetApi",
            method="POST",
            path="/pets",
            summary="Create a pet"
        )
    ]
    
    return ClientAnalysis(
        client_package_name="petstore_client",
        api_classes=[ApiClass(name="PetApi", module="pet_api", methods=["list_pets", "create_pet"])],
        operations=operations,
        models=[Model(name="Pet", properties=["id", "name"])],
        base_url="https://api.petstore.example.com",
        auth_schemes=["ApiKeyAuth"]
    )


@pytest.fixture
def enhanced_generator():
    """Create OpenAPIEnhancedGenerator instance"""
    return OpenAPIEnhancedGenerator()


class TestOpenAPIEnhancedGeneratorRefactored:
    """Test the refactored OpenAPIEnhancedGenerator"""
    
    def test_generate_new_architecture(self, enhanced_generator, sample_openapi_data, sample_client_analysis):
        """Test the new architecture flow"""
        # Mock the client generator instance directly on the enhanced generator
        enhanced_generator.client_generator = Mock()
        
        # Mock client generation
        enhanced_generator.client_generator.generate_python_client.return_value = GenerationResult(
            success=True,
            files_created=["generated_client/api_client.py"],
            errors=[],
            warnings=[]
        )
        
        # Mock client analysis
        enhanced_generator.client_generator.parse_generated_client.return_value = sample_client_analysis
        enhanced_generator.client_generator.validate_generated_client.return_value = Mock(is_valid=True, errors=[])
        
        # Mock the MCP generator
        enhanced_generator.mcp_generator = Mock()
        enhanced_generator.mcp_generator.generate_from_openapi.return_value = GenerationResult(
            success=True,
            files_created=["project/server.py", "project/tools.py"],
            errors=[],
            warnings=[]
        )
        
        # Test the generation
        project_path = Path("/tmp/test-project")
        
        # Create a temporary MCPProjectConfig for input
        input_config = MCPProjectConfig(
            project_name="test-project",
            service_name="test_service", 
            description="Test description",
            author="Test Author"
        )
        
        result = enhanced_generator.generate(
            project_path=project_path,
            config=input_config,
            openapi_data=sample_openapi_data,
            include_examples=True,
            max_tools=50
        )
        
        # Verify the new architecture flow
        assert result.success
        
        # Verify OpenAPIClientGenerator was called
        enhanced_generator.client_generator.generate_python_client.assert_called_once()
        enhanced_generator.client_generator.parse_generated_client.assert_called_once()
        
        # Verify MCPGenerator was used
        enhanced_generator.mcp_generator.generate_from_openapi.assert_called_once()
    
    def test_client_generation_failure(self, enhanced_generator, sample_openapi_data):
        """Test handling of client generation failure"""
        # Mock the client generator to fail
        enhanced_generator.client_generator = Mock()
        enhanced_generator.client_generator.generate_python_client.return_value = GenerationResult(
            success=False,
            files_created=[],
            errors=["Client generation failed"],
            warnings=[]
        )
        
        # Test generation
        project_path = Path("/tmp/test-project")
        input_config = MCPProjectConfig(
            project_name="test-project",
            service_name="test_service",
            description="Test description", 
            author="Test Author"
        )
        
        result = enhanced_generator.generate(
            project_path=project_path,
            config=input_config,
            openapi_data=sample_openapi_data
        )
        
        # Should fail gracefully
        assert not result.success
        assert any("Client generation failed" in error for error in result.errors)
    
    def test_client_analysis_failure(self, enhanced_generator, sample_openapi_data):
        """Test handling of client analysis failure"""
        # Mock successful client generation but failed analysis
        enhanced_generator.client_generator = Mock()
        enhanced_generator.client_generator.generate_python_client.return_value = GenerationResult(
            success=True,
            files_created=["client.py"],
            errors=[],
            warnings=[]
        )
        
        enhanced_generator.client_generator.parse_generated_client.return_value = None  # Analysis fails
        
        # Test generation
        project_path = Path("/tmp/test-project") 
        input_config = MCPProjectConfig(
            project_name="test-project",
            service_name="test_service",
            description="Test description",
            author="Test Author"
        )
        
        result = enhanced_generator.generate(
            project_path=project_path,
            config=input_config,
            openapi_data=sample_openapi_data
        )
        
        # Should fail gracefully
        assert not result.success
        assert any("Failed to analyze generated client" in error for error in result.errors)
    
    def test_config_enhancement_from_analysis(self, enhanced_generator, sample_client_analysis):
        """Test that the generator can enhance config from client analysis"""
        # This tests the integration between MCPToolMapper and the generator
        from mcp_cli.mcp_tool_mapper import MCPToolMapper
        
        tool_mapper = MCPToolMapper(sample_client_analysis)
        
        enhanced_config = tool_mapper.generate_mcp_project_config(
            project_name="enhanced-project",
            author="Enhanced Author"
        )
        
        assert enhanced_config.project_name == "enhanced-project"
        assert enhanced_config.author == "Enhanced Author"
        assert enhanced_config.service_name == "enhanced_project"
        assert enhanced_config.openapi_config.package_name == "petstore_client"
        assert enhanced_config.mcp_config.max_tools >= 2  # We have 2 operations


class TestOpenAPIEnhancedGeneratorIntegration:
    """Integration tests for the new architecture"""
    
    def test_integration_with_real_tool_mapper(self, enhanced_generator, sample_client_analysis):
        """Test integration with real MCPToolMapper (not mocked)"""
        from mcp_cli.mcp_tool_mapper import MCPToolMapper
        
        # Create real tool mapper
        tool_mapper = MCPToolMapper(sample_client_analysis)
        
        # Test config generation
        config = tool_mapper.generate_mcp_project_config(
            project_name="integration-test",
            author="Integration Author",
            description="Integration test project"
        )
        
        # Verify config is properly generated
        assert isinstance(config, MCPProjectConfig)
        assert config.project_name == "integration-test"
        assert config.service_name == "integration_test"
        assert config.description == "Integration test project"
        assert config.openapi_config.package_name == "petstore_client"
        
        # Test tool definitions
        tool_definitions = tool_mapper.generate_tool_definitions()
        assert len(tool_definitions) == 2
        assert tool_definitions[0].name == "list_pets"
        assert tool_definitions[1].name == "create_pet"


if __name__ == "__main__":
    pytest.main([__file__]) 