# MCP CLI - Model Context Protocol Server Generator

A powerful command-line tool for generating production-ready MCP (Model Context Protocol) servers from templates or OpenAPI specifications. Built with a test-first approach and designed for easy deployment and maintenance.

## 🚀 Features

- **Quick Project Initialization**: Generate complete MCP server projects in seconds
- **OpenAPI Integration**: Automatically convert OpenAPI specs to MCP servers
- **Test-First Development**: Comprehensive test suites generated automatically
- **Docker Ready**: Production-ready containerization included
- **Configuration Driven**: Easily customizable through YAML configuration
- **Quality Assurance**: Built-in validation and linting
- **Modular Architecture**: Clean, maintainable code structure

## 📦 Installation

### From PyPI (Recommended)
```bash
pip install mcp-cli
```

### From Source
```bash
git clone https://github.com/your-org/mcp-cli.git
cd mcp-cli
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/your-org/mcp-cli.git
cd mcp-cli
pip install -e ".[dev]"
```

## ⚡ Prerequisites

### OpenAPI Generator CLI (Required for `from-openapi` command)

The `mcp-cli from-openapi` command requires the OpenAPI Generator CLI tool to be installed on your system. Follow the instructions below for your operating system:

#### macOS

**Option 1: Using Homebrew (Recommended)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install OpenAPI Generator
brew install openapi-generator
```

**Option 2: Using npm**
```bash
# Install Node.js if not already installed
brew install node

# Install OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli
```

#### Linux (Ubuntu/Debian)

**Option 1: Using npm (Recommended)**
```bash
# Install Node.js and npm
sudo apt update
sudo apt install nodejs npm

# Install OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli
```

**Option 2: Using snap**
```bash
# Install via snap
sudo snap install openapi-generator
```

**Option 3: Manual installation**
```bash
# Download the JAR file (requires Java 8+)
# First install Java if not present
sudo apt install openjdk-11-jre-headless

# Download OpenAPI Generator
wget https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.0.1/openapi-generator-cli-7.0.1.jar -O openapi-generator-cli.jar

# Make it executable and move to PATH
sudo mv openapi-generator-cli.jar /usr/local/bin/
echo 'alias openapi-generator-cli="java -jar /usr/local/bin/openapi-generator-cli.jar"' >> ~/.bashrc
source ~/.bashrc
```

#### Linux (CentOS/RHEL/Fedora)

**Option 1: Using npm**
```bash
# Install Node.js and npm (Fedora)
sudo dnf install nodejs npm

# Install Node.js and npm (CentOS/RHEL - requires EPEL)
sudo yum install epel-release
sudo yum install nodejs npm

# Install OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli
```

**Option 2: Manual installation**
```bash
# Install Java if not present
sudo dnf install java-11-openjdk  # Fedora
# OR
sudo yum install java-11-openjdk  # CentOS/RHEL

# Download and setup OpenAPI Generator
wget https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.0.1/openapi-generator-cli-7.0.1.jar -O openapi-generator-cli.jar
sudo mv openapi-generator-cli.jar /usr/local/bin/
echo 'alias openapi-generator-cli="java -jar /usr/local/bin/openapi-generator-cli.jar"' >> ~/.bashrc
source ~/.bashrc
```

#### Windows

**Option 1: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey if not already installed
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install OpenAPI Generator
choco install openapi-generator-cli
```

**Option 2: Using npm**
```powershell
# Install Node.js from https://nodejs.org/en/download/ if not already installed
# Then install OpenAPI Generator CLI
npm install -g @openapitools/openapi-generator-cli
```

**Option 3: Using Scoop**
```powershell
# Install Scoop if not already installed
iwr -useb get.scoop.sh | iex

# Install OpenAPI Generator
scoop install openapi-generator
```

**Option 4: Manual installation**
```powershell
# Download Java if not present (from https://adoptium.net/)
# Download OpenAPI Generator JAR
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.0.1/openapi-generator-cli-7.0.1.jar" -OutFile "openapi-generator-cli.jar"

# Move to a permanent location (e.g., C:\tools\)
New-Item -ItemType Directory -Force -Path C:\tools
Move-Item openapi-generator-cli.jar C:\tools\

# Add to PATH and create alias (add to PowerShell profile)
$profile_path = $PROFILE
if (!(Test-Path $profile_path)) { New-Item -ItemType File -Force -Path $profile_path }
Add-Content $profile_path 'function openapi-generator-cli { java -jar C:\tools\openapi-generator-cli.jar $args }'
```

#### Docker Alternative (All Platforms)

If you prefer using Docker and don't want to install OpenAPI Generator directly:

```bash
# Create an alias for the Docker version
# Linux/macOS
echo 'alias openapi-generator-cli="docker run --rm -v ${PWD}:/local openapitools/openapi-generator-cli"' >> ~/.bashrc
source ~/.bashrc

# Windows PowerShell
Add-Content $PROFILE 'function openapi-generator-cli { docker run --rm -v ${PWD}:/local openapitools/openapi-generator-cli $args }'
```

#### Verify Installation

After installation, verify that OpenAPI Generator is working:

```bash
openapi-generator-cli version
```

You should see output similar to:
```
openapi-generator-cli 7.0.1
  commit : 40cf523
  built  : 2023-08-11T07:47:21.337138706Z
  source : https://github.com/openapitools/openapi-generator
  docs   : https://openapi-generator.tech/
```

## 🎯 Quick Start

### Initialize a Standard MCP Server
```bash
# Create a new MCP server project
mcp-cli init --name "weather-api" --author "Your Name"

# Navigate to the project
cd weather-api

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start the server
python scripts/run_server.py
```

### Generate from OpenAPI Specification
**Note**: Requires OpenAPI Generator CLI (see [Prerequisites](#prerequisites))

```bash
# From URL
mcp-cli from-openapi --spec https://api.example.com/openapi.json

# From local file
mcp-cli from-openapi --spec ./api-spec.yaml --name "my-api-server"

# With examples and documentation
mcp-cli from-openapi --spec ./api-spec.yaml --include-examples --max-tools 25
```

### Validate Projects
```bash
# Validate OpenAPI specification
mcp-cli analyze --spec ./api-spec.yaml --format yaml

# Validate existing project
mcp-cli validate --project-dir ./my-mcp-server
```

## 📚 Commands

### `mcp-cli init`
Initialize a new MCP server project with standard structure.

**Options:**
- `--name, -n`: Project name (required)
- `--description, -d`: Project description
- `--author, -a`: Author name
- `--output-dir, -o`: Output directory (default: current directory)
- `--python-version`: Python version (default: 3.11)
- `--no-docker`: Skip Docker setup
- `--no-ci`: Skip CI/CD setup
- `--test-framework`: Testing framework (default: pytest)

**Example:**
```bash
mcp-cli init \
  --name "social-media-api" \
  --description "MCP server for social media management" \
  --author "Jane Developer" \
  --python-version "3.12"
```

### `mcp-cli from-openapi`
Generate MCP server from OpenAPI specification.

**Prerequisites**: Requires OpenAPI Generator CLI to be installed (see [Prerequisites](#prerequisites))

**Options:**
- `--spec, -s`: OpenAPI spec file path or URL (required)
- `--name, -n`: Project name (auto-generated if not provided)
- `--output-dir, -o`: Output directory
- `--author, -a`: Author name
- `--validate-only`: Only validate the specification
- `--include-examples`: Generate usage examples
- `--max-tools`: Maximum number of tools to generate (default: 50)

**Example:**
```bash
mcp-cli from-openapi \
  --spec https://petstore3.swagger.io/api/v3/openapi.json \
  --name "petstore-mcp" \
  --include-examples \
  --max-tools 30
```

### `mcp-cli analyze`
Analyze OpenAPI specification and show generation plan.

**Options:**
- `--spec, -s`: OpenAPI spec file path or URL (required)
- `--output, -o`: Output file (default: stdout)
- `--format`: Output format - json or yaml (default: json)

**Example:**
```bash
mcp-cli analyze --spec ./api-spec.yaml --format yaml --output analysis.yaml
```

### `mcp-cli validate`
Validate existing MCP server project structure.

**Options:**
- `--project-dir, -p`: Project directory to validate (default: current directory)

**Example:**
```bash
mcp-cli validate --project-dir ./my-mcp-server
```

## 🏗️ Project Structure

Generated projects follow a standardized structure:

```
my-mcp-server/
├── src/
│   └── mcp_my_service/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # Main MCP server implementation
│       ├── client.py            # API client wrapper
│       ├── models.py            # Pydantic data models
│       ├── tools.py             # MCP tool definitions
│       ├── resources.py         # MCP resource definitions
│       └── config.py            # Configuration management
├── tests/
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   ├── fixtures/                # Test data and fixtures
│   └── conftest.py              # Pytest configuration
├── docker/
│   ├── Dockerfile               # Docker container definition
│   └── docker-compose.yml       # Docker Compose configuration
├── config/
│   ├── server_config.yaml       # Server configuration
│   ├── api_config.yaml          # API-specific configuration
│   └── logging.yaml             # Logging configuration
├── scripts/
│   ├── run_server.py            # Server startup script
│   └── deploy.sh                # Deployment script
├── docs/
│   ├── API_REFERENCE.md         # Generated API documentation
│   ├── USAGE_EXAMPLES.md        # Usage examples
│   └── DEPLOYMENT.md            # Deployment instructions
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml               # Project configuration
├── .env.example                 # Environment variables template
├── .dockerignore                # Docker ignore file
└── README.md                    # Project documentation
```

## ⚙️ Configuration

### Environment Variables
```bash
# API Configuration
MCP_API_BASE_URL=https://api.example.com
MCP_API_KEY=your-api-key
MCP_TIMEOUT=30

# Server Configuration
MCP_SERVER_NAME=my-mcp-server
MCP_MAX_TOOLS=50
MCP_ENABLE_RESOURCES=true

# Development
MCP_LOG_LEVEL=DEBUG
MCP_ENABLE_CORS=true
```

### Configuration Files

**config/server_config.yaml**
```yaml
server:
  name: "my-mcp-server"
  version: "1.0.0"
  description: "My MCP server description"

api:
  base_url: "https://api.example.com"
  timeout: 30
  retry_attempts: 3

mcp:
  max_tools: 50
  enable_resources: true
  enable_logging: true
```

## 🧪 Testing

All generated projects include comprehensive test suites:

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=src --cov-report=html

# Run specific test types
python -m pytest tests/unit/          # Unit tests only
python -m pytest tests/integration/   # Integration tests only

# Run with verbose output
python -m pytest -v --tb=short
```

## 🐳 Docker Deployment

Generated projects include Docker support:

```bash
# Build the container
docker build -f docker/Dockerfile -t my-mcp-server .

# Run with Docker Compose
docker-compose -f docker/docker-compose.yml up

# Run standalone container
docker run -p 8080:8080 --env-file .env my-mcp-server
```

## 🔧 Development

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/your-org/mcp-cli.git
cd mcp-cli

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
python -m pytest tests/
```

### Adding New Templates

1. Create template files in `mcp_cli/templates/`
2. Update the appropriate generator in `mcp_cli/generators.py`
3. Add tests for the new template
4. Update documentation

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Run the test suite (`python -m pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📖 Examples

### Basic Weather API MCP Server
```bash
mcp-cli init --name "weather-mcp" --description "Weather data MCP server"
```

### E-commerce API from OpenAPI
```bash
mcp-cli from-openapi \
  --spec https://api.shop.com/openapi.json \
  --name "shop-mcp" \
  --include-examples
```

### Social Media Management Server
```bash
mcp-cli init \
  --name "social-media-mcp" \
  --description "Social media management MCP server" \
  --author "Social Team"
```

## 🐛 Troubleshooting

### Common Issues

**"Command not found: mcp-cli"**
```bash
# Ensure the package is installed
pip install mcp-cli

# Check if it's in PATH
which mcp-cli

# Try running with python -m
python -m mcp_cli.cli --help
```

**"Command not found: openapi-generator-cli"**
```bash
# Check if OpenAPI Generator is installed
openapi-generator-cli version

# If not installed, follow the Prerequisites section
# https://github.com/your-org/mcp-cli#prerequisites

# For Docker users
docker run --rm openapitools/openapi-generator-cli version
```

**"OpenAPI validation failed"**
```bash
# Validate your spec first
mcp-cli analyze --spec your-spec.yaml

# Check for common issues:
# - Missing required fields
# - Invalid URLs
# - Malformed YAML/JSON
```

**"Tests failing after generation"**
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Check Python version compatibility
python --version  # Should be 3.11+

# Run tests with verbose output
python -m pytest -v
```

**"Java not found" (when using manual OpenAPI Generator installation)**
```bash
# Install Java 8 or later
# Ubuntu/Debian: sudo apt install openjdk-11-jre-headless
# macOS: brew install openjdk@11
# Windows: Download from https://adoptium.net/

# Verify Java installation
java -version
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Support

- **Documentation**: [Project Wiki](https://github.com/your-org/mcp-cli/wiki)
- **Issues**: [GitHub Issues](https://github.com/your-org/mcp-cli/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/mcp-cli/discussions)

## 🗺️ Roadmap

- [ ] Support for additional API specifications (GraphQL, gRPC)
- [ ] Interactive project setup wizard
- [ ] Plugin system for custom generators
- [ ] Integration with popular IDEs
- [ ] Advanced monitoring and observability features
- [ ] Support for multiple MCP protocol versions

## 🙏 Acknowledgments

- [Model Context Protocol](https://github.com/anthropics/mcp) - Core protocol specification
- [LangChain](https://github.com/langchain-ai/langchain) - AI framework inspiration
- [Click](https://click.palletsprojects.com/) - Command-line interface framework
- [Jinja2](https://jinja.palletsprojects.com/) - Template engine

---

**Built with ❤️ for the MCP community**