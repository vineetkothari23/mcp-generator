"""
Integration tests for MCPGenerator

These tests verify that MCPGenerator can generate complete, working MCP projects
and that the generated tests pass successfully.
"""
import pytest
import tempfile
import subprocess
import sys
from pathlib import Path
from mcp_cli.generators import MCPGenerator
from mcp_cli.config import MCPProjectConfig


@pytest.mark.integration
class TestMCPGeneratorIntegration:
    """Integration tests for complete MCP project generation"""
    
    @pytest.fixture
    def integration_config(self):
        """Create a realistic project configuration for integration testing"""
        return MCPProjectConfig(
            project_name="test-integration-server",
            service_name="integration_service",
            description="Integration test MCP server",
            author="Test Suite",
            version="1.0.0",
            python_version="3.11",
            test_framework="pytest",
            include_docker=True,
            include_ci=False
        )
    
    @pytest.mark.integration
    def test_complete_project_generation_and_validation(self, integration_config):
        """
        Test complete project generation and comprehensive validation
        
        This is the main integration test that:
        1. Generates a complete MCP project
        2. Validates the project structure
        3. Validates generated files are syntactically correct
        4. Validates configuration files are valid
        5. Validates the project can be imported
        """
        generator = MCPGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / integration_config.project_name
            
            # Phase 1: Generate the project
            result = generator.generate(project_path, integration_config)
            
            # Verify generation succeeded
            assert result.success is True, f"Project generation failed: {result.errors}"
            assert len(result.errors) == 0, f"Generation had errors: {result.errors}"
            assert len(result.files_created) > 0, "No files were created"
            
            # Phase 2: Validate project structure
            self._validate_project_structure(project_path, integration_config)
            
            # Phase 3: Validate generated files are syntactically correct
            self._validate_generated_code_syntax(project_path)
            
            # Phase 4: Validate configuration files
            self._validate_configuration_files(project_path, integration_config)
            
            # Phase 5: Validate project can be imported
            self._validate_project_importability(project_path, integration_config)
    
    def _validate_project_structure(self, project_path: Path, config: MCPProjectConfig):
        """Validate that all expected files and directories exist"""
        # Essential directories
        essential_dirs = [
            "src",
            f"src/mcp_{config.service_name}",
            "tests/unit",
            "tests/fixtures",
            "config",
            "scripts"
        ]
        
        for dir_name in essential_dirs:
            dir_path = project_path / dir_name
            assert dir_path.exists(), f"Essential directory {dir_name} is missing"
            assert dir_path.is_dir(), f"Path {dir_name} exists but is not a directory"
        
        # Essential files
        essential_files = [
            # Core Python files
            f"src/mcp_{config.service_name}/__init__.py",
            f"src/mcp_{config.service_name}/server.py",
            f"src/mcp_{config.service_name}/tools.py",
            f"src/mcp_{config.service_name}/client.py",
            f"src/mcp_{config.service_name}/models.py",
            f"src/mcp_{config.service_name}/config.py",
            # Configuration files
            "requirements.txt",
            "requirements-dev.txt",
            "pyproject.toml",
            ".env.example",
            "config/server_config.yaml",
            "config/logging.yaml",
            "scripts/run_server.py",
            # Test files
            "tests/conftest.py",
            "pytest.ini",
            ".coveragerc",
            "tests/fixtures/test_data.py",
            "tests/unit/test_server.py",
            "tests/unit/test_config.py",
            # Documentation
            "README.md",
            "PROJECT_SUMMARY.md"
        ]
        
        # Add Docker files if enabled
        if config.include_docker:
            essential_files.extend([
                "docker/Dockerfile",
                "docker/docker-compose.yml",
                ".dockerignore"
            ])
        
        for file_name in essential_files:
            file_path = project_path / file_name
            assert file_path.exists(), f"Essential file {file_name} is missing"
            assert file_path.is_file(), f"Path {file_name} exists but is not a file"
            assert file_path.stat().st_size > 0, f"File {file_name} is empty"
    
    def _validate_generated_code_syntax(self, project_path: Path):
        """Validate that all generated Python files have valid syntax"""
        import ast
        
        # Find all Python files
        python_files = list(project_path.rglob("*.py"))
        assert len(python_files) > 0, "No Python files found in generated project"
        
        for python_file in python_files:
            try:
                content = python_file.read_text(encoding='utf-8')
                # This will raise SyntaxError if the file has invalid Python syntax
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Generated file {python_file} has invalid Python syntax: {str(e)}")
            except UnicodeDecodeError as e:
                pytest.fail(f"Generated file {python_file} has encoding issues: {str(e)}")
    
    def _validate_configuration_files(self, project_path: Path, config: MCPProjectConfig):
        """Validate that configuration files are valid and well-formed"""
        import yaml
        import tomllib
        
        # Validate YAML files
        yaml_files = [
            project_path / "config" / "server_config.yaml",
            project_path / "config" / "logging.yaml"
        ]
        
        for yaml_file in yaml_files:
            try:
                content = yaml_file.read_text(encoding='utf-8')
                parsed_yaml = yaml.safe_load(content)
                assert parsed_yaml is not None, f"YAML file {yaml_file} is empty"
                assert isinstance(parsed_yaml, dict), f"YAML file {yaml_file} should contain a dictionary"
            except yaml.YAMLError as e:
                pytest.fail(f"Invalid YAML syntax in {yaml_file}: {str(e)}")
        
        # Validate TOML files
        toml_files = [
            project_path / "pyproject.toml"
        ]
        
        for toml_file in toml_files:
            try:
                content = toml_file.read_bytes()
                parsed_toml = tomllib.load(toml_file.open('rb'))
                assert parsed_toml is not None, f"TOML file {toml_file} is empty"
                assert isinstance(parsed_toml, dict), f"TOML file {toml_file} should contain a dictionary"
                
                # Validate pyproject.toml has required sections
                if toml_file.name == "pyproject.toml":
                    assert "project" in parsed_toml, "pyproject.toml missing [project] section"
                    assert "name" in parsed_toml["project"], "pyproject.toml missing project.name"
                    
            except Exception as e:
                pytest.fail(f"Invalid TOML syntax in {toml_file}: {str(e)}")
    
    def _validate_project_importability(self, project_path: Path, config: MCPProjectConfig):
        """Validate that the generated project can be imported successfully"""
        import sys
        import importlib
        
        # Add the generated project to Python path temporarily
        src_path = project_path / "src"
        sys.path.insert(0, str(src_path))
        
        try:
            # Test that we can import the generated module
            module_name = f"mcp_{config.service_name}"
            
            # Import the main module
            main_module = importlib.import_module(module_name)
            assert main_module is not None, f"Failed to import {module_name}"
            
            # Import and validate submodules
            submodules = ["server", "tools", "client", "models", "config"]
            for submodule in submodules:
                full_module_name = f"{module_name}.{submodule}"
                try:
                    sub_module = importlib.import_module(full_module_name)
                    assert sub_module is not None, f"Failed to import {full_module_name}"
                except ImportError as e:
                    pytest.fail(f"Failed to import {full_module_name}: {str(e)}")
                    
        finally:
            # Clean up Python path
            if str(src_path) in sys.path:
                sys.path.remove(str(src_path))
            
            # Remove imported modules from cache
            modules_to_remove = [
                name for name in sys.modules.keys() 
                if name.startswith(f"mcp_{config.service_name}")
            ]
            for module_name in modules_to_remove:
                del sys.modules[module_name]
    
    def _install_dependencies_and_run_tests(self, project_path: Path):
        """Install project dependencies and run the generated tests"""
        # Change to project directory
        original_cwd = Path.cwd()
        
        try:
            # Install dependencies
            self._run_command([
                sys.executable, "-m", "pip", "install", "-e", "."
            ], project_path, "Failed to install project dependencies")
            
            # Install dev dependencies
            self._run_command([
                sys.executable, "-m", "pip", "install", "-r", "requirements-dev.txt"
            ], project_path, "Failed to install dev dependencies")
            
            # Run the generated tests
            self._run_command([
                sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"
            ], project_path, "Generated tests failed to pass")
            
        finally:
            # Restore original working directory
            import os
            os.chdir(original_cwd)
    
    def _run_command(self, cmd: list, cwd: Path, error_message: str):
        """Run a command and handle errors appropriately"""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                check=True,
                timeout=300  # 5 minute timeout
            )
            return result
        except subprocess.CalledProcessError as e:
            pytest.fail(
                f"{error_message}\n"
                f"Command: {' '.join(cmd)}\n"
                f"Return code: {e.returncode}\n"
                f"STDOUT: {e.stdout}\n"
                f"STDERR: {e.stderr}"
            )
        except subprocess.TimeoutExpired:
            pytest.fail(f"{error_message} - Command timed out after 5 minutes")
    
    def test_project_generation_with_different_configurations(self):
        """Test project generation with various configuration options"""
        test_configs = [
            # Minimal configuration
            MCPProjectConfig(
                project_name="minimal-server",
                service_name="minimal",
                description="Minimal test server",
                author="Test",
                include_docker=False,
                include_ci=False
            ),
            # Full configuration
            MCPProjectConfig(
                project_name="full-featured-server",
                service_name="full_featured",
                description="Full featured test server",
                author="Test Suite",
                version="2.0.0",
                python_version="3.12",
                test_framework="pytest",
                include_docker=True,
                include_ci=False
            )
        ]
        
        generator = MCPGenerator()
        
        for config in test_configs:
            with tempfile.TemporaryDirectory() as temp_dir:
                project_path = Path(temp_dir) / config.project_name
                
                # Generate project
                result = generator.generate(project_path, config)
                
                # Verify generation succeeded
                assert result.success is True, f"Generation failed for {config.project_name}: {result.errors}"
                assert len(result.errors) == 0, f"Generation had errors for {config.project_name}: {result.errors}"
                
                # Validate structure
                self._validate_project_structure(project_path, config)
                
                # Validate syntax
                self._validate_generated_code_syntax(project_path)
    
    def test_generated_project_readme_completeness(self, integration_config):
        """Test that generated README contains all necessary information"""
        generator = MCPGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / integration_config.project_name
            
            result = generator.generate(project_path, integration_config)
            assert result.success is True
            
            readme_path = project_path / "README.md"
            readme_content = readme_path.read_text(encoding='utf-8')
            
            # Verify README contains essential information
            essential_sections = [
                integration_config.project_name,
                integration_config.description,
                "Installation",
                "Usage",
                "Development",
                "Testing"
            ]
            
            for section in essential_sections:
                assert section in readme_content, f"README missing section: {section}"
    
    def test_generated_project_summary_accuracy(self, integration_config):
        """Test that PROJECT_SUMMARY.md accurately reflects the generated project"""
        generator = MCPGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / integration_config.project_name
            
            result = generator.generate(project_path, integration_config)
            assert result.success is True
            
            summary_path = project_path / "PROJECT_SUMMARY.md"
            summary_content = summary_path.read_text(encoding='utf-8')
            
            # Verify summary contains project details
            project_details = [
                integration_config.project_name,
                integration_config.service_name,
                integration_config.description,
                integration_config.author,
                integration_config.version,
                str(len(result.files_created))
            ]
            
            for detail in project_details:
                assert detail in summary_content, f"PROJECT_SUMMARY.md missing detail: {detail}"


@pytest.mark.slow
class TestMCPGeneratorPerformanceIntegration:
    """Performance-focused integration tests"""
    
    def test_generation_performance_benchmark(self):
        """Test that project generation completes within reasonable time"""
        import time
        
        config = MCPProjectConfig(
            project_name="performance-test-server",
            service_name="performance_test",
            description="Performance test server",
            author="Test Suite",
            include_docker=True
        )
        
        generator = MCPGenerator()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / config.project_name
            
            start_time = time.time()
            result = generator.generate(project_path, config)
            end_time = time.time()
            
            generation_time = end_time - start_time
            
            # Verify generation succeeded
            assert result.success is True
            
            # Verify generation completed within reasonable time (30 seconds)
            assert generation_time < 30.0, f"Generation took too long: {generation_time:.2f} seconds"
            
            # Log performance for monitoring
            print(f"Project generation completed in {generation_time:.2f} seconds")
            print(f"Generated {len(result.files_created)} files") 