#!/usr/bin/env python3
"""
Simple Deployment Script

A minimal deployment script that focuses on getting the basic application running.
This is a fallback option if the main deployment script fails.
"""

import os
import sys
import asyncio
from pathlib import Path

def setup_minimal_environment():
    """Set up minimal production environment."""
    print("🔧 Setting up minimal environment...")
    
    # Create required directories
    directories = ["data", "logs", "output"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    # Set environment variables
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("USE_MOCK_DATA", "true")  # Use mock data for minimal deployment
    os.environ.setdefault("HOST", "0.0.0.0")
    
    print("✅ Minimal environment configured")

def check_minimal_dependencies():
    """Check only essential dependencies."""
    print("📦 Checking minimal dependencies...")
    
    essential_deps = ["quart"]
    
    for dep in essential_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} available")
        except ImportError:
            print(f"❌ {dep} missing - CRITICAL")
            return False
    
    return True

async def create_minimal_app():
    """Create a minimal Quart application."""
    try:
        from quart import Quart, render_template_string
        
        app = Quart(__name__)
        
        @app.route('/')
        async def home():
            return render_template_string("""
            <!DOCTYPE html>
            <html>
            <head>
                <title>eBay Scraper - Minimal Deployment</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    .status { padding: 15px; border-radius: 5px; margin: 20px 0; }
                    .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                    .warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
                    .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                    h1 { color: #333; }
                    .feature-list { margin: 20px 0; }
                    .feature-list li { margin: 10px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🚀 eBay Scraper - Minimal Deployment</h1>
                    
                    <div class="status success">
                        <strong>✅ Application Status:</strong> Running in minimal mode
                    </div>
                    
                    <div class="status warning">
                        <strong>⚠️  Deployment Mode:</strong> Minimal deployment with limited functionality
                    </div>
                    
                    <h2>Current Status:</h2>
                    <ul class="feature-list">
                        <li>✅ Web server running</li>
                        <li>✅ Basic routing working</li>
                        <li>⚠️  Database: Using mock data</li>
                        <li>⚠️  Scraping: Limited functionality</li>
                        <li>⚠️  Browser automation: Not available</li>
                    </ul>
                    
                    <h2>Next Steps:</h2>
                    <ul class="feature-list">
                        <li>Check Railway logs for dependency installation issues</li>
                        <li>Verify requirements.txt is being processed correctly</li>
                        <li>Ensure all Python packages are compatible</li>
                        <li>Consider using a different deployment strategy</li>
                    </ul>
                    
                    <div class="status error">
                        <strong>🔧 Debug Information:</strong><br>
                        Environment: {{ env }}<br>
                        Python Path: {{ python_path }}<br>
                        Working Directory: {{ cwd }}
                    </div>
                </div>
            </body>
            </html>
            """, 
            env=os.environ.get('ENVIRONMENT', 'unknown'),
            python_path=sys.executable,
            cwd=os.getcwd()
            )
        
        @app.route('/health')
        async def health():
            return {"status": "healthy", "mode": "minimal", "environment": os.environ.get('ENVIRONMENT', 'unknown')}
        
        return app
        
    except Exception as e:
        print(f"❌ Failed to create minimal app: {e}")
        raise

async def start_minimal_server(app):
    """Start the minimal server."""
    try:
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"🌍 Environment: {os.environ.get('ENVIRONMENT', 'production')}")
        print(f"🚀 Starting minimal server on {host}:{port}")
        
        await app.run_task(host=host, port=port, debug=False)
        
    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        raise

async def main():
    """Main minimal deployment function."""
    try:
        print("=" * 60)
        print("🚀 MINIMAL DEPLOYMENT STARTING")
        print("=" * 60)
        
        # Step 1: Setup environment
        setup_minimal_environment()
        
        # Step 2: Check minimal dependencies
        if not check_minimal_dependencies():
            print("❌ Critical dependencies missing!")
            sys.exit(1)
        
        # Step 3: Create minimal app
        app = await create_minimal_app()
        
        # Step 4: Start server
        print("=" * 60)
        print("🎉 MINIMAL DEPLOYMENT COMPLETE - STARTING SERVER")
        print("=" * 60)
        
        await start_minimal_server(app)
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"\n❌ MINIMAL DEPLOYMENT FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    # Set event loop policy for compatibility
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # Run the minimal deployment
    asyncio.run(main()) 