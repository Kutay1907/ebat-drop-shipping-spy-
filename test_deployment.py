#!/usr/bin/env python3
"""
Quick Deployment Test

Tests that all components work before Railway deployment.
"""

import os
import sys
import asyncio
from pathlib import Path

async def test_deployment():
    """Test deployment readiness."""
    print("🧪 Testing deployment readiness...")
    
    # Test 1: Environment setup
    os.environ["ENVIRONMENT"] = "production"
    os.environ["USE_MOCK_DATA"] = "false"
    print("✅ Environment variables set")
    
    # Test 2: Directory creation
    for directory in ["data", "logs", "output"]:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directory {directory} ready")
    
    # Test 3: Import test
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.presentation.web_app import EbayScraperWebApp
        from src.infrastructure.dependency_injection import container
        print("✅ Imports successful")
        
        # Test 4: Container initialization
        await container.initialize()
        print("✅ Dependency container initialized")
        
        # Test 5: Web app creation
        web_app = EbayScraperWebApp(container)
        app = web_app.app
        print("✅ Web application created")
        
        print("\n🎉 ALL TESTS PASSED! Ready for Railway deployment")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_deployment())
    sys.exit(0 if success else 1) 