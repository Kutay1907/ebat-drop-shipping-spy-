#!/usr/bin/env python3
"""
Installation Script for eBay Scraper

Helps set up the project and install dependencies.
"""

import sys
import subprocess
import os
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.10 or higher."""
    if sys.version_info < (3, 10):
        print("❌ This project requires Python 3.10 or higher")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version.split()[0]} is compatible")
    return True


def install_dependencies():
    """Install Python dependencies."""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True, text=True)
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print(f"   Output: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return False


def install_playwright():
    """Install Playwright browsers."""
    print("\n🎭 Installing Playwright browsers...")
    try:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], 
                      check=True, capture_output=True, text=True)
        print("✅ Playwright browsers installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Playwright browsers: {e}")
        return False


def create_directories():
    """Create required directories."""
    print("\n📁 Creating required directories...")
    directories = ["logs", "output", "templates"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")


def create_env_file():
    """Create a sample .env file."""
    print("\n⚙️ Creating sample environment file...")
    
    env_content = """# eBay Scraper Configuration

# Application Settings
APP_ENVIRONMENT=development
APP_NAME=eBay Scraper
APP_VERSION=1.0.0

# Web Server Settings
WEB_HOST=127.0.0.1
WEB_PORT=5000
WEB_DEBUG=True
WEB_SECRET_KEY=dev-secret-key-change-in-production

# Bot Protection Settings
BOT_PROTECTION_MIN_DELAY=1.0
BOT_PROTECTION_MAX_DELAY=5.0
BOT_PROTECTION_MOUSE_MOVE_PROBABILITY=0.8
BOT_PROTECTION_SCROLL_PROBABILITY=0.7

# Scraping Settings
SCRAPING_MAX_CONCURRENT_REQUESTS=3
SCRAPING_REQUEST_TIMEOUT=30.0
SCRAPING_PAGE_LOAD_TIMEOUT=30.0

# Retry Settings
RETRY_MAX_RETRIES=3
RETRY_BASE_BACKOFF=1.0
RETRY_MAX_BACKOFF=30.0

# Logging Settings
LOG_LEVEL=INFO
LOG_TO_FILE=True
LOG_TO_CONSOLE=True
LOG_FILE_PATH=logs/ebay_scraper.log

# Storage Settings
STORAGE_OUTPUT_DIRECTORY=output
STORAGE_COMPRESS_RESULTS=True

# Playwright Settings
PLAYWRIGHT_BROWSER_TYPE=chromium
PLAYWRIGHT_HEADLESS=True
PLAYWRIGHT_VIEWPORT_WIDTH=1280
PLAYWRIGHT_VIEWPORT_HEIGHT=720
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        env_file.write_text(env_content)
        print("✅ Created .env file with default settings")
    else:
        print("ℹ️  .env file already exists, skipping")


def create_sample_state_file():
    """Create a sample eBay state file."""
    print("\n🔐 Creating sample eBay state file...")
    
    state_content = """{
    "cookies": {
        "s": "REPLACE_WITH_YOUR_SESSION_COOKIE",
        "nonsession": "REPLACE_WITH_YOUR_NONSESSION_COOKIE",
        "dp1": "REPLACE_WITH_YOUR_DP1_COOKIE"
    },
    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "is_authenticated": false,
    "username": "REPLACE_WITH_YOUR_EBAY_USERNAME"
}"""
    
    state_file = Path("ebay_state.json")
    if not state_file.exists():
        state_file.write_text(state_content)
        print("✅ Created ebay_state.json template")
        print("ℹ️  Please update ebay_state.json with your actual eBay session cookies")
    else:
        print("ℹ️  ebay_state.json already exists, skipping")


def check_installation():
    """Check if installation was successful."""
    print("\n🔍 Checking installation...")
    
    try:
        import pydantic
        print("✅ Pydantic is available")
    except ImportError:
        print("❌ Pydantic not found")
        return False
    
    try:
        import quart
        print("✅ Quart is available")
    except ImportError:
        print("❌ Quart not found")
        return False
    
    try:
        import playwright
        print("✅ Playwright is available")
    except ImportError:
        print("❌ Playwright not found")
        return False
    
    return True


def print_usage_instructions():
    """Print usage instructions."""
    print("""
🚀 Installation Complete!

Next Steps:
1. Update ebay_state.json with your eBay session cookies (optional for demo)
2. Run the application:
   python main.py

3. Open your browser to:
   http://localhost:5000

4. Use the API endpoints:
   POST http://localhost:5000/api/v1/scrape
   GET  http://localhost:5000/api/v1/health

Configuration:
- Edit .env file to customize settings
- Check config/settings.py for all available options

Architecture:
This project demonstrates clean architecture with:
- SOLID principles implementation
- Dependency injection
- Async-first design
- Comprehensive error handling
- Structured logging

For more information, see README.md

Happy scraping! 🕷️
""")


def main():
    """Main installation process."""
    print("🚀 eBay Scraper Installation Script")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Installation failed during dependency installation")
        sys.exit(1)
    
    # Install Playwright
    if not install_playwright():
        print("\n⚠️  Playwright installation failed, but you can continue")
        print("   Run 'python -m playwright install chromium' manually later")
    
    # Create configuration files
    create_env_file()
    create_sample_state_file()
    
    # Check installation
    if check_installation():
        print("\n✅ Installation completed successfully!")
        print_usage_instructions()
    else:
        print("\n❌ Installation verification failed")
        print("   Some dependencies may not be properly installed")
        sys.exit(1)


if __name__ == "__main__":
    main() 