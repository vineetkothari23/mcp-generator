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
from pathlib import Path
from unittest.mock import Mock, patch
from mcp_cli.generators import ProjectStructureGenerator, GenerationResult

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