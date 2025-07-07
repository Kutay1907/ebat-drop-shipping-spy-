#!/usr/bin/env python3
"""
eBay Scraper CLI Entry Point

Main entry point for command-line operations.
Usage: python -m ebay_scraper <command> [options]
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.dependency_injection import container
from src.infrastructure.cli_service import CLIService
from src.domain.exceptions import ConfigurationError
from config.simple_settings import settings


def check_production_configuration():
    """Check production configuration before initializing services."""
    if not settings.app.use_mock_data:
        print("🔍 Production mode: Checking requirements...")
        
        # Check critical dependencies for CLI operations
        missing_deps = []
        try:
            import playwright
        except ImportError:
            missing_deps.append("playwright")
        
        try:
            import pandas
        except ImportError:
            missing_deps.append("pandas")
        
        if missing_deps:
            print(f"❌ Production mode requires missing dependencies: {', '.join(missing_deps)}")
            print("   Please install them with: pip install playwright pandas")
            print("   Or set USE_MOCK_DATA=true for development mode")
            sys.exit(1)
        
        print("✅ Production requirements satisfied")
    else:
        print("⚠️  Development mode: Mock services may be active")


async def main():
    """Main CLI entry point."""
    try:
        # Early production configuration check
        check_production_configuration()
        
        # Initialize dependency container (with production enforcement)
        await container.initialize()
        
        # Get CLI service
        cli_service = container.get_cli_service()
        
        # Log service mode
        if not settings.app.use_mock_data:
            print("🚀 CLI running in production mode with real scraping services")
        
        # Run CLI with command line arguments
        exit_code = await cli_service.run_cli()
        
        # Cleanup
        await container.cleanup()
        
        # Exit with appropriate code
        sys.exit(exit_code)
        
    except ConfigurationError as e:
        print(f"❌ Configuration Error: {e.message}")
        if hasattr(e, 'config_key'):
            print(f"   Config key: {e.config_key}")
        if "mock" in e.message.lower():
            print("\n💡 Tip: For development, set USE_MOCK_DATA=true in config/simple_settings.py")
            print("   Or install required dependencies for production mode")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 10):
        print("❌ This application requires Python 3.10 or higher")
        print(f"   Current version: {sys.version}")
        sys.exit(1)
    
    # Create required directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    Path("exports").mkdir(exist_ok=True)
    
    # Run the CLI
    asyncio.run(main()) 