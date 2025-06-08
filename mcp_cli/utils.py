"""
MCP CLI Utilities - Helper functions for project generation and management

This module provides common utilities used throughout the MCP CLI tool:
- Logging setup and configuration
- File system operations
- Template processing helpers
- Development environment setup

All utilities follow consistent error handling patterns and provide
detailed logging for debugging and monitoring.
"""

import os
import sys
import logging
import subprocess
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import tempfile
import zipfile
import tarfile

def setup_logging(level: str = "INFO") -> logging.Logger:
    """
    Setup logging configuration for MCP CLI
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        
    Returns:
        logging.Logger: Configured logger instance
        
    Example:
        logger = setup_logging("DEBUG")
        logger.info("Starting MCP CLI operation")
    """
    logger = logging.getLogger("mcp-cli")
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Set level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(numeric_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    return logger

def create_directory_structure(base_path: Path, structure: Dict[str, Any]) -> List[str]:
    """
    Create directory structure from nested dictionary
    
    Args:
        base_path: Base directory path
        structure: Nested dictionary representing directory structure
        
    Returns:
        List[str]: List of created directories
        
    Example:
        structure = {
            "src": {
                "mcp_service": {},
                "tests": {"unit": {}, "integration": {}}
            }
        }
        created = create_directory_structure(Path("./project"), structure)
    """
    created_dirs = []
    
    def _create_recursive(current_path: Path, current_structure: Dict[str, Any]):
        for name, content in current_structure.items():
            dir_path = current_path / name
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            
            if isinstance(content, dict):
                _create_recursive(dir_path, content)
    
    _create_recursive(base_path, structure)
    return created_dirs

def copy_template_files(template_dir: Path, target_dir: Path, 
                       file_mapping: Dict[str, str]) -> List[str]:
    """
    Copy template files to target directory with renaming
    
    Args:
        template_dir: Source template directory
        target_dir: Target directory for copied files
        file_mapping: Dictionary mapping source files to target names
        
    Returns:
        List[str]: List of copied files
        
    Example:
        mapping = {
            "server.py.template": "server.py",
            "config.yaml.template": "config.yaml"
        }
        copied = copy_template_files(template_dir, target_dir, mapping)
    """
    copied_files = []
    
    for source_file, target_file in file_mapping.items():
        source_path = template_dir / source_file
        target_path = target_dir / target_file
        
        if source_path.exists():
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            copied_files.append(str(target_path))
    
    return copied_files

def install_dependencies(project_path: Path, requirements_file: str = "requirements-dev.txt") -> bool:
    """
    Install project dependencies using pip
    
    Args:
        project_path: Project directory path
        requirements_file: Requirements file name
        
    Returns:
        bool: True if installation successful, False otherwise
        
    Example:
        success = install_dependencies(Path("./my-project"))
        if success:
            print("Dependencies installed successfully")
    """
    requirements_path = project_path / requirements_file
    
    if not requirements_path.exists():
        return False
    
    try:
        # Run pip install in the project directory
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        return False
    except Exception:
        return False

def run_initial_tests(project_path: Path) -> tuple[bool, str]:
    """
    Run initial test suite for generated project
    
    Args:
        project_path: Project directory path
        
    Returns:
        tuple[bool, str]: (success, output) - Success status and test output
        
    Example:
        success, output = run_initial_tests(Path("./my-project"))
        if success:
            print("All tests passed!")
        else:
            print(f"Tests failed: {output}")
    """
    try:
        # Check if pytest is available and tests directory exists
        tests_dir = project_path / "tests"
        if not tests_dir.exists():
            return False, "No tests directory found"
        
        # Run pytest
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-v"],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        return result.returncode == 0, result.stdout + result.stderr
        
    except subprocess.TimeoutExpired:
        return False, "Tests timed out"
    except Exception as e:
        return False, f"Error running tests: {str(e)}"

def validate_python_version(required_version: str = "3.11") -> bool:
    """
    Validate that current Python version meets requirements
    
    Args:
        required_version: Minimum required Python version
        
    Returns:
        bool: True if version is sufficient, False otherwise
        
    Example:
        if validate_python_version("3.11"):
            print("Python version is compatible")
    """
    import sys
    from packaging import version
    
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    
    try:
        return version.parse(current_version) >= version.parse(required_version)
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing/replacing invalid characters
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename safe for filesystem
        
    Example:
        safe_name = sanitize_filename("my file!@#$%.txt")
        # Returns: "my_file___.txt"
    """
    import string
    
    # Define valid characters
    valid_chars = f"-_.() {string.ascii_letters}{string.digits}"
    
    # Replace invalid characters with underscore
    sanitized = ''.join(c if c in valid_chars else '_' for c in filename)
    
    # Remove multiple consecutive underscores
    while '__' in sanitized:
        sanitized = sanitized.replace('__', '_')
    
    # Remove leading/trailing underscores and spaces
    sanitized = sanitized.strip('_ ')
    
    return sanitized or "unnamed"

def extract_archive(archive_path: Path, extract_to: Path) -> bool:
    """
    Extract archive file (zip, tar.gz, tar.bz2) to directory
    
    Args:
        archive_path: Path to archive file
        extract_to: Directory to extract to
        
    Returns:
        bool: True if extraction successful, False otherwise
        
    Example:
        success = extract_archive(Path("./template.zip"), Path("./extracted"))
    """
    try:
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive_path.suffix.lower() == '.zip':
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_to)
                
        elif archive_path.suffix.lower() in ['.tar', '.gz', '.bz2']:
            with tarfile.open(archive_path, 'r:*') as tar_ref:
                tar_ref.extractall(extract_to)
                
        else:
            return False
        
        return True
        
    except Exception:
        return False

def get_project_metadata(project_path: Path) -> Optional[Dict[str, Any]]:
    """
    Extract metadata from existing MCP project
    
    Args:
        project_path: Project directory path
        
    Returns:
        Optional[Dict[str, Any]]: Project metadata or None if not found
        
    Example:
        metadata = get_project_metadata(Path("./my-project"))
        if metadata:
            print(f"Project: {metadata['name']} v{metadata['version']}")
    """
    try:
        # Try pyproject.toml first
        pyproject_path = project_path / "pyproject.toml"
        if pyproject_path.exists():
            import tomli
            with open(pyproject_path, 'rb') as f:
                data = tomli.load(f)
                project_data = data.get('project', {})
                return {
                    'name': project_data.get('name'),
                    'version': project_data.get('version'),
                    'description': project_data.get('description'),
                    'source': 'pyproject.toml'
                }
        
        # Fallback to package __init__.py
        src_dirs = list(project_path.glob("src/mcp_*"))
        for src_dir in src_dirs:
            init_path = src_dir / "__init__.py"
            if init_path.exists():
                with open(init_path, 'r') as f:
                    content = f.read()
                    
                # Extract version and other metadata using regex
                import re
                version_match = re.search(r'__version__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                name_match = re.search(r'__name__\s*=\s*[\'"]([^\'"]+)[\'"]', content)
                
                return {
                    'name': name_match.group(1) if name_match else src_dir.name,
                    'version': version_match.group(1) if version_match else '0.1.0',
                    'description': None,
                    'source': '__init__.py'
                }
        
        return None
        
    except Exception:
        return None

def check_port_available(port: int, host: str = "localhost") -> bool:
    """
    Check if a port is available for binding
    
    Args:
        port: Port number to check
        host: Host address to check
        
    Returns:
        bool: True if port is available, False otherwise
        
    Example:
        if check_port_available(8080):
            print("Port 8080 is available")
    """
    import socket
    
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            return result != 0  # Port is available if connection fails
            
    except Exception:
        return False

def generate_requirements_from_imports(source_dir: Path) -> List[str]:
    """
    Generate requirements list by analyzing import statements
    
    Args:
        source_dir: Directory containing Python source files
        
    Returns:
        List[str]: List of detected package requirements
        
    Example:
        requirements = generate_requirements_from_imports(Path("./src"))
        print("\\n".join(requirements))
    """
    import ast
    
    detected_packages = set()
    standard_library = {
        'os', 'sys', 'json', 'yaml', 'pathlib', 'typing', 'dataclasses',
        'logging', 'subprocess', 'shutil', 'tempfile', 'zipfile', 'tarfile',
        'socket', 'ast', 're', 'string', 'time', 'datetime', 'uuid', 'hashlib'
    }
    
    # Common package mappings
    package_mappings = {
        'yaml': 'PyYAML',
        'requests': 'requests',
        'httpx': 'httpx',
        'pydantic': 'pydantic',
        'click': 'click',
        'jinja2': 'Jinja2',
        'mcp': 'mcp',
        'tomli': 'tomli',
        'packaging': 'packaging'
    }
    
    try:
        for py_file in source_dir.rglob("*.py"):
            with open(py_file, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read())
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                package = alias.name.split('.')[0]
                                if package not in standard_library:
                                    detected_packages.add(package)
                                    
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                package = node.module.split('.')[0]
                                if package not in standard_library:
                                    detected_packages.add(package)
                                    
                except SyntaxError:
                    continue  # Skip files with syntax errors
    
    except Exception:
        pass
    
    # Map to actual package names
    requirements = []
    for package in detected_packages:
        actual_package = package_mappings.get(package, package)
        requirements.append(actual_package)
    
    return sorted(requirements) 