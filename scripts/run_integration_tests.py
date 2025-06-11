#!/usr/bin/env python3
"""
Script to run integration tests for MCP Generator

This script runs the comprehensive integration tests that generate complete
projects and validate they work correctly.
"""
import subprocess
import sys
from pathlib import Path


def main():
    """Run integration tests with appropriate settings"""
    # Change to project root directory
    project_root = Path(__file__).parent.parent
    
    # Run integration tests
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/",
        "-v",
        "--tb=long",
        "-m", "integration",
        "--durations=10",  # Show 10 slowest tests
        "--capture=no"     # Show print statements
    ]
    
    print("Running MCP Generator Integration Tests...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print("\n" + "=" * 60)
        print("✅ All integration tests passed!")
        return 0
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 60)
        print(f"❌ Integration tests failed with return code {e.returncode}")
        return e.returncode


if __name__ == "__main__":
    sys.exit(main()) 