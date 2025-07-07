#!/usr/bin/env python3
"""
Production Validation Script

Comprehensive validation that eBay scraper is running in production mode
with real services, no mock data, and proper result persistence.
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime
import tempfile

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def check_python_version():
    """Check Python version meets requirements."""
    print("\n🐍 Python Version Check:")
    
    if sys.version_info >= (3, 10):
        print(f"✅ Python version: {sys.version.split()[0]} (>= 3.10)")
        return True
    else:
        print(f"❌ Python version: {sys.version.split()[0]} (requires >= 3.10)")
        return False


def check_mock_data_setting():
    """Check that USE_MOCK_DATA is disabled."""
    print("\n⚙️  Mock Data Setting Check:")
    
    try:
        from config.simple_settings import settings
        
        if settings.app.use_mock_data:
            print("❌ USE_MOCK_DATA is enabled (development mode)")
            print("   Set USE_MOCK_DATA=false in config/simple_settings.py for production")
            return False
        else:
            print("✅ USE_MOCK_DATA is disabled (production mode)")
            return True
            
    except Exception as e:
        print(f"❌ Failed to check mock data setting: {e}")
        return False


def check_dependencies():
    """Check required dependencies."""
    print("\n📦 Dependencies Check:")
    
    required_deps = [
        ("playwright", "Web automation for scraping"),
        ("pandas", "Data processing and export"),
        ("asyncio", "Async support"),
        ("decimal", "Precise decimal calculations"),
        ("sqlite3", "Database storage"),
        ("json", "JSON processing"),
        ("pathlib", "Path handling")
    ]
    
    missing_deps = []
    
    for dep_name, description in required_deps:
        try:
            __import__(dep_name)
            print(f"✅ {dep_name}: {description}")
        except ImportError:
            print(f"❌ {dep_name}: {description} - MISSING")
            missing_deps.append(dep_name)
    
    # Check Playwright browsers
    try:
        import playwright
        print("✅ Playwright installed")
        
        # Check if browsers are installed
        from playwright.sync_api import sync_playwright
        try:
            with sync_playwright() as p:
                # Try to launch chromium to verify it's installed
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✅ Playwright browsers installed")
        except Exception as e:
            print("⚠️  Playwright browsers may not be installed")
            print("   Run: playwright install chromium")
            print(f"   Error: {e}")
    except ImportError:
        missing_deps.append("playwright")
    
    if missing_deps:
        print(f"\n❌ Missing dependencies: {', '.join(missing_deps)}")
        print("   Install with: pip install " + " ".join(missing_deps))
        if "playwright" in missing_deps:
            print("   Then run: playwright install chromium")
        return False
    
    return True


async def check_service_initialization():
    """Check that services can be initialized without mock services."""
    print("\n⚙️  Service Initialization Check:")
    
    try:
        # Import and initialize container
        from src.infrastructure.dependency_injection import container
        
        # This should raise ConfigurationError if mock services are used
        await container.initialize()
        
        # Check that we have real services
        terapeak_analyzer = container.get_terapeak_analyzer()
        fallback_scraper = container.get_fallback_scraper()
        
        terapeak_class = terapeak_analyzer.__class__.__name__
        scraper_class = fallback_scraper.__class__.__name__
        
        if "Mock" in terapeak_class:
            print(f"❌ Terapeak analyzer is mock service: {terapeak_class}")
            return False
        
        if "Mock" in scraper_class:
            print(f"❌ Fallback scraper is mock service: {scraper_class}")
            return False
        
        print(f"✅ Terapeak analyzer: {terapeak_class}")
        print(f"✅ Fallback scraper: {scraper_class}")
        
        # Cleanup
        await container.cleanup()
        
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if "mock" in error_msg:
            print(f"❌ Mock services detected: {e}")
        else:
            print(f"❌ Service initialization failed: {e}")
        return False


async def check_database_storage():
    """Check database storage functionality."""
    print("\n💾 Database Storage Check:")
    
    try:
        from src.infrastructure.dependency_injection import container
        await container.initialize()
        
        # Get database storage service
        db_storage = container.get_database_storage()
        
        # Test database functionality
        from src.domain.models import ScrapingResult, SearchCriteria, Marketplace, ScrapingStatus
        
        # Create test result
        test_criteria = SearchCriteria(
            keyword="test-validation",
            marketplace=Marketplace.EBAY_US,
            max_results=1
        )
        
        test_result = ScrapingResult(
            criteria=test_criteria,
            products=[],
            status=ScrapingStatus.COMPLETED,
            scraping_duration=0.1
        )
        
        # Store result
        result_id = await db_storage.store_scraping_result(test_result)
        print(f"✅ Test result stored with ID: {result_id}")
        
        # Retrieve result
        retrieved_result = await db_storage.get_scraping_result(result_id)
        
        if retrieved_result:
            print("✅ Test result retrieved successfully")
            print(f"   Keyword: {retrieved_result.criteria.keyword}")
            print(f"   Status: {retrieved_result.status.value}")
        else:
            print("❌ Test result could not be retrieved")
            return False
        
        await container.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Database storage test failed: {e}")
        return False


async def check_scraping_workflow():
    """Check actual scraping workflow."""
    print("\n🔍 Scraping Workflow Check:")
    
    try:
        from src.infrastructure.dependency_injection import container
        await container.initialize()
        
        # Get orchestrator
        orchestrator = container.get_scraping_orchestrator()
        
        # Create minimal test criteria
        from src.domain.models import SearchCriteria, Marketplace
        
        test_criteria = SearchCriteria(
            keyword="smartphone",  # Simple, common search term
            marketplace=Marketplace.EBAY_US,
            max_results=1  # Just test one result
        )
        
        print(f"   Testing scraping for: '{test_criteria.keyword}'")
        print("   (This may take 30-60 seconds...)")
        
        # Execute scraping
        result = await orchestrator.execute_scraping(test_criteria)
        
        if result.result_id:
            print(f"✅ Scraping completed with result ID: {result.result_id}")
            print(f"   Status: {result.status.value}")
            print(f"   Products found: {len(result.products)}")
            print(f"   Duration: {result.scraping_duration:.2f}s")
            
            if result.products:
                print("✅ Real product data retrieved")
                sample_product = result.products[0]
                print(f"   Sample: {sample_product.title[:50]}...")
                print(f"   Price: ${sample_product.price}")
            else:
                print("⚠️  No products found (may indicate scraping issues)")
                return False
        else:
            print("❌ No result ID returned from scraping")
            return False
        
        await container.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Scraping workflow test failed: {e}")
        print(f"   This may indicate authentication, network, or bot detection issues")
        return False


def check_directories():
    """Check required directories exist."""
    print("\n📁 Directory Structure Check:")
    
    required_dirs = [
        "data",
        "logs", 
        "output",
        "exports"
    ]
    
    all_exist = True
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/ directory exists")
        else:
            print(f"⚠️  {dir_name}/ directory missing (will be created)")
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created {dir_name}/ directory")
            except Exception as e:
                print(f"❌ Failed to create {dir_name}/ directory: {e}")
                all_exist = False
    
    return all_exist


async def run_comprehensive_validation():
    """Run all validation checks."""
    print("🚀 eBay Scraper Production Validation")
    print("=" * 50)
    
    checks = [
        ("Python Version", check_python_version()),
        ("Mock Data Setting", check_mock_data_setting()),
        ("Dependencies", check_dependencies()),
        ("Directory Structure", check_directories()),
        ("Service Initialization", check_service_initialization()),
        ("Database Storage", check_database_storage()),
        ("Scraping Workflow", check_scraping_workflow())
    ]
    
    results = []
    
    for check_name, check_coro in checks:
        if asyncio.iscoroutine(check_coro):
            result = await check_coro
        else:
            result = check_coro
        results.append((check_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for check_name, result in results:
        if result:
            print(f"✅ {check_name}")
            passed += 1
        else:
            print(f"❌ {check_name}")
            failed += 1
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n🎉 ALL CHECKS PASSED!")
        print("✅ Your eBay scraper is ready for production")
        print("✅ use_mock_data is disabled")
        print("✅ TerapeakAnalyzer is real") 
        print("✅ Scraping result persisted successfully")
        print("✅ Real data returned")
        return True
    else:
        print(f"\n❌ {failed} checks failed")
        print("   Please fix the issues above before running in production")
        return False


if __name__ == "__main__":
    try:
        success = asyncio.run(run_comprehensive_validation())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n🛑 Validation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Validation script failed: {e}")
        sys.exit(1) 