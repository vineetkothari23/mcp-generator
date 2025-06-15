#!/usr/bin/env python3
"""
Blog API Client Generator Script

Generates a Python client for the blog API using openapi-generator-cli.
This script wraps the CLI command in a Python subprocess for better control and error handling.
"""

import subprocess
import sys
from pathlib import Path
import time


def generate_blog_api_client():
    """
    Generate Python client for the blog API using openapi-generator-cli
    
    Uses the specific paths and configuration for the content-autopilot project.
    
    Returns:
        bool: True if generation succeeded, False otherwise
    """
    
    # Define the command components
    input_spec = r"C:\Users\vinee\OneDrive\Documents\Projects\content-autopilot\blog-api-spec.yaml"
    output_dir = r"C:\Users\vinee\OneDrive\Documents\Projects\content-autopilot"
    generator = "python"
    package_name = "lynnx_blog_client"
    
    # Build the command
    cmd = [
        "openapi-generator-cli",
        "generate",
        "-i", input_spec,
        "-o", output_dir, 
        "-g", generator,
        "--package-name", package_name
    ]
    
    print("🚀 Starting blog API client generation...")
    print(f"📁 Input spec: {input_spec}")
    print(f"📂 Output dir: {output_dir}")
    print(f"📦 Package name: {package_name}")
    print(f"⚙️  Generator: {generator}")
    print()
    
    # Verify input file exists
    if not Path(input_spec).exists():
        print(f"❌ Error: Input spec file not found: {input_spec}")
        return False
    
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    try:
        start_time = time.time()
        
        print("🔧 Running openapi-generator-cli...")
        print(f"Command: {' '.join(cmd)}")
        print()
        
        # Run the command with real-time output
        result = subprocess.run(
            cmd,
            capture_output=False,  # Show output in real-time
            text=True,
            shell=True,  # Required on Windows
            timeout=300  # 5-minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ Client generation completed successfully in {duration:.1f} seconds!")
            
            # Show what was created
            client_dir = Path(output_dir) / package_name
            if client_dir.exists():
                python_files = list(client_dir.rglob("*.py"))
                print(f"📊 Generated {len(python_files)} Python files")
                
                # Show key files
                key_files = ["__init__.py", "api_client.py", "configuration.py"]
                print("📋 Key files created:")
                for key_file in key_files:
                    file_path = client_dir / key_file
                    if file_path.exists():
                        print(f"   ✓ {key_file}")
                    else:
                        print(f"   ⚠ {key_file} (not found)")
            
            return True
            
        else:
            print(f"❌ Client generation failed with return code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⏰ Error: Command timed out after 5 minutes")
        return False
        
    except FileNotFoundError:
        print("❌ Error: openapi-generator-cli not found")
        print("💡 Make sure openapi-generator-cli is installed and in your PATH")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def verify_openapi_generator_available():
    """
    Check if openapi-generator-cli is available
    
    Returns:
        bool: True if CLI is available, False otherwise
    """
    try:
        result = subprocess.run(
            ["openapi-generator-cli", "version"],
            capture_output=True,
            text=True,
            shell=True,
            timeout=10
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"✅ openapi-generator-cli found (version: {version})")
            return True
        else:
            return False
            
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def main():
    """Main function to run the client generation"""
    
    print("=" * 60)
    print("🔧 Blog API Client Generator")
    print("=" * 60)
    print()
    
    # Check if openapi-generator-cli is available
    if not verify_openapi_generator_available():
        print("❌ openapi-generator-cli is not available")
        print("📖 Please install it from: https://openapi-generator.tech/docs/installation")
        sys.exit(1)
    
    print()
    
    # Generate the client
    success = generate_blog_api_client()
    
    print()
    print("=" * 60)
    
    if success:
        print("🎉 Blog API client generation completed successfully!")
        print()
        print("📝 Next steps:")
        print("   1. Navigate to the generated client directory")
        print("   2. Install dependencies: pip install -r requirements.txt")
        print("   3. Import and use: from lynnx_blog_client import ApiClient")
    else:
        print("💥 Blog API client generation failed!")
        print("🔍 Check the error messages above for details")
        sys.exit(1)


if __name__ == "__main__":
    main() 