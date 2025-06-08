"""
Unit tests for TestGenerator class

Tests the TestGenerator's ability to generate test files correctly
using templates in the right locations.
"""
import pytest
from unittest.mock import Mock, patch, call
from pathlib import Path
from mcp_cli.generators import TestGenerator, GenerationResult
from mcp_cli.config import MCPProjectConfig


class TestTestGenerator:
    """Test suite for TestGenerator class"""
    
    @pytest.fixture
    def test_generator(self):
        """Create a TestGenerator instance for testing"""
        return TestGenerator()
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock project configuration"""
        config = Mock(spec=MCPProjectConfig)
        config.service_name = "test_service"
        config.project_name = "Test Project"
        return config
    
    @pytest.fixture
    def project_path(self, tmp_path):
        """Create a temporary project path"""
        return tmp_path / "test_project"
    
    def test_generate_success(self, test_generator, project_path, mock_config):
        """Test successful test generation"""
        with patch.object(test_generator, '_generate_pytest_config') as mock_pytest, \
             patch.object(test_generator, '_generate_test_fixtures') as mock_fixtures, \
             patch.object(test_generator, '_generate_basic_tests') as mock_basic:
            
            # Execute
            result = test_generator.generate(project_path, mock_config)
            
            # Verify
            assert result.success is True
            assert result.errors == []
            assert result.warnings == []
            assert isinstance(result.files_created, list)
            
            # Verify all generation methods were called
            mock_pytest.assert_called_once_with(project_path, mock_config, result.files_created)
            mock_fixtures.assert_called_once_with(project_path, mock_config, result.files_created)
            mock_basic.assert_called_once_with(project_path, mock_config, result.files_created)
    
    def test_generate_failure(self, test_generator, project_path, mock_config):
        """Test generation failure handling"""
        with patch.object(test_generator, '_generate_pytest_config', side_effect=Exception("Test error")):
            
            # Execute
            result = test_generator.generate(project_path, mock_config)
            
            # Verify
            assert result.success is False
            assert len(result.errors) == 1
            assert "Failed to generate tests: Test error" in result.errors[0]
            assert isinstance(result.files_created, list)
    
    def test_generate_pytest_config(self, test_generator, project_path, mock_config):
        """Test pytest configuration generation"""
        files_created = []
        
        with patch.object(test_generator, 'render_template') as mock_render, \
             patch.object(test_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.side_effect = ["conftest content", "pytest.ini content"]
            
            # Execute
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
            
            # Verify template rendering
            expected_calls = [
                call("tests/conftest.py.j2", {
                    "service_name": "test_service",
                    "project_name": "Test Project"
                }),
                call("tests/pytest.ini.j2", {
                    "project_name": "Test Project"
                })
            ]
            mock_render.assert_has_calls(expected_calls)
            
            # Verify file writing
            expected_write_calls = [
                call(project_path / "tests" / "conftest.py", "conftest content"),
                call(project_path / "pytest.ini", "pytest.ini content")
            ]
            mock_write.assert_has_calls(expected_write_calls)
            
            # Verify files_created list
            assert len(files_created) == 2
            assert str(project_path / "tests" / "conftest.py") in files_created
            assert str(project_path / "pytest.ini") in files_created
    
    def test_generate_test_fixtures(self, test_generator, project_path, mock_config):
        """Test test fixtures generation"""
        files_created = []
        
        with patch.object(test_generator, 'render_template') as mock_render, \
             patch.object(test_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.return_value = "fixtures content"
            
            # Execute
            test_generator._generate_test_fixtures(project_path, mock_config, files_created)
            
            # Verify template rendering
            mock_render.assert_called_once_with("tests/fixtures.py.j2", {
                "service_name": "test_service",
                "project_name": "Test Project"
            })
            
            # Verify file writing
            expected_path = project_path / "tests" / "fixtures" / "test_data.py"
            mock_write.assert_called_once_with(expected_path, "fixtures content")
            
            # Verify files_created list
            assert len(files_created) == 1
            assert str(expected_path) in files_created
    
    def test_generate_basic_tests(self, test_generator, project_path, mock_config):
        """Test basic test cases generation"""
        files_created = []
        
        with patch.object(test_generator, 'render_template') as mock_render, \
             patch.object(test_generator, 'write_file') as mock_write:
            
            # Setup mocks
            mock_render.side_effect = ["server test content", "config test content"]
            
            # Execute
            test_generator._generate_basic_tests(project_path, mock_config, files_created)
            
            # Verify template rendering
            expected_calls = [
                call("tests/test_server.py.j2", {
                    "service_name": "test_service",
                    "project_name": "Test Project"
                }),
                call("tests/test_config.py.j2", {
                    "service_name": "test_service",
                    "project_name": "Test Project"
                })
            ]
            mock_render.assert_has_calls(expected_calls)
            
            # Verify file writing
            expected_write_calls = [
                call(project_path / "tests" / "unit" / "test_server.py", "server test content"),
                call(project_path / "tests" / "unit" / "test_config.py", "config test content")
            ]
            mock_write.assert_has_calls(expected_write_calls)
            
            # Verify files_created list
            assert len(files_created) == 2
            assert str(project_path / "tests" / "unit" / "test_server.py") in files_created
            assert str(project_path / "tests" / "unit" / "test_config.py") in files_created
    
    def test_file_path_construction(self, test_generator, project_path, mock_config):
        """Test that file paths are constructed correctly"""
        files_created = []
        
        with patch.object(test_generator, 'render_template', return_value="content"), \
             patch.object(test_generator, 'write_file') as mock_write:
            
            # Execute all generation methods
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
            test_generator._generate_test_fixtures(project_path, mock_config, files_created)
            test_generator._generate_basic_tests(project_path, mock_config, files_created)
            
            # Verify correct file paths were used
            expected_paths = [
                project_path / "tests" / "conftest.py",
                project_path / "pytest.ini",
                project_path / "tests" / "fixtures" / "test_data.py",
                project_path / "tests" / "unit" / "test_server.py",
                project_path / "tests" / "unit" / "test_config.py"
            ]
            
            actual_paths = [call_args[0][0] for call_args in mock_write.call_args_list]
            
            for expected_path in expected_paths:
                assert expected_path in actual_paths
    
    def test_template_context_data(self, test_generator, project_path, mock_config):
        """Test that correct context data is passed to templates"""
        files_created = []
        
        with patch.object(test_generator, 'render_template') as mock_render, \
             patch.object(test_generator, 'write_file'):
            
            # Execute
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
            test_generator._generate_test_fixtures(project_path, mock_config, files_created)
            test_generator._generate_basic_tests(project_path, mock_config, files_created)
            
            # Verify all template calls received correct context
            for call_args in mock_render.call_args_list:
                template_name, context = call_args[0]
                
                # All templates should receive service_name and project_name
                if template_name != "tests/pytest.ini.j2":  # pytest.ini only needs project_name
                    assert context["service_name"] == "test_service"
                assert context["project_name"] == "Test Project"
    
    def test_files_created_tracking(self, test_generator, project_path, mock_config):
        """Test that files_created list is properly maintained"""
        with patch.object(test_generator, 'render_template', return_value="content"), \
             patch.object(test_generator, 'write_file'):
            
            # Execute
            result = test_generator.generate(project_path, mock_config)
            
            # Verify files_created contains all expected files
            expected_files = [
                str(project_path / "tests" / "conftest.py"),
                str(project_path / "pytest.ini"),
                str(project_path / "tests" / "fixtures" / "test_data.py"),
                str(project_path / "tests" / "unit" / "test_server.py"),
                str(project_path / "tests" / "unit" / "test_config.py")
            ]
            
            assert len(result.files_created) == len(expected_files)
            for expected_file in expected_files:
                assert expected_file in result.files_created
    
    def test_template_names_used(self, test_generator, project_path, mock_config):
        """Test that correct template names are used"""
        files_created = []
        
        with patch.object(test_generator, 'render_template') as mock_render, \
             patch.object(test_generator, 'write_file'):
            
            # Execute all generation methods
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
            test_generator._generate_test_fixtures(project_path, mock_config, files_created)
            test_generator._generate_basic_tests(project_path, mock_config, files_created)
            
            # Verify correct template names were used
            expected_templates = [
                "tests/conftest.py.j2",
                "tests/pytest.ini.j2",
                "tests/fixtures.py.j2",
                "tests/test_server.py.j2",
                "tests/test_config.py.j2"
            ]
            
            actual_templates = [call_args[0][0] for call_args in mock_render.call_args_list]
            
            for expected_template in expected_templates:
                assert expected_template in actual_templates
    
    def test_error_handling_in_individual_methods(self, test_generator, project_path, mock_config):
        """Test error handling in individual generation methods"""
        files_created = []
        
        # Test error in render_template
        with patch.object(test_generator, 'render_template', side_effect=Exception("Template error")), \
             pytest.raises(Exception, match="Template error"):
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
        
        # Test error in write_file
        with patch.object(test_generator, 'render_template', return_value="content"), \
             patch.object(test_generator, 'write_file', side_effect=Exception("Write error")), \
             pytest.raises(Exception, match="Write error"):
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
    
    def test_inheritance_from_base_generator(self, test_generator):
        """Test that TestGenerator properly inherits from BaseGenerator"""
        from mcp_cli.generators import BaseGenerator
        
        assert isinstance(test_generator, BaseGenerator)
        assert hasattr(test_generator, 'render_template')
        assert hasattr(test_generator, 'write_file')
        assert hasattr(test_generator, 'generate')
    
    def test_generation_result_structure(self, test_generator, project_path, mock_config):
        """Test that GenerationResult has correct structure"""
        with patch.object(test_generator, 'render_template', return_value="content"), \
             patch.object(test_generator, 'write_file'):
            
            result = test_generator.generate(project_path, mock_config)
            
            # Verify GenerationResult structure
            assert hasattr(result, 'success')
            assert hasattr(result, 'files_created')
            assert hasattr(result, 'errors')
            assert hasattr(result, 'warnings')
            
            assert isinstance(result.success, bool)
            assert isinstance(result.files_created, list)
            assert isinstance(result.errors, list)
            assert isinstance(result.warnings, list)
