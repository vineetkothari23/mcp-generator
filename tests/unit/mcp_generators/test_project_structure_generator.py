"""
Tests for the ProjectStructureGenerator class.

This module contains tests for:
- Project structure generation
- Core file generation
- Configuration file generation
- Documentation generation
- Error handling
"""

import pytest
import tempfile
import ast
import tomllib
from pathlib import Path
from unittest.mock import Mock, patch
from mcp_cli.generators import ProjectStructureGenerator, GenerationResult
from mcp_cli.config import MCPProjectConfig

@pytest.fixture
def project_config():
    """Fixture providing a mock project configuration"""
    config = Mock()
    config.service_name = "test_service"
    config.project_name = "test_project"
    config.version = "1.0.0"
    config.description = "Test project description"
    config.author = "Test Author"
    config.python_version = "3.9"
    config.test_framework = "pytest"
    return config

@pytest.fixture
def generator():
    """Fixture providing a ProjectStructureGenerator instance"""
    return ProjectStructureGenerator()

@pytest.fixture
def temp_project_dir(tmp_path):
    """Fixture providing a temporary project directory"""
    return tmp_path / "test_project"

def test_generate_project_structure(generator, temp_project_dir, project_config):
    """Test basic project structure generation"""
    result = generator.generate(temp_project_dir, project_config)
    
    assert result.success
    assert len(result.files_created) > 0
    assert len(result.errors) == 0
    
    # Check if core directories were created
    expected_dirs = [
        "src",
        f"src/mcp_{project_config.service_name}",
        "tests/unit",
        "tests/integration",
        "tests/fixtures",
        "config",
        "scripts",
        "docs",
        "docker"
    ]
    
    for dir_path in expected_dirs:
        assert (temp_project_dir / dir_path).exists()
        assert (temp_project_dir / dir_path).is_dir()

def test_generate_core_files(generator, temp_project_dir, project_config):
    """Test generation of core Python files"""
    files_created = []
    generator._generate_core_files(temp_project_dir, project_config, files_created)
    
    expected_files = [
        f"src/mcp_{project_config.service_name}/__init__.py",
        f"src/mcp_{project_config.service_name}/server.py",
        f"src/mcp_{project_config.service_name}/config.py",
        f"src/mcp_{project_config.service_name}/models.py",
        f"src/mcp_{project_config.service_name}/client.py",
        f"src/mcp_{project_config.service_name}/tools.py"
    ]
    
    for file_path in expected_files:
        assert (temp_project_dir / file_path).exists()
        assert (temp_project_dir / file_path).is_file()
        assert str(temp_project_dir / file_path) in files_created

def test_generate_config_files(generator, temp_project_dir, project_config):
    """Test generation of configuration files"""
    files_created = []
    generator._generate_config_files(temp_project_dir, project_config, files_created)
    
    expected_files = [
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        ".env.example"
    ]
    
    for file_path in expected_files:
        assert (temp_project_dir / file_path).exists()
        assert (temp_project_dir / file_path).is_file()
        assert str(temp_project_dir / file_path) in files_created

def test_generate_docs(generator, temp_project_dir, project_config):
    """Test generation of documentation files"""
    files_created = []
    generator._generate_docs(temp_project_dir, project_config, files_created)
    
    expected_files = [
        "README.md"
    ]
    
    for file_path in expected_files:
        assert (temp_project_dir / file_path).exists()
        assert (temp_project_dir / file_path).is_file()
        assert str(temp_project_dir / file_path) in files_created

def test_generate_with_existing_directory(generator, temp_project_dir, project_config):
    """Test generation with existing directory structure"""
    # Create some existing directories
    (temp_project_dir / "src").mkdir(parents=True)
    (temp_project_dir / "tests").mkdir(parents=True)
    
    result = generator.generate(temp_project_dir, project_config)
    
    assert result.success
    assert len(result.errors) == 0
    # Should still create all required files
    assert len(result.files_created) > 0

def test_generate_with_permission_error(generator, temp_project_dir, project_config):
    """Test handling of permission errors during generation"""
    with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
        result = generator.generate(temp_project_dir, project_config)
        
        assert not result.success
        assert len(result.errors) > 0
        assert any("Permission denied" in error for error in result.errors)

def test_generate_with_invalid_config(generator, temp_project_dir):
    """Test generation with invalid configuration"""
    invalid_config = Mock()
    invalid_config.service_name = None  # Missing required attribute
    
    result = generator.generate(temp_project_dir, invalid_config)
    
    assert not result.success
    assert len(result.errors) > 0

def test_file_content_generation(generator, temp_project_dir, project_config):
    """Test that generated files contain expected content"""
    result = generator.generate(temp_project_dir, project_config)
    
    # Check README.md content
    readme_path = temp_project_dir / "README.md"
    assert readme_path.exists()
    readme_content = readme_path.read_text(encoding='utf-8')
    assert project_config.project_name in readme_content
    assert project_config.description in readme_content
    
    # Check __init__.py content
    init_path = temp_project_dir / f"src/mcp_{project_config.service_name}/__init__.py"
    assert init_path.exists()
    init_content = init_path.read_text()
    assert project_config.version in init_content

def test_template_rendering(generator, temp_project_dir, project_config):
    """Test template rendering functionality"""
    files_created = []
    generator._generate_core_files(temp_project_dir, project_config, files_created)
    
    # Check server.py template rendering
    server_path = temp_project_dir / f"src/mcp_{project_config.service_name}/server.py"
    assert server_path.exists()
    server_content = server_path.read_text()
    
    # Verify template variables were properly rendered
    assert project_config.service_name in server_content
    assert project_config.project_name in server_content

def test_error_handling_in_file_generation(generator, temp_project_dir, project_config):
    """Test error handling during file generation"""
    with patch('builtins.open', side_effect=IOError("Failed to write file")):
        result = generator.generate(temp_project_dir, project_config)
        
        assert not result.success
        assert len(result.errors) > 0
        assert any("Failed to write file" in error for error in result.errors)


class TestProjectStructureGeneratorIntegration:
    """Integration tests that actually use real templates"""
    
    @pytest.fixture
    def real_config(self):
        """Create a real MCPProjectConfig for integration testing"""
        return MCPProjectConfig(
            project_name="test-structure-server",
            service_name="structure_service",
            description="Test Structure MCP server",
            author="Test Author",
            version="1.5.0",
            python_version="3.11",
            test_framework="pytest"
        )
    
    def test_template_files_exist_and_load(self):
        """Test that all required template files exist and can be loaded"""
        generator = ProjectStructureGenerator()
        
        # Test that all expected templates exist and can be loaded
        required_templates = [
            # Core Python files
            "python/__init__.py.j2",
            "python/server.py.j2",
            "python/config.py.j2",
            "python/models.py.j2",
            "python/client.py.j2",
            "python/tools.py.j2",
            # Config files
            "config/requirements.txt.j2",
            "config/requirements-dev.txt.j2",
            "config/pyproject.toml.j2",
            "config/.env.example.j2",
            # Documentation
            "docs/README.md.j2"
        ]
        
        test_context = {
            "service_name": "structure_service",
            "project_name": "test-structure-server",
            "version": "1.5.0",
            "description": "Test Structure MCP server",
            "author": "Test Author",
            "python_version": "3.11",
            "test_framework": "pytest"
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
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            # This should work with real templates
            result = generator.generate(project_path, real_config)
            
            # Verify generation succeeded
            assert result.success is True
            assert len(result.errors) == 0
            assert len(result.files_created) == 11  # 6 core + 4 config + 1 doc files
            
            # Verify all expected files were created
            expected_files = [
                # Core Python files
                project_path / "src" / "mcp_structure_service" / "__init__.py",
                project_path / "src" / "mcp_structure_service" / "server.py",
                project_path / "src" / "mcp_structure_service" / "config.py",
                project_path / "src" / "mcp_structure_service" / "models.py",
                project_path / "src" / "mcp_structure_service" / "client.py",
                project_path / "src" / "mcp_structure_service" / "tools.py",
                # Config files
                project_path / "requirements.txt",
                project_path / "requirements-dev.txt",
                project_path / "pyproject.toml",
                project_path / ".env.example",
                # Documentation
                project_path / "README.md"
            ]
            
            for expected_file in expected_files:
                assert expected_file.exists(), f"Expected file {expected_file} was not created"
                assert expected_file.stat().st_size > 0, f"File {expected_file} is empty"
    
    def test_directory_structure_creation(self, real_config):
        """Test that directory structure is created correctly"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Verify all expected directories were created
            expected_directories = [
                project_path / "src",
                project_path / "src" / "mcp_structure_service",
                project_path / "tests" / "unit",
                project_path / "tests" / "integration",
                project_path / "tests" / "fixtures",
                project_path / "config",
                project_path / "scripts",
                project_path / "docs",
                project_path / "docker"
            ]
            
            for expected_dir in expected_directories:
                assert expected_dir.exists(), f"Expected directory {expected_dir} was not created"
                assert expected_dir.is_dir(), f"Path {expected_dir} exists but is not a directory"
    
    def test_generated_python_files_are_valid(self, real_config):
        """Test that generated Python files have valid syntax"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check Python files for valid syntax
            python_files = [
                project_path / "src" / "mcp_structure_service" / "__init__.py",
                project_path / "src" / "mcp_structure_service" / "server.py",
                project_path / "src" / "mcp_structure_service" / "config.py",
                project_path / "src" / "mcp_structure_service" / "models.py",
                project_path / "src" / "mcp_structure_service" / "client.py",
                project_path / "src" / "mcp_structure_service" / "tools.py"
            ]
            
            for python_file in python_files:
                try:
                    content = python_file.read_text(encoding='utf-8')
                    # This will raise SyntaxError if the file has invalid Python syntax
                    ast.parse(content)
                except SyntaxError as e:
                    pytest.fail(f"Generated file {python_file} has invalid Python syntax: {str(e)}")
    
    def test_pyproject_toml_is_valid(self, real_config):
        """Test that generated pyproject.toml has valid TOML syntax"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check pyproject.toml for valid TOML syntax
            pyproject_file = project_path / "pyproject.toml"
            try:
                content = pyproject_file.read_text(encoding='utf-8')
                # This will raise tomllib.TOMLDecodeError if the file has invalid TOML syntax
                parsed_toml = tomllib.loads(content)
                assert parsed_toml is not None
                assert isinstance(parsed_toml, dict)
                
                # Verify expected sections exist
                expected_sections = ['build-system', 'project', 'tool']
                for section in expected_sections:
                    assert section in parsed_toml, f"Expected section '{section}' not found in pyproject.toml"
                    
            except tomllib.TOMLDecodeError as e:
                pytest.fail(f"Generated pyproject.toml has invalid TOML syntax: {str(e)}")
    
    def test_template_content_substitution(self, real_config):
        """Test that template variables are properly substituted"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check that README.md contains the correct substitutions
            readme_path = project_path / "README.md"
            readme_content = readme_path.read_text(encoding='utf-8')
            assert "test-structure-server" in readme_content
            assert "structure_service" in readme_content
            assert "Test Structure MCP server" in readme_content
            assert "mcp_structure_service" in readme_content  # Check service name in module path
            
            # Check that __init__.py contains version
            init_path = project_path / "src" / "mcp_structure_service" / "__init__.py"
            init_content = init_path.read_text(encoding='utf-8')
            assert "1.5.0" in init_content
            assert "Structure_service" in init_content  # Template uses title filter
            assert "Structure_serviceServer" in init_content  # Template uses pascal_case filter
            
            # Check that pyproject.toml contains project info
            pyproject_path = project_path / "pyproject.toml"
            pyproject_content = pyproject_path.read_text(encoding='utf-8')
            assert "test-structure-server" in pyproject_content
            assert "structure_service" in pyproject_content
            assert "Test Author" in pyproject_content
            assert "1.5.0" in pyproject_content
            assert "3.11" in pyproject_content
            
            # Check that .env.example contains service name
            env_path = project_path / ".env.example"
            env_content = env_path.read_text(encoding='utf-8')
            assert "STRUCTURE_SERVICE" in env_content  # Template uses .upper() for env vars
            assert "test-structure-server" in env_content
    
    def test_template_syntax_validity(self):
        """Test that templates have valid syntax and render without errors"""
        generator = ProjectStructureGenerator()
        
        # Test various context combinations
        test_contexts = [
            {
                "service_name": "simple_service",
                "project_name": "simple-project",
                "version": "1.0.0",
                "description": "Simple test",
                "author": "Test Author",
                "python_version": "3.9",
                "test_framework": "pytest"
            },
            {
                "service_name": "complex_service_name",
                "project_name": "complex-project-name-with-hyphens",
                "version": "0.1.0-alpha",
                "description": "Complex test with special characters",
                "author": "Test Author with Special Chars",
                "python_version": "3.11",
                "test_framework": "unittest"
            }
        ]
        
        templates = [
            "python/__init__.py.j2",
            "python/server.py.j2",
            "python/config.py.j2",
            "python/models.py.j2",
            "python/client.py.j2",
            "python/tools.py.j2",
            "config/requirements.txt.j2",
            "config/requirements-dev.txt.j2",
            "config/pyproject.toml.j2",
            "config/.env.example.j2",
            "docs/README.md.j2"
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
    
    def test_requirements_files_have_valid_format(self, real_config):
        """Test that generated requirements files have valid format"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Check requirements.txt format
            req_file = project_path / "requirements.txt"
            req_content = req_file.read_text(encoding='utf-8')
            lines = [line.strip() for line in req_content.split('\n') if line.strip()]
            
            # Verify each line is either a comment, empty, or a valid package spec
            for line in lines:
                if line.startswith('#'):
                    continue  # Comment line
                if '==' in line or '>=' in line or '<=' in line or '~=' in line or line.isalpha():
                    continue  # Valid package specification
                pytest.fail(f"Invalid line in requirements.txt: '{line}'")
            
            # Check requirements-dev.txt format
            dev_req_file = project_path / "requirements-dev.txt"
            dev_req_content = dev_req_file.read_text(encoding='utf-8')
            assert "pytest" in dev_req_content  # Should contain the specified test framework
    
    def test_missing_template_handling(self):
        """Test behavior when a template is missing"""
        generator = ProjectStructureGenerator()
        
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
                    version="1.0.0",
                    python_version="3.9",
                    test_framework="pytest"
                )
                
                result = generator.generate(project_path, config)
                
                assert result.success is False
                assert len(result.errors) > 0
                assert "Failed to generate project structure" in result.errors[0]
    
    def test_file_permissions_and_structure(self, real_config):
        """Test that files are created with proper permissions and structure"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Verify all files are readable
            for file_path_str in result.files_created:
                file_path = Path(file_path_str)
                assert file_path.exists()
                assert file_path.is_file()
                
                # Verify file is readable
                try:
                    content = file_path.read_text(encoding='utf-8')
                    assert len(content) > 0
                except Exception as e:
                    pytest.fail(f"File {file_path} is not readable: {str(e)}")
    
    def test_project_structure_completeness(self, real_config):
        """Test that generated project has all necessary components for an MCP server"""
        generator = ProjectStructureGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test-project"
            
            result = generator.generate(project_path, real_config)
            assert result.success is True
            
            # Verify essential MCP server components exist
            essential_files = [
                "src/mcp_structure_service/server.py",  # Main server
                "src/mcp_structure_service/tools.py",   # MCP tools
                "src/mcp_structure_service/client.py",  # API client
                "src/mcp_structure_service/models.py",  # Data models
                "src/mcp_structure_service/config.py",  # Configuration
                "requirements.txt",                      # Dependencies
                "pyproject.toml",                       # Project config
                "README.md"                             # Documentation
            ]
            
            for essential_file in essential_files:
                file_path = project_path / essential_file
                assert file_path.exists(), f"Essential MCP server file {essential_file} is missing"
                assert file_path.stat().st_size > 0, f"Essential file {essential_file} is empty" 