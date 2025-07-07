#!/usr/bin/env python3
"""
Deployment Verification Script

This script helps diagnose deployment issues by checking:
- Python environment
- Installed packages
- File system access
- Environment variables
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_environment():
    """Check Python environment details."""
    print("🐍 Python Environment Check")
    print("=" * 40)
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Python path: {sys.path[:3]}...")  # Show first 3 entries
    print(f"Current working directory: {os.getcwd()}")
    print(f"Platform: {sys.platform}")
    print()

def check_installed_packages():
    """Check installed packages."""
    print("📦 Installed Packages Check")
    print("=" * 40)
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pip", "list"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ pip list command successful")
            # Show key packages
            lines = result.stdout.split('\n')
            key_packages = ['quart', 'aiosqlite', 'pydantic', 'playwright', 'hypercorn']
            for line in lines:
                for pkg in key_packages:
                    if pkg.lower() in line.lower():
                        print(f"  {line.strip()}")
        else:
            print(f"❌ pip list failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error running pip list: {e}")
    print()

def check_file_system():
    """Check file system access and key files."""
    print("📁 File System Check")
    print("=" * 40)
    
    key_files = [
        "requirements.txt",
        "start_production.py",
        "railway.json",
        "nixpacks.toml"
    ]
    
    key_dirs = [
        "src",
        "data",
        "logs",
        "output"
    ]
    
    print("Checking key files:")
    for file in key_files:
        if Path(file).exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
    
    print("\nChecking key directories:")
    for dir_name in key_dirs:
        if Path(dir_name).exists():
            print(f"  ✅ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ - MISSING")
    print()

def check_environment_variables():
    """Check environment variables."""
    print("🔧 Environment Variables Check")
    print("=" * 40)
    
    key_vars = [
        "ENVIRONMENT",
        "USE_MOCK_DATA",
        "HOST",
        "PORT",
        "PYTHONPATH",
        "RAILWAY_ENVIRONMENT",
        "RAILWAY_PROJECT_ID"
    ]
    
    for var in key_vars:
        value = os.environ.get(var, "NOT SET")
        print(f"  {var}: {value}")
    print()

def check_dependencies():
    """Check specific dependencies."""
    print("🔍 Dependency Check")
    print("=" * 40)
    
    dependencies = {
        "quart": "Web framework",
        "aiosqlite": "Database",
        "pydantic": "Data validation",
        "playwright": "Browser automation",
        "hypercorn": "ASGI server",
        "sqlmodel": "Database ORM"
    }
    
    for dep, description in dependencies.items():
        try:
            module = __import__(dep)
            version = getattr(module, '__version__', 'unknown')
            print(f"  ✅ {description}: {dep} (v{version})")
        except ImportError as e:
            print(f"  ❌ {description}: {dep} - {e}")
    print()

def check_requirements_installation():
    """Check if requirements.txt can be installed."""
    print("📋 Requirements Installation Check")
    print("=" * 40)
    
    if not Path("requirements.txt").exists():
        print("  ❌ requirements.txt not found")
        return
    
    try:
        print("  🔄 Attempting to install requirements.txt...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("  ✅ Requirements installed successfully")
        else:
            print(f"  ❌ Requirements installation failed:")
            print(f"     {result.stderr}")
    except Exception as e:
        print(f"  ❌ Error during installation: {e}")
    print()

def main():
    """Run all verification checks."""
    print("🚀 DEPLOYMENT VERIFICATION")
    print("=" * 60)
    print()
    
    check_python_environment()
    check_file_system()
    check_environment_variables()
    check_installed_packages()
    check_dependencies()
    check_requirements_installation()
    
    print("=" * 60)
    print("✅ Verification complete")
    print("📝 Check the output above for any issues")

if __name__ == "__main__":
    main() 