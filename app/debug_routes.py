"""
Debug routes for troubleshooting eBay authentication issues
"""

import os
import logging
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional

from app.ebay_api_client import ebay_client, EbayAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/env")
async def check_environment_variables() -> Dict[str, Any]:
    """
    Check which environment variables are set (without exposing values).
    Useful for debugging Railway deployment issues.
    """
    env_vars = {
        "EBAY_CLIENT_ID": "SET" if os.getenv("EBAY_CLIENT_ID") else "NOT_SET",
        "EBAY_CLIENT_SECRET": "SET" if os.getenv("EBAY_CLIENT_SECRET") else "NOT_SET",
        "EBAY_OAUTH_TOKEN": "SET" if os.getenv("EBAY_OAUTH_TOKEN") else "NOT_SET",
        "EBAY_USER_TOKEN": "SET" if os.getenv("EBAY_USER_TOKEN") else "NOT_SET",
        "PORT": os.getenv("PORT", "NOT_SET"),
    }
    
    # Show partial values for debugging (first 4 and last 4 characters)
    for var_name in ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"]:
        value = os.getenv(var_name)
        if value and len(value) > 8:
            env_vars[f"{var_name}_PREVIEW"] = f"{value[:4]}...{value[-4:]}"
    
    return {
        "environment_variables": env_vars,
        "critical_missing": [
            var for var in ["EBAY_CLIENT_ID", "EBAY_CLIENT_SECRET"] 
            if not os.getenv(var)
        ]
    }

@router.get("/test-token")
async def test_ebay_token() -> Dict[str, Any]:
    """
    Test eBay token generation and API connectivity.
    """
    try:
        # Test the connection using the existing client
        connection_result = await ebay_client.test_connection()
        
        return {
            "status": "success" if connection_result.get("overall_status") == "healthy" else "issues",
            "message": "eBay authentication test completed",
            "details": connection_result
        }
    except Exception as e:
        logger.error(f"Token test failed: {e}")
        return {
            "status": "error",
            "message": f"Token test failed: {str(e)}",
            "details": None
        }

@router.get("/test-search")
async def test_ebay_search() -> Dict[str, Any]:
    """
    Test a simple eBay search to verify full functionality.
    """
    try:
        # Test search with the client
        results = await ebay_client.search_products(
            keyword="test",
            limit=1
        )
        
        return {
            "status": "success",
            "message": "eBay search test successful",
            "results_found": len(results.get("itemSummaries", [])),
            "total_available": results.get("total", 0)
        }
    except EbayAPIError as e:
        logger.error(f"Search test failed: {e}")
        return {
            "status": "error",
            "message": f"eBay search test failed: {e.message}",
            "error_code": e.status_code
        }
    except Exception as e:
        logger.error(f"Search test failed with unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Search test failed: {str(e)}",
            "error_code": None
        }

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Comprehensive health check including eBay API status.
    """
    health_status = {
        "service": "ebay-dropshipping-spy",
        "status": "healthy",
        "timestamp": None,
        "checks": {}
    }
    
    # Check environment variables
    env_check = await check_environment_variables()
    health_status["checks"]["environment"] = {
        "status": "healthy" if not env_check["critical_missing"] else "unhealthy",
        "missing_variables": env_check["critical_missing"]
    }
    
    # Check eBay token
    try:
        token_check = await test_ebay_token()
        health_status["checks"]["ebay_token"] = {
            "status": token_check["status"],
            "message": token_check["message"]
        }
    except Exception as e:
        health_status["checks"]["ebay_token"] = {
            "status": "error",
            "message": f"Token check failed: {str(e)}"
        }
    
    # Check eBay API
    try:
        search_check = await test_ebay_search()
        health_status["checks"]["ebay_api"] = {
            "status": search_check["status"],
            "message": search_check["message"]
        }
    except Exception as e:
        health_status["checks"]["ebay_api"] = {
            "status": "error",
            "message": f"API check failed: {str(e)}"
        }
    
    # Overall status
    failed_checks = [
        check for check in health_status["checks"].values()
        if check["status"] not in ["healthy", "success"]
    ]
    
    if failed_checks:
        health_status["status"] = "unhealthy"
    
    return health_status

@router.get("/troubleshooting")
async def get_troubleshooting_info() -> Dict[str, Any]:
    """
    Get comprehensive troubleshooting information.
    """
    return {
        "common_issues": {
            "no_valid_token": {
                "error": "No valid eBay authentication token available",
                "causes": [
                    "EBAY_CLIENT_ID not set in Railway environment variables",
                    "EBAY_CLIENT_SECRET not set in Railway environment variables",
                    "Wrong variable names (must be exact: EBAY_CLIENT_ID, EBAY_CLIENT_SECRET)",
                    "Invalid eBay app credentials",
                    "App not deployed after setting environment variables"
                ],
                "solutions": [
                    "Check Railway project → Variables tab",
                    "Verify eBay Developer account credentials",
                    "Make sure to click 'Deploy' after setting variables",
                    "Check Railway deployment logs for errors"
                ]
            },
            "token_request_failed": {
                "error": "eBay token request fails with 401/403",
                "causes": [
                    "Invalid App ID or Cert ID",
                    "App not approved for production",
                    "Using sandbox credentials in production",
                    "Insufficient app permissions"
                ],
                "solutions": [
                    "Verify credentials in eBay Developer portal",
                    "Check app approval status",
                    "Ensure using production credentials",
                    "Check app scope permissions"
                ]
            },
            "port_5000_in_use": {
                "error": "Port 5000 is in use",
                "causes": [
                    "AirPlay Receiver using port 5000 on macOS",
                    "Another process using the port"
                ],
                "solutions": [
                    "Disable AirPlay Receiver in System Preferences",
                    "Use a different port: uvicorn app.main:app --port 8000",
                    "Kill processes using port 5000"
                ]
            }
        },
        "debug_endpoints": {
            "/debug/env": "Check environment variables",
            "/debug/test-token": "Test eBay token generation",
            "/debug/test-search": "Test eBay API search",
            "/debug/health": "Comprehensive health check"
        },
        "railway_specific": {
            "environment_variables": "Set in Railway project → Variables tab",
            "deployment": "Must redeploy after setting variables",
            "logs": "Check Railway project → Deployments → View logs",
            "domain": "Generate domain in Railway project → Settings → Domains"
        }
    } 