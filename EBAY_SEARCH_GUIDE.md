# 🎯 eBay Search API - Complete Usage Guide

**✅ ALL ISSUES FIXED!** Your eBay search now works with:
- ✅ Working filters (price, condition, shipping, etc.)
- ✅ Clickable item links to eBay pages
- ✅ Available sold count data (with realistic limitations)
- ✅ Comprehensive market analysis tools

## 🚀 **Quick Start Examples**

### 1. **Basic Search**
```bash
GET /api/search?keyword=phone&limit=20
```

### 2. **Search with Price Filter**
```bash
GET /api/search?keyword=phone&min_price=100&max_price=500&limit=20
```

### 3. **Advanced Filtering**
```bash
GET /api/search?keyword=phone&condition=NEW&free_shipping_only=true&top_rated_sellers_only=true&limit=20
```

## 📊 **Available Endpoints**

### 🔍 **Main Search** - `/api/search`

**Parameters:**
- `keyword` (required) - Search term
- `limit` (1-200) - Number of results  
- `min_price` / `max_price` - Price range filters
- `condition` - Item condition (NEW, USED, CERTIFIED_REFURBISHED, etc.)
- `sort` - Sort order (BEST_MATCH, PRICE_LOW_TO_HIGH, NEWLY_LISTED, etc.)
- `category_ids` - Comma-separated category IDs
- `buy_it_now_only` - Show only Buy It Now items
- `free_shipping_only` - Show only free shipping items
- `top_rated_sellers_only` - Show only top-rated sellers
- `min_feedback_score` - Minimum seller feedback score
- `fast_n_free` - Items with Fast 'N Free shipping
- `charity_ids` - Charity listings
- `exclude_categories` - Categories to exclude

**Example Response:**
```json
{
  "success": true,
  "results": [
    {
      "item_id": "123456789",
      "title": "iPhone 15 Pro Max",
      "price": {"value": "999.00", "currency": "USD"},
      "condition": "New",
      "item_web_url": "https://www.ebay.com/itm/123456789",
      "item_affiliate_web_url": "https://rover.ebay.com/...",
      "view_item_url": "https://www.ebay.com/itm/123456789",
      "image_url": "https://i.ebayimg.com/...",
      "seller": {
        "username": "tech_seller_99",
        "feedbackPercentage": "100.0",
        "feedbackScore": 5420
      },
      "watch_count": 24,
      "bid_count": 0,
      "free_shipping": true,
      "listing_type": "BUY_IT_NOW",
      "time_left": "25d 14h 32m",
      "market_insights": {
        "popularity_indicators": {
          "watch_count": 24,
          "bid_count": 0,
          "has_bids": false
        },
        "seller_quality": {
          "feedback_percentage": "100.0",
          "feedback_score": 5420
        },
        "listing_quality": {
          "top_rated_buying_experience": true,
          "has_multiple_images": true
        }
      }
    }
  ],
  "total_found": 50000,
  "search_metadata": {
    "filters_applied": ["price:[100..500]", "deliveryOptions:{FreeShipping}"],
    "sort_order": "bestMatch",
    "results_count": 20
  }
}
```

### 📝 **Item Details** - `/api/item/{item_id}`

Get comprehensive details for a specific item:

```bash
GET /api/item/123456789
```

**Returns:**
- Full item description
- All images
- Detailed seller information
- Estimated availability data
- Watch count (if available)
- Bidding information
- Shipping options
- Return policies

### 📊 **Market Analysis** - `/api/research/market-analysis`

Perfect for dropshipping research:

```bash
GET /api/research/market-analysis?keyword=wireless%20earbuds&limit=100
```

**Returns:**
- Price analysis (average, min, max, range)
- Competition analysis (number of sellers)
- Listing type distribution
- Popular categories
- Market insights and recommendations

### 🏷️ **Categories** - `/api/categories`

Get popular eBay categories with IDs for filtering:

```bash
GET /api/categories
```

## 🎯 **Working Filters Explained**

### 💰 **Price Filters**
```bash
# Price range
?min_price=50&max_price=200

# Minimum price only  
?min_price=100

# Maximum price only
?max_price=500
```

### 🏷️ **Condition Filters**
```bash
# New items only
?condition=NEW

# Used items only  
?condition=USED

# Refurbished items
?condition=CERTIFIED_REFURBISHED
```

**Available Conditions:**
- `NEW` (1000)
- `USED` (3000) 
- `CERTIFIED_REFURBISHED` (2000)
- `EXCELLENT_REFURBISHED` (2010)
- `VERY_GOOD_REFURBISHED` (2020)
- `GOOD_REFURBISHED` (2030)
- `SELLER_REFURBISHED` (2500)
- `FOR_PARTS_OR_NOT_WORKING` (7000)

### 🚚 **Shipping Filters**
```bash
# Free shipping only
?free_shipping_only=true

# Fast 'N Free shipping
?fast_n_free=true
```

### ⭐ **Seller Filters**
```bash
# Top-rated sellers only
?top_rated_sellers_only=true

# Minimum feedback score
?min_feedback_score=1000
```

### 📦 **Listing Type Filters**
```bash
# Buy It Now only
?buy_it_now_only=true
```

### 🏪 **Category Filters**
```bash
# Electronics category
?category_ids=58058

# Multiple categories
?category_ids=58058,293,1249

# Exclude categories
?exclude_categories=12345,67890
```

## 🔗 **Working Item Links**

Each item now includes working links:

### 🌐 **Direct eBay Links**
- `item_web_url` - Direct link to eBay listing
- `view_item_url` - Same as item_web_url

### 💰 **Affiliate Links** 
- `item_affiliate_web_url` - eBay Partner Network affiliate link (when available)

**Usage:**
```javascript
// Direct user to eBay listing
window.open(item.item_web_url, '_blank');

// Use affiliate link for commissions
window.open(item.item_affiliate_web_url || item.item_web_url, '_blank');
```

## 📈 **Sold Count Data Reality**

### ✅ **What's Available:**
- `watch_count` - Number of watchers (requires special eBay permissions)
- `bid_count` - Number of bids (auction items only)
- `unique_bidder_count` - Unique bidders (detailed view only)
- `estimated_availabilities` - Stock estimates (detailed view)

### ⚠️ **Limitations:**
- **Exact sold counts** require eBay Terapeak or premium tools
- **Watch count** requires special API permissions
- **Historical sold data** not available in public API

### 🎯 **Alternative Metrics:**
- **Watch count** - Indicates interest/demand
- **Bid count** - Shows competition level
- **Time left + watchers** - Demand indicator
- **Price analysis** - Market positioning

## 🛒 **Dropshipping Research Examples**

### 1. **Find Trending Products**
```bash
GET /api/search?keyword=fidget&sort=NEWLY_LISTED&top_rated_sellers_only=true&limit=50
```

### 2. **Price Competition Analysis**
```bash
GET /api/research/market-analysis?keyword=wireless%20charger&limit=100
```

### 3. **High-Quality Listings Only**
```bash
GET /api/search?keyword=phone%20case&free_shipping_only=true&min_feedback_score=1000&condition=NEW&limit=50
```

### 4. **Category Research**
```bash
GET /api/search?keyword=gaming&category_ids=139973&buy_it_now_only=true&limit=100
```

## 📱 **Integration Examples**

### JavaScript/React
```javascript
// Search with filters
const searchProducts = async (keyword, filters = {}) => {
  const params = new URLSearchParams({
    keyword,
    limit: 50,
    ...filters
  });
  
  const response = await fetch(`/api/search?${params}`);
  const data = await response.json();
  
  return data.results;
};

// Usage
const phones = await searchProducts('phone', {
  min_price: 200,
  max_price: 800,
  condition: 'NEW',
  free_shipping_only: true
});

// Display results with working links
phones.forEach(item => {
  console.log(`${item.title} - $${item.price.value}`);
  console.log(`Link: ${item.item_web_url}`);
  console.log(`Watchers: ${item.watch_count || 'N/A'}`);
});
```

### Python
```python
import httpx

async def search_ebay(keyword, **filters):
    params = {"keyword": keyword, "limit": 50, **filters}
    
    async with httpx.AsyncClient() as client:
        response = await client.get("/api/search", params=params)
        data = response.json()
        
    return data["results"]

# Usage
results = await search_ebay(
    "laptop",
    min_price=500,
    max_price=1500,
    condition="NEW",
    top_rated_sellers_only=True
)

for item in results:
    print(f"{item['title']} - ${item['price']['value']}")
    print(f"Seller: {item['seller']['username']}")
    print(f"Link: {item['item_web_url']}")
```

## 🔧 **Troubleshooting**

### ❌ **No Results**
- Check if filters are too restrictive
- Try broader keywords
- Remove condition or price filters
- Use `/api/categories` to find valid category IDs

### ❌ **Links Not Working**
- Use `item_web_url` for direct eBay links
- Check if `item_affiliate_web_url` exists before using
- Links are automatically generated by eBay

### ❌ **No Sold Count Data**
- This is normal - eBay restricts this data
- Use `watch_count` and `bid_count` instead
- Consider upgrading to eBay Terapeak for historical data

### ❌ **Filters Not Working**
- Make sure you're using the correct parameter names
- Check condition values (use enum values like "NEW", not "1000")
- Price filters should be numbers, not strings

## 🎉 **Success! Your eBay Search is Now Fully Functional**

✅ **Working filters** - Price, condition, shipping, seller filters all work  
✅ **Clickable links** - Direct links to eBay listings included  
✅ **Available data** - All data that eBay API provides is extracted  
✅ **Market analysis** - Built-in tools for dropshipping research  
✅ **Proper documentation** - Clear examples and usage patterns  

Your eBay Dropshipping Spy tool is now ready for production use! 🚀 