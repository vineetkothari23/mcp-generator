# lynnx-blog-mcp-server - Project Summary

## Project Information
- **Project Name**: lynnx-blog-mcp-server
- **Service Name**: lynnx_blog_mcp_server
- **Description**: API for managing blog posts, including comments and user interactions
- **Author**: Developer
- **Version**: 1.0.0
- **Python Version**: 3.11
- **Test Framework**: pytest

## Generation Configuration
- **Docker Support**: Enabled
- **CI/CD Support**: Enabled

## Generated Files
This project was generated with **24** files:

- `__init__.py`
- `server.py`
- `config.py`
- `models.py`
- `client.py`
- `tools.py`
- `requirements.txt`
- `requirements-dev.txt`
- `pyproject.toml`
- `.env.example`
- `README.md`
- `server_config.yaml`
- `logging.yaml`
- `run_server.py`
- `conftest.py`
- `pytest.ini`
- `.coveragerc`
- `test_data.py`
- `test_server.py`
- `test_config.py`
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`

## Project Structure
```
lynnx-blog-mcp-server/
├── src/
│   └── mcp_lynnx_blog_mcp_server/
│       ├── __init__.py
│       ├── server.py          # Main MCP server implementation
│       ├── tools.py           # MCP tools and functions
│       ├── client.py          # API client implementation
│       ├── models.py          # Data models
│       └── config.py          # Configuration management
├── tests/
│   ├── unit/                  # Unit tests
│   ├── fixtures/              # Test fixtures and data
│   └── conftest.py            # Pytest configuration
├── config/
│   ├── server_config.yaml     # Server configuration
│   └── logging.yaml           # Logging configuration
├── scripts/
│   └── run_server.py          # Server startup script
├── docker/
│   ├── Dockerfile             # Docker container definition
│   └── docker-compose.yml     # Docker Compose configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml             # Project configuration
├── pytest.ini                # Test configuration
├── .coveragerc                # Coverage configuration
├── .env.example               # Environment variables template
├── .dockerignore              # Docker ignore patterns
└── README.md                  # Project documentation
```

## Getting Started

### Installation
```bash
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running the Server
```bash
# Using the startup script
python scripts/run_server.py

# Or directly
python -m mcp_lynnx_blog_mcp_server.server
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_lynnx_blog_mcp_server

# Run specific test categories
pytest tests/unit/
```

### Docker Deployment
```bash
# Build and run with Docker Compose
cd docker/
docker-compose up --build

# Or build manually
docker build -t lynnx-blog-mcp-server -f docker/Dockerfile .
docker run -p 8000:8000 lynnx-blog-mcp-server
```

## Development

### Project Configuration
The project uses `pyproject.toml` for configuration and dependency management. Key settings include:
- Python version requirement: 3.11+
- Test framework: pytest
- Package structure: `src/mcp_lynnx_blog_mcp_server/`

### Adding New Tools
1. Define new tool functions in `src/mcp_lynnx_blog_mcp_server/tools.py`
2. Register tools in the MCP server (`src/mcp_lynnx_blog_mcp_server/server.py`)
3. Add corresponding tests in `tests/unit/`
4. Update documentation as needed

### Configuration Management
- Server settings: `config/server_config.yaml`
- Logging configuration: `config/logging.yaml`
- Environment variables: `.env` (copy from `.env.example`)

---

*This project was generated using MCP Generator* 