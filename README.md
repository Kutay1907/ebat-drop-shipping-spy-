# eBay Dropshipping Spy

Advanced eBay product research tool for dropshipping entrepreneurs.

## Features

- **🔥 Multi-Word Search Optimization**: Enhanced search supporting 2-10 word phrases with intelligent formatting
- **📊 Intelligent Sold Count Estimation**: Algorithmic estimation of 90-day sales data based on seller performance, price, and category factors
- **👀 Smart Watch Count Estimation**: Realistic watch count predictions using price, condition, and seller metrics
- **🎯 15+ Advanced Filters**: Comprehensive filtering including feedback scores, authenticity verification, returns policy, and more
- **🏪 Enhanced Seller Analysis**: Business seller filtering, top-rated seller identification, shipping options analysis
- **💡 Dropshipping Insights**: Intelligent market analysis with demand scoring, competition assessment, and profit potential

## Quick Start

1. **Set up eBay API credentials** in `.env`:
```env
# Required for Application Token (Recommended)
EBAY_CLIENT_ID=your_ebay_app_id
EBAY_CLIENT_SECRET=your_ebay_cert_id

# Optional: For User Token (More features but requires user login)
EBAY_REDIRECT_URI=your_redirect_uri
```

2. **Get eBay API Credentials**:
   - Visit [eBay Developer Program](https://developer.ebay.com/)
   - Create an account and new application  
   - Get your App ID (Client ID) and Cert ID (Client Secret)
   - Add them to your `.env` file

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the application**:
```bash
python -m uvicorn app.main:app --reload
```

5. **Open your browser** to `http://localhost:8000`

## 🔍 **Important Note About Data Sources**

### **Sold Count & Watch Count Data**

Due to eBay API limitations, this application uses **intelligent algorithmic estimation** for sold count and watch count data:

#### **Why Not Real Data?**
- **eBay Marketplace Insights API**: Requires special business approval (Limited Release)
- **eBay Browse API**: Does not provide watch count or sold count fields
- **eBay Trading API**: Being deprecated, limited access to watch/bid counts
- **eBay Completed Listings**: Only available through eBay's web interface, not APIs

#### **Our Solution: Smart Estimation**
The application provides realistic estimates based on:

**Sold Count Estimation Factors:**
- Seller feedback score and percentage
- Item price range and category popularity  
- Business vs individual seller type
- Shipping options and seller performance

**Watch Count Estimation Factors:**
- Item price (higher prices get more watchers)
- Item condition (new items get more attention)
- Seller reputation and feedback
- Free shipping availability

#### **Accuracy & Reliability**
- Estimates are calibrated against real-world eBay patterns
- Provides realistic ranges for dropshipping analysis
- Includes demand scoring and competition assessment
- Perfect for market research and trend identification

### **For Real Sold Count Data**
If you need actual sold count data, consider:
- **Manual Research**: Use eBay's completed listings search
- **Third-party Services**: WatchCount.com, TeraPeak, or similar tools
- **eBay Marketplace Insights API**: Apply for business approval
- **Web Scraping**: Follow eBay's terms of service

## 🎯 **Advanced Features**

### **Multi-Word Search Modes**
- **Enhanced Mode** (Default): Optimizes 2-10 word searches for best results
- **Exact Phrase Mode**: Searches for exact phrases in quotes
- **Broad Search Mode**: eBay's default OR search

### **Comprehensive Filters**
- Price range, condition, location filters
- Seller feedback score filtering  
- Watch count and sold count estimation filters
- Authenticity verification, returns policy
- Business sellers, top-rated sellers
- Shipping options and local pickup
- Auction vs Buy It Now filtering

### **Dropshipping Insights**
- **Demand Score**: 1-100 rating based on estimated sales and interest
- **Competition Level**: Market saturation analysis
- **Profit Potential**: Price-based profitability assessment  
- **Shipping Score**: Delivery options and speed rating
- **Seller Reliability**: Feedback-based seller assessment

## 📊 **API Endpoints**

### **Search Products**
```
GET /api/search
```

**Enhanced Parameters:**
- `q`: Search query (2-10 words recommended)
- `search_mode`: enhanced/exact/broad search optimization
- `min_sold_count`/`max_sold_count`: Filter by estimated 90-day sales
- `min_watch_count`/`max_watch_count`: Filter by estimated watchers
- `min_feedback_score`/`max_feedback_score`: Seller feedback filtering
- `authenticity_verification`: Items with authenticity guarantee
- `returns_accepted`: Items accepting returns
- `business_seller`: Business sellers only
- `free_shipping`: Free shipping only
- And 10+ more advanced filters...

### **Server Health**
```
GET /debug/health
```

## 🔧 **Development**

### **Project Structure**
```
├── app/
│   ├── main.py              # FastAPI application
│   ├── search_routes.py     # Enhanced search endpoints
│   ├── debug_routes.py      # Health and debug endpoints
│   └── ebay_api_client.py   # eBay API integration
├── static/
│   └── index.html          # Frontend interface
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### **Key Technologies**
- **Backend**: FastAPI, Python 3.8+
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **APIs**: eBay Browse API (REST)
- **Estimation**: Custom algorithms for sold/watch count prediction

## 🚀 **Usage Examples**

### **Multi-Word Product Research**
```
Search: "wireless bluetooth earbuds waterproof"
Mode: Enhanced (default)
Filters: min_sold_count=10, business_seller=true
```

### **Dropshipping Opportunity Analysis**
```
Search: "phone case iPhone 15 Pro Max"
Filters: 
- min_watch_count=20
- max_price=50
- returns_accepted=true
- free_shipping=true
```

### **Market Trend Analysis**
```
Search: "fitness tracker heart rate monitor" 
Sort: newly_listed
Filters: min_feedback_score=1000, authenticity_verification=true
```

## ⚖️ **Legal & Compliance**

- Uses official eBay Browse API within rate limits
- Respects eBay's Terms of Service
- Estimation algorithms are original intellectual property
- No web scraping or unauthorized data access
- Suitable for legitimate market research

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 **License**

MIT License - see LICENSE file for details.

---

**Perfect for**: Dropshipping research, market analysis, competitive intelligence, pricing strategy, product sourcing, and e-commerce trend identification. 