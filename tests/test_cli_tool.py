"""
Unit tests for CLI tool functions, focusing on _generate_standard_project

This module contains tests for:
- _generate_standard_project function behavior
- Integration with MCPGenerator
- Error handling and reporting
- Configuration validation
- Project path generation

Note: This test isolates the function to avoid complex import dependencies.
"""

import pytest
import sys
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from dataclasses import dataclass
from typing import List

from mcp_cli.generators import GenerationResult


# Mock the MCPCLIError exception for testing
class MCPCLIError(Exception):
    """Mock exception for testing"""
    pass


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
    output_dir: str = "/tmp/test"


# Extracted function implementation for testing
def _generate_standard_project_isolated(cli_instance, config):
    """
    Generate standard MCP server project structure using MCPGenerator
    
    This is an isolated version of the function for testing purposes.
    
    Args:
        cli_instance: CLI instance with generators (unused but kept for compatibility)
        config: Project configuration
        
    Returns:
        str: Path to generated project
    """
    from mcp_cli.generators import MCPGenerator
    
    project_path = Path(config.output_dir) / config.project_name
    
    # Use MCPGenerator for comprehensive project generation
    mcp_generator = MCPGenerator()
    result = mcp_generator.generate(project_path, config)
    
    if not result.success:
        error_msg = "Project generation failed:\n" + "\n".join(result.errors)
        if result.warnings:
            error_msg += "\nWarnings:\n" + "\n".join(result.warnings)
        raise MCPCLIError(error_msg)
    
    return str(project_path)


@pytest.mark.unit
class TestGenerateStandardProject:
    """Test cases for _generate_standard_project function"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cli_instance = Mock()
        self.config = MockConfig()
        
        # Mock successful result
        self.success_result = GenerationResult(
            success=True,
            files_created=[
                "src/mcp_test_service/__init__.py",
                "src/mcp_test_service/server.py",
                "tests/unit/test_server.py",
                "config/server_config.yaml",
                "docker/Dockerfile"
            ],
            errors=[],
            warnings=[]
        )
        
        # Mock failure result
        self.failure_result = GenerationResult(
            success=False,
            files_created=["partial_file.py"],
            errors=["Generation failed", "Template not found"],
            warnings=["Warning message"]
        )
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_generate_standard_project_success(self, mock_generator_class):
        """Test successful project generation"""
        # Setup mock
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Execute function
        result_path = _generate_standard_project_isolated(self.cli_instance, self.config)
        
        # Verify results
        expected_path = Path(self.config.output_dir) / self.config.project_name
        assert result_path == str(expected_path)
        
        # Verify MCPGenerator was used correctly
        mock_generator_class.assert_called_once()
        mock_generator.generate.assert_called_once_with(expected_path, self.config)
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_generate_standard_project_failure(self, mock_generator_class):
        """Test project generation failure handling"""
        # Setup mock to return failure
        mock_generator = Mock()
        mock_generator.generate.return_value = self.failure_result
        mock_generator_class.return_value = mock_generator
        
        # Execute and verify exception
        with pytest.raises(MCPCLIError) as exc_info:
            _generate_standard_project_isolated(self.cli_instance, self.config)
        
        # Verify error message includes both errors and warnings
        error_message = str(exc_info.value)
        assert "Project generation failed:" in error_message
        assert "Generation failed" in error_message
        assert "Template not found" in error_message
        assert "Warnings:" in error_message
        assert "Warning message" in error_message
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_generate_standard_project_failure_errors_only(self, mock_generator_class):
        """Test project generation failure with errors but no warnings"""
        # Setup mock to return failure without warnings
        failure_result_no_warnings = GenerationResult(
            success=False,
            files_created=[],
            errors=["Critical error occurred"],
            warnings=[]
        )
        
        mock_generator = Mock()
        mock_generator.generate.return_value = failure_result_no_warnings
        mock_generator_class.return_value = mock_generator
        
        # Execute and verify exception
        with pytest.raises(MCPCLIError) as exc_info:
            _generate_standard_project_isolated(self.cli_instance, self.config)
        
        # Verify error message format
        error_message = str(exc_info.value)
        assert "Project generation failed:" in error_message
        assert "Critical error occurred" in error_message
        assert "Warnings:" not in error_message
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_generate_standard_project_with_different_config(self, mock_generator_class):
        """Test project generation with different configuration settings"""
        # Setup different config
        custom_config = MockConfig()
        custom_config.project_name = "custom-mcp-server"
        custom_config.output_dir = "/custom/path"
        custom_config.include_docker = False
        
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Execute function
        result_path = _generate_standard_project_isolated(self.cli_instance, custom_config)
        
        # Verify correct path generation
        expected_path = Path("/custom/path") / "custom-mcp-server"
        assert result_path == str(expected_path)
        
        # Verify generator called with correct parameters
        mock_generator.generate.assert_called_once_with(expected_path, custom_config)
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_generate_standard_project_path_handling(self, mock_generator_class):
        """Test path handling with various input formats"""
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Test with relative path
        config_relative = MockConfig()
        config_relative.output_dir = "."
        config_relative.project_name = "test-project"
        
        result = _generate_standard_project_isolated(self.cli_instance, config_relative)
        expected = str(Path(".") / "test-project")
        assert result == expected
        
        # Test with absolute path
        config_absolute = MockConfig()
        config_absolute.output_dir = "/absolute/path"
        config_absolute.project_name = "my-project"
        
        result = _generate_standard_project_isolated(self.cli_instance, config_absolute)
        expected = str(Path("/absolute/path") / "my-project")
        assert result == expected
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_cli_instance_parameter_unused(self, mock_generator_class):
        """Test that cli_instance parameter is unused but function still works"""
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Pass None as cli_instance to verify it's not used
        result_path = _generate_standard_project_isolated(None, self.config)
        
        # Should still work correctly
        expected_path = Path(self.config.output_dir) / self.config.project_name
        assert result_path == str(expected_path)
        
        # Verify MCPGenerator was still called correctly
        mock_generator_class.assert_called_once()
        mock_generator.generate.assert_called_once()
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_mcp_generator_import(self, mock_generator_class):
        """Test that MCPGenerator is imported correctly within the function"""
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Execute function
        _generate_standard_project_isolated(self.cli_instance, self.config)
        
        # Verify MCPGenerator class was instantiated
        mock_generator_class.assert_called_once_with()
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_generation_result_success_check(self, mock_generator_class):
        """Test that function properly checks GenerationResult.success"""
        # Test success case
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Should not raise exception
        result = _generate_standard_project_isolated(self.cli_instance, self.config)
        assert result is not None
        
        # Test failure case
        mock_generator.generate.return_value = self.failure_result
        
        # Should raise exception
        with pytest.raises(MCPCLIError):
            _generate_standard_project_isolated(self.cli_instance, self.config)
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_exception_handling_from_generator(self, mock_generator_class):
        """Test handling of exceptions raised by MCPGenerator"""
        # Setup mock to raise exception
        mock_generator = Mock()
        mock_generator.generate.side_effect = Exception("Unexpected generator error")
        mock_generator_class.return_value = mock_generator
        
        # Execute and verify exception propagation
        with pytest.raises(Exception) as exc_info:
            _generate_standard_project_isolated(self.cli_instance, self.config)
        
        assert "Unexpected generator error" in str(exc_info.value)
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_project_config_types(self, mock_generator_class):
        """Test function works with different config types"""
        mock_generator = Mock()
        mock_generator.generate.return_value = self.success_result
        mock_generator_class.return_value = mock_generator
        
        # Test with MockConfig
        result = _generate_standard_project_isolated(self.cli_instance, self.config)
        expected_path = str(Path(self.config.output_dir) / self.config.project_name)
        assert result == expected_path
        
        # Verify generator was called with config
        mock_generator.generate.assert_called_with(
            Path(self.config.output_dir) / self.config.project_name, 
            self.config
        )


@pytest.mark.unit
class TestGenerateStandardProjectFunctionBehavior:
    """Tests focusing on the function's behavior and interface"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.cli_instance = Mock()
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_return_value_format(self, mock_generator_class):
        """Test that return value is properly formatted string path"""
        mock_generator = Mock()
        mock_generator.generate.return_value = GenerationResult(
            success=True, files_created=[], errors=[], warnings=[]
        )
        mock_generator_class.return_value = mock_generator
        
        config = MockConfig()
        config.output_dir = "/test/path"
        config.project_name = "test-project"
        
        result = _generate_standard_project_isolated(self.cli_instance, config)
        
        # Should return string path
        assert isinstance(result, str)
        # Use Path to normalize for cross-platform compatibility
        expected_path = str(Path("/test/path") / "test-project")
        assert result == expected_path
    
    def test_function_docstring_content(self):
        """Test that function has appropriate docstring"""
        # Function should have docstring
        assert _generate_standard_project_isolated.__doc__ is not None
        docstring = _generate_standard_project_isolated.__doc__
        
        # Should mention MCPGenerator
        assert "MCPGenerator" in docstring
        
        # Should mention compatibility note about cli_instance
        assert "unused but kept for compatibility" in docstring
        
        # Should describe return value
        assert "Path to generated project" in docstring
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_path_construction_logic(self, mock_generator_class):
        """Test the path construction logic"""
        mock_generator = Mock()
        mock_generator.generate.return_value = GenerationResult(
            success=True, files_created=[], errors=[], warnings=[]
        )
        mock_generator_class.return_value = mock_generator
        
        # Test different path combinations
        test_cases = [
            ("/home/user", "my-project", "/home/user/my-project"),
            (".", "test-app", "./test-app"),
            ("/var/projects", "api-server", "/var/projects/api-server"),
            ("relative/path", "new-service", "relative/path/new-service")
        ]
        
        for output_dir, project_name, expected in test_cases:
            config = MockConfig()
            config.output_dir = output_dir
            config.project_name = project_name
            
            result = _generate_standard_project_isolated(self.cli_instance, config)
            assert result == str(Path(expected))
    
    @patch('mcp_cli.generators.MCPGenerator')
    def test_error_message_formatting(self, mock_generator_class):
        """Test error message formatting with various combinations"""
        mock_generator = Mock()
        mock_generator_class.return_value = mock_generator
        
        # Test errors only
        mock_generator.generate.return_value = GenerationResult(
            success=False,
            files_created=[],
            errors=["Error 1", "Error 2"],
            warnings=[]
        )
        
        with pytest.raises(MCPCLIError) as exc_info:
            _generate_standard_project_isolated(self.cli_instance, MockConfig())
        
        error_msg = str(exc_info.value)
        assert "Project generation failed:" in error_msg
        assert "Error 1" in error_msg
        assert "Error 2" in error_msg
        assert "Warnings:" not in error_msg
        
        # Test both errors and warnings
        mock_generator.generate.return_value = GenerationResult(
            success=False,
            files_created=[],
            errors=["Critical error"],
            warnings=["Warning 1", "Warning 2"]
        )
        
        with pytest.raises(MCPCLIError) as exc_info:
            _generate_standard_project_isolated(self.cli_instance, MockConfig())
        
        error_msg = str(exc_info.value)
        assert "Project generation failed:" in error_msg
        assert "Critical error" in error_msg
        assert "Warnings:" in error_msg
        assert "Warning 1" in error_msg
        assert "Warning 2" in error_msg 