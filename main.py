#!/usr/bin/env python3
"""
eBay Dropshipping Spy - Main Application Entry Point

Production-ready eBay scraper with Clean Architecture.
Supports both local development and cloud deployment (Railway, Heroku, etc.)
"""

import os
import sys
import asyncio
from pathlib import Path

# Add project root to Python path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

async def main():
    """Main application entry point for both development and production."""
    try:
        from src.presentation.web_app import EbayScraperWebApp
        from src.infrastructure.dependency_injection import container
        
        # Initialize the dependency container
        print("🚀 Initializing eBay Scraper...")
        await container.initialize()
        
        # Initialize the web application
        web_app = EbayScraperWebApp(container)
        app = web_app.app
        
        # ✅ PRODUCTION CONFIGURATION: Get host and port from environment
        # Railway, Heroku, and other cloud platforms set PORT environment variable
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")  # 0.0.0.0 required for cloud deployment
        
        # ✅ ENVIRONMENT DETECTION
        environment = os.environ.get("ENVIRONMENT", "development")
        is_production = environment.lower() in ["production", "prod"]
        
        print(f"🌍 Environment: {environment}")
        print(f"🚀 Starting eBay Scraper on {host}:{port}")
        
        if is_production:
            print("🏭 Production mode: Using Hypercorn ASGI server")
            try:
                import hypercorn.asyncio
                from hypercorn import Config
                
                # ✅ PRODUCTION SERVER: Use Hypercorn for better performance
                config = Config()
                config.bind = [f"{host}:{port}"]
                config.use_reloader = False
                config.accesslog = "-"  # Log to stdout
                config.errorlog = "-"   # Log to stderr
                config.loglevel = "info"
                
                # Start the production server
                await hypercorn.asyncio.serve(app, config)
                
            except ImportError:
                print("⚠️  Hypercorn not available, falling back to development server")
                await app.run_task(host=host, port=port, debug=False)
        else:
            print("🛠️  Development mode: Using Quart development server")
            # ✅ DEVELOPMENT SERVER: Use Quart's built-in server
            await app.run_task(host=host, port=port, debug=True)
            
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # ✅ CROSS-PLATFORM COMPATIBILITY
    if sys.platform.startswith('win'):
        # Windows requires ProactorEventLoop for subprocess support
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Start the application
    asyncio.run(main()) 