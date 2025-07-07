#!/usr/bin/env python3
"""
Deployment Readiness Check

Verifies that all files are properly configured for Railway deployment.
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if a file exists and report status."""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} (MISSING)")
        return False

def check_file_content(filepath, required_content, description):
    """Check if file contains required content."""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
            if required_content in content:
                print(f"✅ {description}: Contains required configuration")
                return True
            else:
                print(f"⚠️  {description}: Missing required content")
                return False
    except FileNotFoundError:
        print(f"❌ {description}: File not found")
        return False

def main():
    """Run deployment readiness check."""
    print("🚀 Railway Deployment Readiness Check")
    print("=" * 50)
    
    all_good = True
    
    # Check required files
    print("\n📁 Required Files:")
    all_good &= check_file_exists("requirements.txt", "Dependencies file")
    all_good &= check_file_exists("railway.json", "Railway configuration")
    all_good &= check_file_exists("Procfile", "Process definition")
    all_good &= check_file_exists(".railwayignore", "Ignore file")
    all_good &= check_file_exists("main.py", "Application entry point")
    
    # Check main application files
    print("\n🏗️  Application Structure:")
    all_good &= check_file_exists("src/presentation/web_app.py", "Web application")
    all_good &= check_file_exists("src/infrastructure/dependency_injection.py", "Dependency injection")
    all_good &= check_file_exists("config/simple_settings.py", "Configuration")
    
    # Check file contents
    print("\n📝 Configuration Contents:")
    all_good &= check_file_content("main.py", "ENVIRONMENT", "Environment detection")
    all_good &= check_file_content("main.py", "hypercorn", "Production server support")
    all_good &= check_file_content("railway.json", "startCommand", "Railway start command")
    all_good &= check_file_content("Procfile", "web:", "Web process definition")
    
    # Check Python version
    print("\n🐍 Python Environment:")
    if sys.version_info >= (3, 10):
        print(f"✅ Python version: {sys.version.split()[0]} (>= 3.10)")
    else:
        print(f"❌ Python version: {sys.version.split()[0]} (< 3.10 - Railway requires 3.10+)")
        all_good = False
    
    # Check dependencies
    print("\n📦 Dependencies:")
    try:
        import quart
        version = getattr(quart, '__version__', 'Unknown version')
        print(f"✅ Quart: {version}")
    except ImportError:
        print("❌ Quart: Not installed")
        all_good = False
    
    try:
        import playwright
        version = getattr(playwright, '__version__', 'Unknown version')
        print(f"✅ Playwright: {version}")
    except ImportError:
        print("❌ Playwright: Not installed")
        all_good = False
    
    # Check environment variables
    print("\n🌍 Environment Variables (for production):")
    env_vars = ["ENVIRONMENT", "USE_MOCK_DATA", "HOST", "PORT"]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Not set (will use defaults)")
    
    # Final verdict
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 DEPLOYMENT READY!")
        print("✅ All required files and configurations are present")
        print("✅ Your eBay scraper is ready for Railway deployment")
        print("\n🚀 Next steps:")
        print("1. Push your code to GitHub")
        print("2. Go to https://railway.app")
        print("3. Deploy from GitHub repo")
        print("4. Set ENVIRONMENT=production")
        print("5. Your app will be live!")
    else:
        print("⚠️  DEPLOYMENT ISSUES DETECTED")
        print("❌ Please fix the issues above before deploying")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 