#!/usr/bin/env python3
"""
Production Startup Script for Railway Deployment

Handles all production initialization:
- Directory creation
- Database initialization  
- Playwright browser installation
- Environment setup
- Error handling and logging
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path

def install_dependencies():
    """Install dependencies if they're missing."""
    print("📦 Installing dependencies...")
    
    try:
        # Try to install requirements.txt
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
            return True
        else:
            print(f"⚠️  Dependency installation warning: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Dependency installation timed out")
        return False
    except Exception as e:
        print(f"⚠️  Dependency installation failed: {e}")
        return False

def setup_production_environment():
    """Set up production environment and directories."""
    print("🔧 Setting up production environment...")
    
    # Create required directories
    directories = ["data", "logs", "output"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Set production environment variables
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("USE_MOCK_DATA", "false")
    os.environ.setdefault("HOST", "0.0.0.0")
    
    print("✅ Production environment configured")

def install_playwright_browsers():
    """Install Playwright browsers if needed."""
    try:
        print("🌐 Installing Playwright browsers...")
        
        # Check if playwright is available
        import playwright
        
        # Install chromium browser
        result = subprocess.run([
            sys.executable, "-m", "playwright", "install", "chromium"
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
        
        if result.returncode == 0:
            print("✅ Playwright Chromium installed successfully")
        else:
            print(f"⚠️  Playwright installation warning: {result.stderr}")
            print("📝 Continuing without browser automation...")
            
    except ImportError:
        print("⚠️  Playwright not available, skipping browser installation")
    except subprocess.TimeoutExpired:
        print("⚠️  Playwright installation timed out, continuing...")
    except Exception as e:
        print(f"⚠️  Playwright installation failed: {e}")
        print("📝 Application will continue with limited functionality")

def check_dependencies():
    """Check and report on critical dependencies."""
    print("📦 Checking dependencies...")
    
    dependencies = {
        "quart": "Web framework",
        "aiosqlite": "Database", 
        "pydantic": "Data validation",
        "playwright": "Browser automation (optional)"
    }
    
    missing_deps = []
    
    for dep, description in dependencies.items():
        try:
            __import__(dep)
            print(f"✅ {description}: {dep} available")
        except ImportError:
            if dep == "playwright":
                print(f"⚠️  {description}: {dep} not available (optional)")
            else:
                print(f"❌ {description}: {dep} missing")
                missing_deps.append(dep)
    
    if missing_deps:
        print(f"⚠️  Missing critical dependencies: {missing_deps}")
        print("🔄 Attempting to install missing dependencies...")
        if install_dependencies():
            # Re-check after installation
            print("🔄 Re-checking dependencies after installation...")
            return check_dependencies()
        else:
            return False
    
    return True

async def initialize_application():
    """Initialize the application with proper error handling."""
    try:
        # Add project root to path
        project_root = Path(__file__).parent
        sys.path.insert(0, str(project_root))
        
        print("🚀 Initializing eBay Scraper application...")
        
        # Import and initialize
        from src.presentation.web_app import EbayScraperWebApp
        from src.infrastructure.dependency_injection import container
        
        # Initialize dependency container
        await container.initialize()
        print("✅ Dependency container initialized")
        
        # Create web application
        web_app = EbayScraperWebApp(container)
        app = web_app.app
        print("✅ Web application created")
        
        return app
        
    except Exception as e:
        print(f"❌ Application initialization failed: {e}")
        print(f"📝 Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        raise

async def start_server(app):
    """Start the production server."""
    try:
        # Get configuration from environment
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"🌍 Environment: {os.environ.get('ENVIRONMENT', 'production')}")
        print(f"🚀 Starting server on {host}:{port}")
        
        # Try to use Hypercorn for production
        try:
            import hypercorn.asyncio
            from hypercorn import Config
            
            print("🏭 Using Hypercorn ASGI server")
            config = Config()
            config.bind = [f"{host}:{port}"]
            config.use_reloader = False
            config.accesslog = "-"
            config.errorlog = "-"
            config.loglevel = "info"
            config.worker_connections = 1000
            
            await hypercorn.asyncio.serve(app, config)
            
        except ImportError:
            print("🛠️  Using Quart development server")
            await app.run_task(host=host, port=port, debug=False)
            
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        raise

async def main():
    """Main production startup function."""
    try:
        print("=" * 60)
        print("🚀 RAILWAY PRODUCTION DEPLOYMENT STARTING")
        print("=" * 60)
        
        # Step 1: Setup environment
        setup_production_environment()
        
        # Step 2: Check dependencies
        if not check_dependencies():
            print("❌ Critical dependencies missing!")
            sys.exit(1)
        
        # Step 3: Install browsers (with timeout protection)
        install_playwright_browsers()
        
        # Step 4: Initialize application
        app = await initialize_application()
        
        # Step 5: Start server
        print("=" * 60)
        print("🎉 PRODUCTION STARTUP COMPLETE - STARTING SERVER")
        print("=" * 60)
        
        await start_server(app)
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ PRODUCTION STARTUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Set event loop policy for compatibility
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run the production startup
    asyncio.run(main()) 