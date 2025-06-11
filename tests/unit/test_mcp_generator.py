"""
Tests for the MCPGenerator class.

This module contains tests for:
- MCP project generation orchestration
- Configuration validation
- Error aggregation from multiple generators
- Generation phase coordination
- Project summary generation
- Overall success/failure determination
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from dataclasses import dataclass
from typing import List

from mcp_cli.generators import MCPGenerator, GenerationResult
from mcp_cli.config import MCPProjectConfig


@dataclass
class MockConfig:
    """Mock configuration for testing"""
    project_name: str = "test-project"
    service_name: str = "test_service"
    description: str = "Test project description"
    author: str = "Test Author"
    version: str = "1.0.0"
    python_version: str = "3.11"
    include_docker: bool = True
    include_ci: bool = True
    test_framework: str = "pytest"
    openapi_spec: str = None
    output_dir: str = "."


class TestMCPGenerator:
    """Test cases for MCPGenerator class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = MCPGenerator()
        self.config = MockConfig()
        self.project_path = Path("/test/project")
        
        # Mock successful result
        self.success_result = GenerationResult(
            success=True,
            files_created=["file1.py", "file2.py"],
            errors=[],
            warnings=[]
        )
        
        # Mock failure result
        self.failure_result = GenerationResult(
            success=False,
            files_created=["partial_file.py"],
            errors=["Generation failed"],
            warnings=["Warning message"]
        )
    
    def test_initialization(self):
        """Test MCPGenerator initialization"""
        generator = MCPGenerator()
        
        # Check that all component generators are initialized
        assert hasattr(generator, 'structure_generator')
        assert hasattr(generator, 'test_generator')
        assert hasattr(generator, 'config_generator')
        assert hasattr(generator, 'docker_generator')
        
        # Check template environment is set up
        assert generator.env is not None
        assert 'snake_case' in generator.env.filters
        assert 'pascal_case' in generator.env.filters
        assert 'kebab_case' in generator.env.filters
    
    def test_successful_generation_all_components(self):
        """Test successful generation of all components"""
        # Mock the component generators directly on the instance
        with patch.object(self.generator, 'structure_generator') as mock_structure, \
             patch.object(self.generator, 'config_generator') as mock_config, \
             patch.object(self.generator, 'test_generator') as mock_test, \
             patch.object(self.generator, 'docker_generator') as mock_docker, \
             patch.object(self.generator, '_generate_project_summary'):
            
            # Setup mocks to return success
            mock_structure.generate.return_value = self.success_result
            mock_config.generate.return_value = self.success_result
            mock_test.generate.return_value = self.success_result
            mock_docker.generate.return_value = self.success_result
            
            result = self.generator.generate(self.project_path, self.config)
        
        # Verify result
        assert result.success is True
        assert len(result.files_created) == 8  # 2 files from each of 4 generators
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        
        # Verify all generators were called
        mock_structure.generate.assert_called_once_with(self.project_path, self.config)
        mock_config.generate.assert_called_once_with(self.project_path, self.config)
        mock_test.generate.assert_called_once_with(self.project_path, self.config)
        mock_docker.generate.assert_called_once_with(self.project_path, self.config)
    
    def test_generation_without_docker(self):
        """Test generation when Docker is disabled"""
        # Set Docker to disabled
        self.config.include_docker = False
        
        # Mock the component generators directly on the instance
        with patch.object(self.generator, 'structure_generator') as mock_structure, \
             patch.object(self.generator, 'config_generator') as mock_config, \
             patch.object(self.generator, 'test_generator') as mock_test, \
             patch.object(self.generator, 'docker_generator') as mock_docker, \
             patch.object(self.generator, '_generate_project_summary'):
            
            # Setup mocks to return success
            mock_structure.generate.return_value = self.success_result
            mock_config.generate.return_value = self.success_result
            mock_test.generate.return_value = self.success_result
            mock_docker.generate.return_value = self.success_result
            
            result = self.generator.generate(self.project_path, self.config)
        
        # Verify Docker generator was not called since include_docker=False
        mock_docker.generate.assert_not_called()
        
        # Verify result is still successful
        assert result.success is True
        assert len(result.files_created) == 6  # 2 files from each of 3 generators
    
    def test_partial_failure_handling(self):
        """Test handling when some generators fail"""
        # Mock the component generators directly on the instance
        with patch.object(self.generator, 'structure_generator') as mock_structure, \
             patch.object(self.generator, 'config_generator') as mock_config, \
             patch.object(self.generator, 'test_generator') as mock_test, \
             patch.object(self.generator, 'docker_generator') as mock_docker, \
             patch.object(self.generator, '_generate_project_summary'):
            
            # Structure succeeds, config fails, test succeeds, docker succeeds
            mock_structure.generate.return_value = self.success_result
            mock_config.generate.return_value = self.failure_result
            mock_test.generate.return_value = self.success_result
            mock_docker.generate.return_value = self.success_result
            
            result = self.generator.generate(self.project_path, self.config)
        
        # Verify overall failure due to critical component failure
        assert result.success is False
        assert "One or more critical components failed to generate" in result.errors
        assert "Configuration generation failed, continuing with other components" in result.warnings
        
        # Verify files from successful generators are included
        assert len(result.files_created) == 7  # 2+1+2+2 files from generators
        assert "Generation failed" in result.errors
        assert "Warning message" in result.warnings
    
    def test_docker_failure_non_critical(self):
        """Test that Docker failure doesn't cause overall failure"""
        # Mock the component generators directly on the instance
        with patch.object(self.generator, 'structure_generator') as mock_structure, \
             patch.object(self.generator, 'config_generator') as mock_config, \
             patch.object(self.generator, 'test_generator') as mock_test, \
             patch.object(self.generator, 'docker_generator') as mock_docker, \
             patch.object(self.generator, '_generate_project_summary'):
            
            # All critical components succeed, Docker fails
            mock_structure.generate.return_value = self.success_result
            mock_config.generate.return_value = self.success_result
            mock_test.generate.return_value = self.success_result
            mock_docker.generate.return_value = self.failure_result
            
            result = self.generator.generate(self.project_path, self.config)
        
        # Verify overall success despite Docker failure
        assert result.success is True
        assert "Docker generation failed" in result.warnings
        assert len(result.files_created) == 7  # 2+2+2+1 files
    
    def test_configuration_validation_success(self):
        """Test successful configuration validation"""
        errors = self.generator.validate_config(self.config)
        assert len(errors) == 0
    
    def test_configuration_validation_missing_required_fields(self):
        """Test configuration validation with missing required fields"""
        # Test missing project name
        config = MockConfig()
        config.project_name = ""
        errors = self.generator.validate_config(config)
        assert "Project name is required" in errors
        
        # Test missing service name
        config = MockConfig()
        config.service_name = ""
        errors = self.generator.validate_config(config)
        assert "Service name is required" in errors
        
        # Test missing description
        config = MockConfig()
        config.description = ""
        errors = self.generator.validate_config(config)
        assert "Project description is required" in errors
        
        # Test missing author
        config = MockConfig()
        config.author = ""
        errors = self.generator.validate_config(config)
        assert "Author is required" in errors
    
    def test_configuration_validation_invalid_formats(self):
        """Test configuration validation with invalid formats"""
        # Test invalid project name
        config = MockConfig()
        config.project_name = "invalid@name!"
        errors = self.generator.validate_config(config)
        assert "Project name can only contain letters, numbers, hyphens, and underscores" in errors
        
        # Test invalid service name (starts with number)
        config = MockConfig()
        config.service_name = "123invalid"
        errors = self.generator.validate_config(config)
        assert "Service name must be a valid Python identifier" in errors
        
        # Test invalid Python version
        config = MockConfig()
        config.python_version = "invalid_version"
        errors = self.generator.validate_config(config)
        assert "Python version must be in format 'X.Y' (e.g., '3.11')" in errors
    
    def test_get_generation_order(self):
        """Test generation order information"""
        order = self.generator.get_generation_order()
        
        expected_order = [
            "Project Structure",
            "Configuration Files", 
            "Test Framework",
            "Docker Setup (optional)",
            "Project Summary"
        ]
        
        assert order == expected_order
    
    @patch('mcp_cli.generators.MCPGenerator.render_template')
    @patch('mcp_cli.generators.MCPGenerator.write_file')
    def test_project_summary_generation(self, mock_write, mock_render):
        """Test project summary generation"""
        mock_render.return_value = "# Project Summary\nTest content"
        files_created = ["file1.py", "file2.py", "file3.py"]
        original_count = len(files_created)
        
        self.generator._generate_project_summary(self.project_path, self.config, files_created)
        
        # Verify template was rendered - check the call args
        assert mock_render.call_count == 1
        call_args = mock_render.call_args
        assert call_args[0][0] == "project/PROJECT_SUMMARY.md.j2"
        
        # Check the context dict passed to template
        context = call_args[0][1]
        assert context["project_name"] == self.config.project_name
        assert context["service_name"] == self.config.service_name
        assert context["description"] == self.config.description
        assert context["author"] == self.config.author
        assert context["version"] == self.config.version
        assert context["python_version"] == self.config.python_version
        assert context["test_framework"] == self.config.test_framework
        assert context["include_docker"] == self.config.include_docker
        assert context["include_ci"] == self.config.include_ci
        assert context["file_count"] == original_count  # Should be count before summary file added
        
        # Verify file was written
        expected_path = self.project_path / "PROJECT_SUMMARY.md"
        mock_write.assert_called_once_with(expected_path, "# Project Summary\nTest content")
        
        # Verify the summary file was added to the files_created list after rendering
        assert str(expected_path) in files_created
        assert len(files_created) == original_count + 1
    
    def test_project_summary_generation_error_handling(self):
        """Test that summary generation errors don't fail the entire process"""
        files_created = ["file1.py"]
        
        # Mock template rendering to raise an exception
        with patch.object(self.generator, 'render_template', side_effect=Exception("Template error")):
            # This should not raise an exception
            self.generator._generate_project_summary(self.project_path, self.config, files_created)
            # If we reach here, the error was handled gracefully
    
    def test_component_generator_exception_handling(self):
        """Test handling of exceptions from component generators"""
        # Mock structure generator to raise an exception
        with patch.object(self.generator, 'structure_generator') as mock_structure:
            mock_structure.generate.side_effect = Exception("Structure generation error")
            
            result = self.generator._generate_project_structure(self.project_path, self.config)
        
        assert result.success is False
        assert "Project structure generation failed: Structure generation error" in result.errors
        assert len(result.files_created) == 0
        assert len(result.warnings) == 0
    
    def test_overall_exception_handling(self):
        """Test handling of unexpected exceptions in main generate method"""
        # Make the structure generator raise an exception during generation
        with patch.object(self.generator, 'structure_generator') as mock_structure:
            mock_structure.generate.side_effect = Exception("Unexpected error")
            
            result = self.generator.generate(self.project_path, self.config)
            
            assert result.success is False
            # The error could be either the specific generator error or the overall error
            error_messages = str(result.errors)
            assert ("Project structure generation failed: Unexpected error" in error_messages or 
                    "Failed to generate MCP project" in error_messages)


class TestMCPGeneratorIntegration:
    """Integration-style tests for MCPGenerator (without mocking component generators)"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.generator = MCPGenerator()
        self.config = MockConfig()
        
    def test_validate_config_comprehensive(self):
        """Test comprehensive configuration validation scenarios"""
        # Test all valid
        valid_config = MockConfig()
        errors = self.generator.validate_config(valid_config)
        assert len(errors) == 0
        
        # Test multiple errors
        invalid_config = MockConfig()
        invalid_config.project_name = ""
        invalid_config.service_name = "123invalid"
        invalid_config.python_version = "invalid"
        
        errors = self.generator.validate_config(invalid_config)
        assert len(errors) == 3
        assert any("Project name is required" in error for error in errors)
        assert any("Service name must be a valid Python identifier" in error for error in errors)
        assert any("Python version must be in format" in error for error in errors)
    
    def test_generation_order_completeness(self):
        """Test that generation order covers all expected phases"""
        order = self.generator.get_generation_order()
        
        # Verify all expected phases are present
        assert "Project Structure" in order
        assert "Configuration Files" in order
        assert "Test Framework" in order
        assert "Docker Setup (optional)" in order
        assert "Project Summary" in order
        
        # Verify reasonable order (structure should be first)
        assert order[0] == "Project Structure"
        assert order[-1] == "Project Summary"
    
    def test_generated_project_basic_functionality(self):
        """Test that generated project has basic working functionality"""
        import tempfile
        import sys
        from pathlib import Path
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / self.config.project_name
            
            # Generate the project
            result = self.generator.generate(project_path, self.config)
            assert result.success is True
            
            # Add the generated project to Python path temporarily
            src_path = project_path / "src"
            sys.path.insert(0, str(src_path))
            
            try:
                # Test that we can import the generated module
                module_name = f"mcp_{self.config.service_name}"
                
                # Import the main module
                import importlib
                main_module = importlib.import_module(module_name)
                assert main_module is not None
                
                # Import and instantiate the server
                server_module = importlib.import_module(f"{module_name}.server")
                assert hasattr(server_module, 'MCPServer')
                
                # Import the config module
                config_module = importlib.import_module(f"{module_name}.config")
                assert hasattr(config_module, 'Config')
                
                # Import the tools module
                tools_module = importlib.import_module(f"{module_name}.tools")
                assert hasattr(tools_module, 'MCPTools')
                
            finally:
                # Clean up Python path
                sys.path.remove(str(src_path))
                
                # Remove imported modules from cache
                modules_to_remove = [
                    name for name in sys.modules.keys() 
                    if name.startswith(f"mcp_{self.config.service_name}")
                ]
                for module_name in modules_to_remove:
                    del sys.modules[module_name] 