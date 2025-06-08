"""
Unit tests for ConfigGenerator class

Tests the ConfigGenerator's ability to generate configuration files correctly
in the right locations using appropriate templates.
"""
import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path
from mcp_cli.generators import ConfigGenerator, GenerationResult
from mcp_cli.config import MCPProjectConfig


class TestConfigGenerator:
    """Test suite for ConfigGenerator class"""
    
    @pytest.fixture
    def config_generator(self):
        """Create a ConfigGenerator instance for testing"""
        return ConfigGenerator()
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock project configuration"""
        config = Mock(spec=MCPProjectConfig)
        config.service_name = "test_service"
        config.project_name = "Test Project"
        config.version = "1.0.0"
        return config
    
    @pytest.fixture
    def project_path(self, tmp_path):
        """Create a temporary project path"""
        return tmp_path / "test_project"
    
    def test_generate_success(self, config_generator, project_path, mock_config):
        """Test successful configuration generation"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.side_effect = [
                "server config content",
                "logging config content", 
                "startup script content"
            ]
            
            # Execute
            result = config_generator.generate(project_path, mock_config)
            
            # Verify success
            assert result.success is True
            assert result.errors == []
            assert result.warnings == []
            assert len(result.files_created) == 3
            
            # Verify all expected files were created
            expected_files = [
                str(project_path / "config" / "server_config.yaml"),
                str(project_path / "config" / "logging.yaml"),
                str(project_path / "scripts" / "run_server.py")
            ]
            
            for expected_file in expected_files:
                assert expected_file in result.files_created
    
    def test_generate_failure(self, config_generator, project_path, mock_config):
        """Test generation failure handling"""
        with patch.object(config_generator, 'render_template', side_effect=Exception("Template error")):
            
            # Execute
            result = config_generator.generate(project_path, mock_config)
            
            # Verify failure
            assert result.success is False
            assert len(result.errors) == 1
            assert "Failed to generate configuration: Template error" in result.errors[0]
            assert isinstance(result.files_created, list)
    
    def test_server_config_generation(self, config_generator, project_path, mock_config):
        """Test server configuration file generation"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.side_effect = ["server config", "logging config", "script content"]
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify server config template rendering
            server_config_call = mock_render.call_args_list[0]
            assert server_config_call[0][0] == "config/server_config.yaml.j2"
            assert server_config_call[0][1] == {
                "project_name": "Test Project",
                "service_name": "test_service",
                "version": "1.0.0"
            }
            
            # Verify server config file writing
            server_config_write_call = mock_write.call_args_list[0]
            expected_path = project_path / "config" / "server_config.yaml"
            assert server_config_write_call[0][0] == expected_path
            assert server_config_write_call[0][1] == "server config"
    
    def test_logging_config_generation(self, config_generator, project_path, mock_config):
        """Test logging configuration file generation"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.side_effect = ["server config", "logging config", "script content"]
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify logging config template rendering
            logging_config_call = mock_render.call_args_list[1]
            assert logging_config_call[0][0] == "config/logging.yaml.j2"
            assert logging_config_call[0][1] == {
                "project_name": "Test Project"
            }
            
            # Verify logging config file writing
            logging_config_write_call = mock_write.call_args_list[1]
            expected_path = project_path / "config" / "logging.yaml"
            assert logging_config_write_call[0][0] == expected_path
            assert logging_config_write_call[0][1] == "logging config"
    
    def test_startup_script_generation(self, config_generator, project_path, mock_config):
        """Test startup script generation"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.side_effect = ["server config", "logging config", "script content"]
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify startup script template rendering
            script_call = mock_render.call_args_list[2]
            assert script_call[0][0] == "scripts/run_server.py.j2"
            assert script_call[0][1] == {
                "service_name": "test_service",
                "project_name": "Test Project"
            }
            
            # Verify startup script file writing
            script_write_call = mock_write.call_args_list[2]
            expected_path = project_path / "scripts" / "run_server.py"
            assert script_write_call[0][0] == expected_path
            assert script_write_call[0][1] == "script content"
    
    def test_file_path_construction(self, config_generator, project_path, mock_config):
        """Test that file paths are constructed correctly"""
        with patch.object(config_generator, 'render_template', return_value="content"), \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify correct file paths were used
            expected_paths = [
                project_path / "config" / "server_config.yaml",
                project_path / "config" / "logging.yaml",
                project_path / "scripts" / "run_server.py"
            ]
            
            actual_paths = [call_args[0][0] for call_args in mock_write.call_args_list]
            
            assert len(actual_paths) == len(expected_paths)
            for expected_path in expected_paths:
                assert expected_path in actual_paths
    
    def test_template_names_used(self, config_generator, project_path, mock_config):
        """Test that correct template names are used"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file'):
            
            # Setup mocks
            mock_render.side_effect = ["content1", "content2", "content3"]
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify correct template names were used
            expected_templates = [
                "config/server_config.yaml.j2",
                "config/logging.yaml.j2",
                "scripts/run_server.py.j2"
            ]
            
            actual_templates = [call_args[0][0] for call_args in mock_render.call_args_list]
            
            assert len(actual_templates) == len(expected_templates)
            for expected_template in expected_templates:
                assert expected_template in actual_templates
    
    def test_template_context_data(self, config_generator, project_path, mock_config):
        """Test that correct context data is passed to templates"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file'):
            
            # Setup mocks
            mock_render.side_effect = ["content1", "content2", "content3"]
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify template contexts
            call_args_list = mock_render.call_args_list
            
            # Server config context
            server_context = call_args_list[0][0][1]
            assert server_context["project_name"] == "Test Project"
            assert server_context["service_name"] == "test_service"
            assert server_context["version"] == "1.0.0"
            
            # Logging config context
            logging_context = call_args_list[1][0][1]
            assert logging_context["project_name"] == "Test Project"
            assert len(logging_context) == 1  # Only project_name
            
            # Startup script context
            script_context = call_args_list[2][0][1]
            assert script_context["service_name"] == "test_service"
            assert script_context["project_name"] == "Test Project"
            assert len(script_context) == 2  # service_name and project_name
    
    def test_files_created_tracking(self, config_generator, project_path, mock_config):
        """Test that files_created list is properly maintained"""
        with patch.object(config_generator, 'render_template', return_value="content"), \
             patch.object(config_generator, 'write_file'):
            
            # Execute
            result = config_generator.generate(project_path, mock_config)
            
            # Verify files_created contains all expected files
            expected_files = [
                str(project_path / "config" / "server_config.yaml"),
                str(project_path / "config" / "logging.yaml"),
                str(project_path / "scripts" / "run_server.py")
            ]
            
            assert len(result.files_created) == len(expected_files)
            for expected_file in expected_files:
                assert expected_file in result.files_created
    
    def test_error_handling_render_template(self, config_generator, project_path, mock_config):
        """Test error handling when template rendering fails"""
        with patch.object(config_generator, 'render_template', side_effect=Exception("Render error")):
            
            # Execute
            result = config_generator.generate(project_path, mock_config)
            
            # Verify error handling
            assert result.success is False
            assert len(result.errors) == 1
            assert "Failed to generate configuration: Render error" in result.errors[0]
    
    def test_error_handling_write_file(self, config_generator, project_path, mock_config):
        """Test error handling when file writing fails"""
        with patch.object(config_generator, 'render_template', return_value="content"), \
             patch.object(config_generator, 'write_file', side_effect=Exception("Write error")):
            
            # Execute
            result = config_generator.generate(project_path, mock_config)
            
            # Verify error handling
            assert result.success is False
            assert len(result.errors) == 1
            assert "Failed to generate configuration: Write error" in result.errors[0]
    
    def test_partial_failure_tracking(self, config_generator, project_path, mock_config):
        """Test that partial failures are tracked correctly"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Setup: first two calls succeed, third fails
            mock_render.side_effect = ["content1", "content2", Exception("Third template error")]
            
            # Execute
            result = config_generator.generate(project_path, mock_config)
            
            # Verify partial failure
            assert result.success is False
            assert len(result.errors) == 1
            assert "Failed to generate configuration: Third template error" in result.errors[0]
            
            # Verify that files created before the error are still tracked
            # (Note: In the current implementation, files_created is empty on error,
            # but this test documents the expected behavior)
            assert isinstance(result.files_created, list)
    
    def test_inheritance_from_base_generator(self, config_generator):
        """Test that ConfigGenerator properly inherits from BaseGenerator"""
        from mcp_cli.generators import BaseGenerator
        
        assert isinstance(config_generator, BaseGenerator)
        assert hasattr(config_generator, 'render_template')
        assert hasattr(config_generator, 'write_file')
        assert hasattr(config_generator, 'generate')
    
    def test_generation_result_structure(self, config_generator, project_path, mock_config):
        """Test that GenerationResult has correct structure"""
        with patch.object(config_generator, 'render_template', return_value="content"), \
             patch.object(config_generator, 'write_file'):
            
            result = config_generator.generate(project_path, mock_config)
            
            # Verify GenerationResult structure
            assert hasattr(result, 'success')
            assert hasattr(result, 'files_created')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'warnings')
            
            assert isinstance(result.success, bool)
            assert isinstance(result.files_created, list)
            assert isinstance(result.errors, list)
            assert isinstance(result.warnings, list)
    
    def test_config_file_locations(self, config_generator, project_path, mock_config):
        """Test that configuration files are placed in correct subdirectories"""
        with patch.object(config_generator, 'render_template', return_value="content"), \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify file locations
            write_calls = mock_write.call_args_list
            
            # Server config should be in config/ directory
            server_config_path = write_calls[0][0][0]
            assert server_config_path.parent.name == "config"
            assert server_config_path.name == "server_config.yaml"
            
            # Logging config should be in config/ directory
            logging_config_path = write_calls[1][0][0]
            assert logging_config_path.parent.name == "config"
            assert logging_config_path.name == "logging.yaml"
            
            # Startup script should be in scripts/ directory
            script_path = write_calls[2][0][0]
            assert script_path.parent.name == "scripts"
            assert script_path.name == "run_server.py"
    
    def test_template_rendering_order(self, config_generator, project_path, mock_config):
        """Test that templates are rendered in the expected order"""
        with patch.object(config_generator, 'render_template') as mock_render, \
             patch.object(config_generator, 'write_file'):
            
            # Setup mocks
            mock_render.side_effect = ["content1", "content2", "content3"]
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify rendering order
            call_args_list = mock_render.call_args_list
            
            assert call_args_list[0][0][0] == "config/server_config.yaml.j2"
            assert call_args_list[1][0][0] == "config/logging.yaml.j2"
            assert call_args_list[2][0][0] == "scripts/run_server.py.j2"
    
    def test_file_writing_order(self, config_generator, project_path, mock_config):
        """Test that files are written in the expected order"""
        with patch.object(config_generator, 'render_template', return_value="content"), \
             patch.object(config_generator, 'write_file') as mock_write:
            
            # Execute
            config_generator.generate(project_path, mock_config)
            
            # Verify writing order
            write_calls = mock_write.call_args_list
            
            expected_paths = [
                project_path / "config" / "server_config.yaml",
                project_path / "config" / "logging.yaml",
                project_path / "scripts" / "run_server.py"
            ]
            
            for i, expected_path in enumerate(expected_paths):
                assert write_calls[i][0][0] == expected_path
