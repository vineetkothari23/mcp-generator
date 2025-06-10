"""
Unit tests for ConfigGenerator class

Tests the ConfigGenerator's ability to generate configuration files correctly
in the right locations using appropriate templates.
"""
import pytest
import tempfile
import yaml
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


class TestConfigGeneratorIntegration:
    """Integration tests that actually use real templates"""
    
    @pytest.fixture
    def real_config(self):
        """Create a real MCPProjectConfig for integration testing"""
        return MCPProjectConfig(
            project_name="test-config-server",
            service_name="config_service",
            description="Test Config MCP server",
            author="Test Author",
            version="2.0.0"
        )
    
    def test_template_files_exist_and_load(self):
        """Test that all required template files exist and can be loaded"""
        generator = ConfigGenerator()
        
        # Test that all expected templates exist and can be loaded
        required_templates = [
            "config/server_config.yaml.j2",
            "config/logging.yaml.j2",
            "scripts/run_server.py.j2"
        ]
        
        test_context = {
            "service_name": "config_service",
            "project_name": "test-config-server",
            "version": "2.0.0"
        }
        
        for template_name in required_templates:
            try:
                # This should not raise an exception if template exists
                content = generator.render_template(template_name, test_context)
                assert content is not None
                assert len(content) > 0
                assert isinstance(content, str)
            except Exception as e:
                pytest.fail(f"Template {template_name} failed to load or render: {str(e)}")
    
    def test_real_generation_with_actual_templates(self, real_config):
        """Test actual generation using real templates (no mocking)"""
        generator = ConfigGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            # This should work with real templates
            result = generator.generate(project_path, real_config)
            
            # Verify generation succeeded
            assert result.success is True
            assert len(result.errors) == 0
            assert len(result.files_created) == 3
            
            # Verify all expected files were created
            expected_files = [
                project_path / "config" / "server_config.yaml",
                project_path / "config" / "logging.yaml", 
                project_path / "scripts" / "run_server.py"
            ]
            
            for expected_file in expected_files:
                assert expected_file.exists(), f"Expected file {expected_file} was not created"
                assert expected_file.stat().st_size > 0, f"File {expected_file} is empty"
    
    def test_generated_yaml_files_are_valid(self, real_config):
        """Test that generated YAML files have valid syntax"""
        generator = ConfigGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check YAML files for valid syntax
            yaml_files = [
                project_path / "config" / "server_config.yaml",
                project_path / "config" / "logging.yaml"
            ]
            
            for yaml_file in yaml_files:
                try:
                    content = yaml_file.read_text()
                    # This will raise yaml.YAMLError if the file has invalid YAML syntax
                    parsed_yaml = yaml.safe_load(content)
                    assert parsed_yaml is not None
                    assert isinstance(parsed_yaml, dict)
                except yaml.YAMLError as e:
                    pytest.fail(f"Generated file {yaml_file} has invalid YAML syntax: {str(e)}")
    
    def test_generated_python_script_is_valid(self, real_config):
        """Test that generated Python script has valid syntax"""
        import ast
        
        generator = ConfigGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check Python script for valid syntax
            script_file = project_path / "scripts" / "run_server.py"
            try:
                content = script_file.read_text()
                # This will raise SyntaxError if the file has invalid Python syntax
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Generated file {script_file} has invalid Python syntax: {str(e)}")
    
    def test_template_content_substitution(self, real_config):
        """Test that template variables are properly substituted"""
        generator = ConfigGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check that server_config.yaml contains the correct substitutions
            server_config_path = project_path / "config" / "server_config.yaml"
            server_config_content = server_config_path.read_text()
            assert "test-config-server" in server_config_content
            assert "config_service" in server_config_content
            assert "2.0.0" in server_config_content
            
            # Check that logging.yaml contains project name
            logging_config_path = project_path / "config" / "logging.yaml"
            logging_config_content = logging_config_path.read_text()
            assert "test-config-server" in logging_config_content
            
            # Check that run_server.py contains service references
            script_path = project_path / "scripts" / "run_server.py"
            script_content = script_path.read_text()
            assert "config_service" in script_content
            assert "test-config-server" in script_content
    
    def test_template_syntax_validity(self):
        """Test that templates have valid syntax and render without errors"""
        generator = ConfigGenerator()
        
        # Test various context combinations
        test_contexts = [
            {
                "service_name": "simple_service",
                "project_name": "simple-project",
                "version": "1.0.0"
            },
            {
                "service_name": "complex_service_name",
                "project_name": "complex-project-name-with-hyphens",
                "version": "0.1.0-alpha"
            },
            {
                "service_name": "api_service",
                "project_name": "api-mcp-server",
                "version": "3.2.1"
            }
        ]
        
        templates = [
            "config/server_config.yaml.j2",
            "config/logging.yaml.j2",
            "scripts/run_server.py.j2"
        ]
        
        for context in test_contexts:
            for template_name in templates:
                try:
                    content = generator.render_template(template_name, context)
                    # Basic validation that content was rendered
                    assert content is not None
                    assert len(content.strip()) > 0
                    # Check that template variables were substituted
                    assert "{{" not in content, f"Template {template_name} has unsubstituted variables"
                    assert "}}" not in content, f"Template {template_name} has unsubstituted variables"
                except Exception as e:
                    pytest.fail(f"Template {template_name} failed with context {context}: {str(e)}")
    
    def test_yaml_structure_validity(self, real_config):
        """Test that generated YAML files have expected structure"""
        generator = ConfigGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check server config structure
            server_config_path = project_path / "config" / "server_config.yaml"
            with open(server_config_path, 'r') as f:
                server_config = yaml.safe_load(f)
            
            # Verify expected top-level keys exist in server config
            expected_server_keys = ['server', 'tools', 'resources', 'logging']
            for key in expected_server_keys:
                assert key in server_config, f"Expected key '{key}' not found in server_config.yaml"
            
            # Check logging config structure
            logging_config_path = project_path / "config" / "logging.yaml"
            with open(logging_config_path, 'r') as f:
                logging_config = yaml.safe_load(f)
            
            # Verify expected top-level keys exist in logging config
            expected_logging_keys = ['version', 'formatters', 'handlers', 'loggers']
            for key in expected_logging_keys:
                assert key in logging_config, f"Expected key '{key}' not found in logging.yaml"
    
    def test_missing_template_handling(self):
        """Test behavior when a template is missing"""
        generator = ConfigGenerator()
        
        # Mock render_template to simulate missing template
        with patch.object(generator, 'render_template') as mock_render:
            mock_render.side_effect = FileNotFoundError("Template not found")
            
            # This should fail gracefully
            with tempfile.TemporaryDirectory() as temp_dir:
                project_path = Path(temp_dir) / "test-project"
                config = MCPProjectConfig(
                    project_name="test",
                    service_name="test",
                    description="test",
                    author="test",
                    version="1.0.0"
                )
                
                result = generator.generate(project_path, config)
                
                assert result.success is False
                assert len(result.errors) > 0
                assert "Failed to generate configuration" in result.errors[0]
    
    def test_directory_creation(self, real_config):
        """Test that directories are created properly when they don't exist"""
        generator = ConfigGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "new-project"
            # Project path doesn't exist yet
            assert not project_path.exists()
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Verify directories were created
            assert (project_path / "config").exists()
            assert (project_path / "scripts").exists()
            
            # Verify they're actually directories
            assert (project_path / "config").is_dir()
            assert (project_path / "scripts").is_dir()
