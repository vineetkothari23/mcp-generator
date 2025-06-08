"""
MCP CLI Tool Setup Configuration

This setup file configures the MCP CLI tool for installation and distribution.
The tool provides commands to initialize and generate MCP servers from templates
or OpenAPI specifications.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read version from __init__.py
def get_version():
    init_file = Path(__file__).parent / "mcp_cli" / "__init__.py"
    with open(init_file, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                return line.split('=')[1].strip().strip('"').strip("'")
    return "0.1.0"

# Read long description from README
def get_long_description():
    readme_file = Path(__file__).parent / "README.md"
    if readme_file.exists():
        with open(readme_file, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name="mcp-cli",
    version=get_version(),
    description="CLI tool for generating MCP (Model Context Protocol) servers",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="AI Development Team",
    author_email="dev@example.com",
    url="https://github.com/vineetkothari23/mcp-generator",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "mcp_cli": [
            "templates/**/*",
            "templates/**/**/*",
        ]
    },
    install_requires=[
        "click>=8.0.0",
        "jinja2>=3.0.0",
        "pydantic>=2.0.0",
        "PyYAML>=6.0",
        "requests>=2.28.0",
        "tomli>=2.0.0",
        "packaging>=21.0",
        "httpx>=0.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "pre-commit>=2.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "mcp-cli=mcp_cli.cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    keywords="mcp model-context-protocol openapi code-generation cli",
) 