# test_openapi_client_generator.py
"""
Quick test runner to validate our OpenAPIClientGenerator implementation
"""

import sys
import tempfile
import json
from pathlib import Path

# Add the current directory to Python path for imports
sys.path.insert(0, '.')

from mcp_cli.openapi_client_generator import OpenAPIClientGenerator, ClientAnalysis
from mcp_cli.config import OpenAPIGeneratorConfig, MCPIntegrationConfig, MCPProjectConfig
from mcp_cli.validators import ValidationResult, GenerationResult

# Sample OpenAPI spec for testing
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
            }
        }
    },
    "paths": {
        "/pets": {
            "get": {
                "operationId": "listPets",
                "summary": "List all pets",
                "responses": {
                    "200": {
                        "description": "A paged array of pets"
                    }
                }
            }
        }
    }
}

def test_basic_functionality():
    """Test basic functionality without openapi-generator"""
    print("🧪 Testing OpenAPIClientGenerator basic functionality...")
    
    generator = OpenAPIClientGenerator()
    
    # Test 1: Check openapi-generator availability
    print("  ✓ Testing openapi-generator availability check...")
    is_available = generator.check_openapi_generator_installed()
    print(f"    openapi-generator available: {is_available}")
    
    # Test 2: Configuration creation
    print("  ✓ Testing configuration creation...")
    
    sync_config = OpenAPIGeneratorConfig.for_sync_client("test_client")
    assert sync_config.client_type == "sync"
    assert sync_config.package_name == "test_client"
    print("    Sync config created successfully")
    
    async_config = OpenAPIGeneratorConfig.for_async_client("test_client")
    assert async_config.client_type == "asyncio"
    assert "asyncio" in async_config.additional_properties.get("library", "")
    print("    Async config created successfully")
    
    # Test 3: CLI args generation
    print("  ✓ Testing CLI args generation...")
    args = sync_config.to_cli_args()
    assert "--package-name" in args
    assert "test_client" in args
    print(f"    Generated args: {args}")
    
    print("✅ Basic functionality tests passed!")

def test_config_classes():
    """Test configuration classes"""
    print("🧪 Testing configuration classes...")
    
    # Test MCPIntegrationConfig
    print("  ✓ Testing MCPIntegrationConfig...")
    mcp_config = MCPIntegrationConfig()
    
    # Test tool naming
    tool_name = mcp_config.get_tool_name("listPets", "GET", "/pets")
    assert tool_name == "list_pets"
    print(f"    Tool name generation: {tool_name}")
    
    # Test operation filtering
    operation = {
        "method": "GET",
        "parameters": [{"name": "limit", "type": "integer"}],
        "deprecated": False
    }
    should_include = mcp_config.should_include_operation(operation)
    assert should_include is True
    print("    Operation filtering works")
    
    # Test MCPProjectConfig
    print("  ✓ Testing MCPProjectConfig...")
    project_config = MCPProjectConfig(
        project_name="test-project",
        service_name="test_service",
        description="Test project",
        author="Test Author"
    )
    
    output_path = project_config.get_output_path()
    assert "test-project" in str(output_path)
    print(f"    Output path: {output_path}")
    
    # Test serialization
    config_dict = project_config.to_dict()
    restored_config = MCPProjectConfig.from_dict(config_dict)
    assert restored_config.project_name == project_config.project_name
    print("    Serialization/deserialization works")
    
    print("✅ Configuration classes tests passed!")

def test_mock_client_analysis():
    """Test client analysis with mock data"""
    print("🧪 Testing mock client analysis...")
    
    generator = OpenAPIClientGenerator()
    
    # Create a temporary directory with mock generated client
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / "generated_client"
        api_dir = client_dir / "api"
        models_dir = client_dir / "models"
        
        # Create directory structure
        for directory in [client_dir, api_dir, models_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # Create mock files
        (client_dir / "__init__.py").touch()
        (client_dir / "api_client.py").touch()
        (client_dir / "configuration.py").write_text('''
class Configuration:
    def __init__(self):
        self.host = "https://petstore.example.com/api/v1"
''')
        
        # Create mock API file
        (api_dir / "__init__.py").touch()
        (api_dir / "pets_api.py").write_text('''
class PetsApi:
    def __init__(self, api_client=None):
        self.api_client = api_client
    
    def list_pets(self, limit=None):
        """List all pets"""
        pass
    
    def create_pet(self, pet):
        """Create a pet"""
        pass
''')
        
        # Create mock model file
        (models_dir / "__init__.py").touch()
        (models_dir / "pet.py").write_text('''
class Pet:
    def __init__(self, id=None, name=None, status=None):
        self.id = id
        self.name = name
        self.status = status
''')
        
        print("  ✓ Testing client parsing...")
        analysis = generator.parse_generated_client(client_dir)
        
        assert isinstance(analysis, ClientAnalysis)
        assert len(analysis.api_classes) >= 1
        assert analysis.api_classes[0].name == "PetsApi"
        assert len(analysis.operations) >= 2
        print(f"    Found {len(analysis.api_classes)} API classes")
        print(f"    Found {len(analysis.operations)} operations")
        print(f"    Found {len(analysis.models)} models")
        
        print("  ✓ Testing client validation...")
        validation = generator.validate_generated_client(client_dir)
        assert validation.is_valid is True
        print("    Client validation passed")
        
        # Test invalid client
        invalid_dir = Path(temp_dir) / "invalid_client"
        invalid_dir.mkdir()
        
        invalid_validation = generator.validate_generated_client(invalid_dir)
        assert invalid_validation.is_valid is False
        print("    Invalid client correctly detected")
    
    print("✅ Mock client analysis tests passed!")

def test_error_handling():
    """Test error handling scenarios"""
    print("🧪 Testing error handling...")
    
    generator = OpenAPIClientGenerator()
    
    # Test with non-existent spec
    with tempfile.TemporaryDirectory() as temp_dir:
        config = OpenAPIGeneratorConfig()
        
        # This should handle the case where openapi-generator is not available
        # or the spec is invalid gracefully
        result = generator.generate_python_client(
            "non-existent-spec.json",
            Path(temp_dir),
            config
        )
        
        # Should return a result object (success might be False if openapi-generator not installed)
        assert isinstance(result, GenerationResult)
        print(f"    Generation result: success={result.success}")
        if not result.success:
            print(f"    Expected error: {result.errors}")
    
    print("✅ Error handling tests passed!")

def main():
    """Run all tests"""
    print("🚀 Testing OpenAPIClientGenerator Implementation")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        print()
        
        test_config_classes()
        print()
        
        test_mock_client_analysis()
        print()
        
        test_error_handling()
        print()
        
        print("🎉 All tests passed! OpenAPIClientGenerator implementation is working.")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())