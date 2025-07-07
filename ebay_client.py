"""Async helper module to fetch eBay product data.

Usage:
    from ebay_client import ebay_keyword_search
    results = asyncio.run(ebay_keyword_search("drone", token))
"""
from __future__ import annotations

import asyncio
from typing import List, Dict, Any
import httpx

EBAY_BROWSE_API = "https://api.ebay.com/buy/browse/v1/item_summary/search"
EBAY_GET_ITEMS_API = "https://api.ebay.com/buy/browse/v1/item/get_items"

class EbayAPIError(Exception):
    """Custom exception for eBay API errors."""

async def _fetch_item_summaries(
    client: httpx.AsyncClient,
    keyword: str,
    token: str,
    limit: int = 20,
    timeout: float = 10.0,
) -> List[str]:
    headers = {"Authorization": f"Bearer {token}"}
    params = {"q": keyword, "limit": str(limit)}
    resp = await client.get(EBAY_BROWSE_API, headers=headers, params=params, timeout=timeout)
    if resp.is_error:
        raise EbayAPIError(f"Browse API error: {resp.status_code} {resp.text}")
    data = resp.json()
    return [item["itemId"] for item in data.get("itemSummaries", [])]

async def _fetch_item_details(
    client: httpx.AsyncClient,
    item_ids: List[str],
    token: str,
    timeout: float = 10.0,
    retries: int = 2,
) -> List[Dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    params = {"item_ids": ",".join(item_ids)}

    for attempt in range(retries + 1):
        resp = await client.get(EBAY_GET_ITEMS_API, headers=headers, params=params, timeout=timeout)
        if resp.status_code == 429 and attempt < retries:
            await asyncio.sleep(2 ** attempt)
            continue
        if resp.is_error:
            raise EbayAPIError(f"getItems API error: {resp.status_code} {resp.text}")
        return resp.json().get("items", [])
    return []

def _parse_item(item: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "itemId": item.get("itemId"),
        "title": item.get("title"),
        "price": item.get("price", {}).get("value"),
        "currency": item.get("price", {}).get("currency"),
        "image": item.get("image", {}).get("imageUrl"),
        "seller": {
            "username": item.get("seller", {}).get("username"),
            "feedbackScore": item.get("seller", {}).get("feedbackScore"),
            "positiveFeedbackPercent": item.get("seller", {}).get("positiveFeedbackPercent"),
        },
        "condition": item.get("condition"),
        "itemWebUrl": item.get("itemWebUrl"),
        "soldQuantity": item.get("quantitySold", {}).get("value"),
    }

async def ebay_keyword_search(
    keyword: str,
    token: str,
    limit: int = 20,
    timeout: float = 10.0,
) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        item_ids = await _fetch_item_summaries(client, keyword, token, limit, timeout)
        if not item_ids:
            return {"results": []}
        items = await _fetch_item_details(client, item_ids, token, timeout)
        parsed = [_parse_item(it) for it in items]
        return {"results": parsed} 