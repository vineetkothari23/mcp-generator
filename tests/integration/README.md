# Integration Tests for MCP Generator

This directory contains comprehensive integration tests for the MCP Generator that validate end-to-end functionality.

## What These Tests Do

The integration tests perform complete project generation and validation:

1. **Generate Complete Projects** - Uses `MCPGenerator` to create full MCP server projects
2. **Validate Project Structure** - Ensures all expected files and directories are created
3. **Syntax Validation** - Verifies all generated Python code has valid syntax
4. **Dependency Installation** - Tests that generated projects can install their dependencies
5. **Test Execution** - Runs the generated tests to ensure they pass
6. **Documentation Validation** - Checks that generated documentation is complete

## Test Categories

### `TestMCPGeneratorIntegration`
- **Main Integration Test**: Complete project generation and test execution
- **Configuration Variants**: Tests different project configurations
- **Documentation Tests**: Validates README and project summary completeness

### `TestMCPGeneratorPerformanceIntegration`
- **Performance Benchmarks**: Ensures generation completes within reasonable time limits
- **Resource Usage**: Monitors generation performance

## Running Integration Tests

### Run All Integration Tests
```bash
# From project root
python -m pytest tests/integration/ -v -m integration

# Or use the convenience script
python scripts/run_integration_tests.py
```

### Run Specific Test Categories
```bash
# Run only the main integration tests
python -m pytest tests/integration/test_mcp_generator_integration.py::TestMCPGeneratorIntegration -v

# Run only performance tests
python -m pytest tests/integration/ -v -m "integration and slow"
```

### Run with Different Verbosity
```bash
# Minimal output
python -m pytest tests/integration/ -m integration -q

# Maximum output (shows all subprocess output)
python -m pytest tests/integration/ -m integration -v -s --tb=long
```

## Test Requirements

These integration tests require:
- Python 3.9+
- All project dependencies installed
- Sufficient disk space for temporary project generation
- Network access for dependency installation during tests

## Test Duration

Integration tests are slower than unit tests because they:
- Generate complete file systems
- Install Python packages
- Run subprocess commands
- Execute generated test suites

Typical execution times:
- **Main Integration Test**: 30-60 seconds
- **Configuration Variants**: 60-120 seconds  
- **Performance Tests**: 10-30 seconds

## Troubleshooting

### Common Issues

**Test Timeout**: If tests timeout, check:
- Network connectivity for package installation
- Available disk space
- System performance

**Import Errors**: If generated projects can't be imported:
- Check that all templates are present
- Verify template syntax is correct
- Ensure generated Python code is valid

**Test Failures**: If generated tests fail:
- Check generated test files for syntax errors
- Verify test dependencies are correctly specified
- Review generated project structure

### Debug Mode

Run with maximum verbosity to debug issues:
```bash
python -m pytest tests/integration/ -v -s --tb=long --capture=no -m integration
```

## CI/CD Integration

For continuous integration, consider:
- Running integration tests on a schedule rather than every commit
- Using test result caching to avoid redundant runs
- Separating fast unit tests from slower integration tests

Example CI configuration:
```yaml
# Run unit tests on every commit
- name: Unit Tests
  run: python -m pytest tests/unit/ -v

# Run integration tests on main branch only
- name: Integration Tests  
  if: github.ref == 'refs/heads/main'
  run: python scripts/run_integration_tests.py
``` 