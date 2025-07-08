# 🚀 eBay Dropshipping Spy - Professional API Integration

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104.1-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

A **production-grade eBay API integration platform** that converts any eBay API Explorer call into working Python code. Perfect for dropshipping businesses, product research, and developers who need reliable access to eBay's vast product catalog.

## 🌟 Key Features

### ⚡ Universal eBay API Access
- **Convert ANY eBay API Explorer call to Python code** - our crown jewel feature!
- Support for all HTTP methods (GET, POST, PUT, DELETE)
- Direct access to any eBay API endpoint
- Automatic authentication and error handling

### 🔐 Multi-Token Authentication
- **Application Tokens** (Client Credentials) - recommended for most use cases
- **User OAuth Tokens** - for user-specific operations
- **Manual Token Override** - bring your own tokens
- Automatic token refresh and management

### 🌍 Global Marketplace Support
- United States, United Kingdom, Germany, Australia, Canada
- France, Italy, Spain, Netherlands, Belgium, and more
- Real-time currency and pricing data
- Marketplace-specific configurations

### 🔍 Advanced Product Search
- Basic keyword search with sorting options
- Advanced filtering (price ranges, conditions, categories)
- Multi-marketplace search capabilities
- Real-time pricing and availability data

### 🏗️ Production Ready
- Comprehensive error handling and retries
- Smart rate limiting with exponential backoff
- Detailed logging and monitoring
- Type-safe API with Pydantic validation

## 🚀 Quick Start

### 1. Installation

```bash
git clone https://github.com/yourusername/ebay-dropshipping-spy.git
cd ebay-dropshipping-spy
pip install -r requirements.txt
```

### 2. Environment Setup

Create a `.env` file with your eBay credentials:

```bash
# Required for Application Token (Recommended)
EBAY_CLIENT_ID=your_ebay_app_id
EBAY_CLIENT_SECRET=your_ebay_cert_id

# Optional for User OAuth
EBAY_OAUTH_TOKEN=your_user_token
EBAY_REDIRECT_URI=https://your-app.railway.app/auth/callback

# Database (optional)
DATABASE_URL=sqlite:///./database.db
```

### 3. Run the Server

```bash
python -m uvicorn app.main:app --reload
```

Visit `http://localhost:8000` to see the beautiful UI and start exploring!

## 🎯 API Endpoints

### Core Features

#### 🔍 Basic Product Search
```bash
POST /api/search
```
```json
{
  "keyword": "wireless headphones",
  "limit": 20,
  "marketplace": "EBAY_US",
  "sort": "price"
}
```

#### ⚡ Advanced Search with Filters
```bash
POST /api/search/advanced
```
```json
{
  "keyword": "smartphone",
  "min_price": 100,
  "max_price": 500,
  "condition": "NEW",
  "category_ids": ["9355"],
  "marketplace": "EBAY_US"
}
```

#### 🌟 Universal API Access (The Crown Jewel!)
```bash
POST /api/api-call
```
```json
{
  "method": "GET",
  "endpoint": "/buy/browse/v1/item_summary/search",
  "params": {
    "q": "gaming laptop",
    "limit": 50,
    "filter": "price:[500..2000],condition:NEW"
  },
  "marketplace": "EBAY_US",
  "token": "optional_token_override"
}
```

#### 📊 Item Details
```bash
GET /api/item/{item_id}?fieldgroups=PRODUCT,EXTENDED
```

### Utility Endpoints

- `GET /api/test-connection` - Test eBay API connectivity
- `GET /api/marketplace/info` - Get marketplace information
- `GET /api/health` - API health check

## 🔧 Python Integration

### Simple Search Example

```python
import httpx
import asyncio

async def search_products():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/api/search",
            json={
                "keyword": "wireless headphones",
                "limit": 50,
                "marketplace": "EBAY_US",
                "sort": "price"
            }
        )
        return response.json()

results = asyncio.run(search_products())
print(f"Found {results['total_found']} products")
```

### Universal API Access Example

```python
async def call_any_ebay_api():
    """Convert any eBay API Explorer call to Python!"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://your-app.railway.app/api/api-call",
            json={
                "method": "GET", 
                "endpoint": "/buy/browse/v1/item_summary/search",
                "params": {
                    "q": "vintage watch",
                    "limit": 100,
                    "filter": "price:[50..500],condition:USED",
                    "sort": "endingSoonest"
                },
                "marketplace": "EBAY_US"
            }
        )
        return response.json()

# This works with ANY eBay API endpoint!
```

### Advanced Multi-Marketplace Search

```python
async def search_global_markets():
    marketplaces = ["EBAY_US", "EBAY_GB", "EBAY_DE", "EBAY_AU"]
    results = {}
    
    async with httpx.AsyncClient() as client:
        for marketplace in marketplaces:
            response = await client.post(
                "https://your-app.railway.app/api/search",
                json={
                    "keyword": "drone camera",
                    "limit": 20,
                    "marketplace": marketplace
                }
            )
            results[marketplace] = response.json()
    
    return results
```

## 🎨 Beautiful Web Interface

Our platform includes a modern, responsive web interface with:

- **Interactive product search** with real-time results
- **API Explorer** to test any eBay endpoint
- **Feature showcase** with live demos
- **Comprehensive documentation** and examples
- **Multi-tab interface** for different functionalities

## 🔐 Authentication Options

### Option 1: Application Token (Recommended)
Set `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET` for automatic token management.

### Option 2: User OAuth Token  
Set `EBAY_OAUTH_TOKEN` for user-specific operations.

### Option 3: Manual Token Override
Pass tokens directly in API calls for maximum flexibility.

## 🌍 Supported Marketplaces

| Marketplace | Country | Currency | Site ID |
|-------------|---------|----------|---------|
| EBAY_US     | United States | USD | 0 |
| EBAY_GB     | United Kingdom | GBP | 3 |
| EBAY_DE     | Germany | EUR | 77 |
| EBAY_AU     | Australia | AUD | 15 |
| EBAY_CA     | Canada | CAD | 2 |
| EBAY_FR     | France | EUR | 71 |
| EBAY_IT     | Italy | EUR | 101 |
| EBAY_ES     | Spain | EUR | 186 |
| EBAY_NL     | Netherlands | EUR | 146 |
| EBAY_BE     | Belgium | EUR | 23 |

## 🧪 Testing & Demo

Run the comprehensive demo to see all features in action:

```bash
python test_all_features.py
```

This demo showcases:
- ✅ Health checks and connection tests
- ✅ Basic and advanced product searches
- ✅ Multi-marketplace functionality
- ✅ Universal API access (the crown jewel!)
- ✅ Error handling and edge cases

## 🚀 Deployment

### Railway (Recommended)
```bash
railway deploy
```

### Vercel
```bash
vercel --prod
```

### Docker
```bash
docker build -t ebay-spy .
docker run -p 8000:8000 ebay-spy
```

### Environment Variables for Production
```bash
EBAY_CLIENT_ID=your_production_app_id
EBAY_CLIENT_SECRET=your_production_cert_id
DATABASE_URL=postgresql://user:pass@host:port/db
```

## 📚 API Documentation

Once running, visit:
- **Interactive UI**: `https://your-app.railway.app/`
- **API Docs**: `https://your-app.railway.app/docs`
- **OpenAPI Schema**: `https://your-app.railway.app/openapi.json`

## 🏗️ Architecture

### Core Components

- **`app/ebay_api_client.py`** - Production-grade async eBay API client
- **`app/search_routes.py`** - FastAPI routes for all search functionality  
- **`app/auth_routes.py`** - OAuth authentication handling
- **`app/main.py`** - FastAPI application with beautiful UI
- **`app/database.py`** - SQLModel database integration

### Key Features of the API Client

- Automatic token management and refresh
- Smart rate limiting with exponential backoff
- Comprehensive error handling and retries
- Support for all HTTP methods and eBay endpoints
- Type-safe with full async/await support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) for high-performance APIs
- Powered by [httpx](https://www.python-httpx.org/) for async HTTP requests
- Uses [SQLModel](https://sqlmodel.tiangolo.com/) for type-safe database operations
- Styled with modern CSS and responsive design principles

## 💡 Use Cases

### For Dropshippers
- **Product Research**: Find trending and profitable products
- **Price Monitoring**: Track competitor pricing across marketplaces  
- **Market Analysis**: Compare prices across different countries
- **Inventory Planning**: Discover high-demand products

### For Developers
- **API Integration**: Convert any eBay API Explorer call to Python
- **Custom Applications**: Build your own eBay-powered tools
- **Data Analysis**: Access real-time eBay data for analytics
- **Automation**: Create automated workflows and bots

### For Businesses
- **E-commerce Platforms**: Integrate eBay data into your platform
- **Market Intelligence**: Monitor competitor activity and pricing
- **Product Catalogs**: Enhance your product database with eBay data
- **Price Optimization**: Dynamic pricing based on market data

---

**🚀 Ready to revolutionize your eBay integration?** Start by setting up your eBay developer account and credentials, then explore our beautiful interface and powerful APIs!

For questions or support, please open an issue or reach out to our community. 