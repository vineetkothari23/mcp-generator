"""
Unit tests for TestGenerator class

Tests the TestGenerator's ability to generate test files correctly
using templates in the right locations.
"""
import pytest
import tempfile
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
            mock_render.side_effect = ["conftest content", "pytest.ini content", "coveragerc content"]
            
            # Execute
            test_generator._generate_pytest_config(project_path, mock_config, files_created)
            
            # Verify template rendering
            expected_calls = [
                call("tests/conftest.py.j2", {
                    "service_name": "test_service",
                    "project_name": "Test Project"
                }),
                call("tests/pytest.ini.j2", {
                    "project_name": "Test Project",
                    "service_name": "test_service"
                }),
                call("tests/.coveragerc.j2", {
                    "project_name": "Test Project",
                    "service_name": "test_service"
                })
            ]
            mock_render.assert_has_calls(expected_calls)
            
            # Verify file writing
            expected_write_calls = [
                call(project_path / "tests" / "conftest.py", "conftest content"),
                call(project_path / "pytest.ini", "pytest.ini content"),
                call(project_path / ".coveragerc", "coveragerc content")
            ]
            mock_write.assert_has_calls(expected_write_calls)
            
            # Verify files_created list
            assert len(files_created) == 3
            assert str(project_path / "tests" / "conftest.py") in files_created
            assert str(project_path / "pytest.ini") in files_created
            assert str(project_path / ".coveragerc") in files_created
    
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
                project_path / ".coveragerc",
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
                str(project_path / ".coveragerc"),
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
                "tests/.coveragerc.j2",
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


class TestTestGeneratorIntegration:
    """Integration tests that actually use real templates"""
    
    @pytest.fixture
    def real_config(self):
        """Create a real MCPProjectConfig for integration testing"""
        return MCPProjectConfig(
            project_name="test-mcp-server",
            service_name="test_service",
            description="Test MCP server",
            author="Test Author"
        )
    
    def test_template_files_exist_and_load(self):
        """Test that all required template files exist and can be loaded"""
        generator = TestGenerator()
        
        # Test that all expected templates exist and can be loaded
        required_templates = [
            "tests/conftest.py.j2",
            "tests/pytest.ini.j2", 
            "tests/.coveragerc.j2",
            "tests/fixtures.py.j2",
            "tests/test_server.py.j2",
            "tests/test_config.py.j2"
        ]
        
        test_context = {
            "service_name": "test_service",
            "project_name": "test-project"
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
        generator = TestGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            # This should work with real templates
            result = generator.generate(project_path, real_config)
            
            # Verify generation succeeded
            assert result.success is True
            assert len(result.errors) == 0
            assert len(result.files_created) == 6  # Updated count for .coveragerc
            
            # Verify all expected files were created
            expected_files = [
                project_path / "tests" / "conftest.py",
                project_path / "pytest.ini",
                project_path / ".coveragerc",
                project_path / "tests" / "fixtures" / "test_data.py",
                project_path / "tests" / "unit" / "test_server.py",
                project_path / "tests" / "unit" / "test_config.py"
            ]
            
            for expected_file in expected_files:
                assert expected_file.exists(), f"Expected file {expected_file} was not created"
                assert expected_file.stat().st_size > 0, f"File {expected_file} is empty"
    
    def test_template_content_substitution(self, real_config):
        """Test that template variables are properly substituted"""
        generator = TestGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check that pytest.ini contains the correct service name
            pytest_ini_path = project_path / "pytest.ini"
            pytest_ini_content = pytest_ini_path.read_text()
            assert "src/mcp_test_service" in pytest_ini_content
            assert "test-mcp-server" in pytest_ini_content
            
            # Check that .coveragerc contains the correct service name
            coveragerc_path = project_path / ".coveragerc"
            coveragerc_content = coveragerc_path.read_text()
            assert "src/mcp_test_service" in coveragerc_content
            assert "test-mcp-server" in coveragerc_content
            
            # Check conftest.py contains service references
            conftest_path = project_path / "tests" / "conftest.py"
            conftest_content = conftest_path.read_text()
            assert "test_service" in conftest_content
            assert "test-mcp-server" in conftest_content
    
    def test_template_syntax_validity(self):
        """Test that templates have valid syntax and render without errors"""
        generator = TestGenerator()
        
        # Test various context combinations
        test_contexts = [
            {
                "service_name": "simple_service",
                "project_name": "simple-project"
            },
            {
                "service_name": "complex_service_name",
                "project_name": "complex-project-name-with-hyphens"
            },
            {
                "service_name": "api_service",
                "project_name": "api-mcp-server"
            }
        ]
        
        templates = [
            "tests/conftest.py.j2",
            "tests/pytest.ini.j2",
            "tests/.coveragerc.j2", 
            "tests/fixtures.py.j2",
            "tests/test_server.py.j2",
            "tests/test_config.py.j2"
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
    
    def test_generated_files_are_valid_python_syntax(self, real_config):
        """Test that generated Python files have valid syntax"""
        import ast
        
        generator = TestGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check Python files for valid syntax
            python_files = [
                project_path / "tests" / "conftest.py",
                project_path / "tests" / "fixtures" / "test_data.py",
                project_path / "tests" / "unit" / "test_server.py",
                project_path / "tests" / "unit" / "test_config.py"
            ]
            
            for python_file in python_files:
                try:
                    content = python_file.read_text()
                    # This will raise SyntaxError if the file has invalid Python syntax
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Generated file {python_file} has invalid Python syntax: {str(e)}")
    
    def test_missing_template_handling(self):
        """Test behavior when a template is missing"""
        generator = TestGenerator()
        
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
                    author="test"
                )
                
                result = generator.generate(project_path, config)
                
                assert result.success is False
                assert len(result.errors) > 0
                assert "Failed to generate tests" in result.errors[0]
