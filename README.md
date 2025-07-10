# eBay Dropshipping Spy Pro

A clean, modern, and user-friendly eBay product research tool designed for dropshipping entrepreneurs. Find profitable products with ease using our streamlined interface and powerful search capabilities.

## ✨ Features

### 🎯 **Core Search Features**
- **Smart Product Search**: Enhanced multi-word search with intelligent keyword processing
- **Advanced Filtering**: Price range, condition, location, shipping options, and seller quality filters
- **Quick Search Presets**: One-click search for popular product categories
- **Real-time Results**: Fast, responsive search with clean product display

### 🎨 **Beautiful User Interface**
- **Modern Design**: Clean, professional interface with premium aesthetics
- **Mobile Responsive**: Optimized for all devices and screen sizes
- **Intuitive Navigation**: Easy-to-use controls and clear product information
- **Premium Experience**: Designed for subscriber satisfaction

### 🔍 **Smart Filtering Options**
- Price range filtering (min/max)
- Product condition selection
- Location-based filtering
- Free shipping options
- Top-rated sellers only
- Buy It Now vs Auction filtering

## 🚀 Quick Start

### 1. **Set up eBay API credentials**

Create a `.env` file in the project root:

```env
# Required eBay API Credentials
EBAY_CLIENT_ID=your_ebay_app_id
EBAY_CLIENT_SECRET=your_ebay_cert_id
```

### 2. **Get eBay Developer Credentials**

1. Visit [eBay Developer Program](https://developer.ebay.com/)
2. Create an account and new application
3. Get your App ID (Client ID) and Cert ID (Client Secret)
4. Add them to your `.env` file

### 3. **Install Dependencies**

```bash
pip install -r requirements.txt
```

### 4. **Run the Application**

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. **Access the Application**

Open your browser to: `http://localhost:8000`

## 🎯 How to Use

### **Basic Search**
1. Enter product keywords in the search box
2. Click "Search Products" or press Enter
3. Browse results with clean product cards

### **Quick Search**
- Use preset buttons for popular categories:
  - Wireless Earbuds
  - Phone Cases
  - Bluetooth Speakers
  - Fitness Trackers
  - And more...

### **Advanced Filtering**
1. Click "Advanced Filters" to expand options
2. Set price ranges, conditions, locations
3. Enable additional filters like free shipping
4. Search automatically applies all filters

### **Product Analysis**
- View key product information at a glance
- See seller ratings and feedback scores
- Identify top-rated sellers and premium listings
- Direct links to eBay product pages

## 🛠 API Endpoints

### **Main Search Endpoint**
```http
GET /api/search
```

**Parameters:**
- `keyword` (required): Search terms
- `limit`: Number of results (1-200, default: 50)
- `min_price`: Minimum price filter
- `max_price`: Maximum price filter
- `condition`: Item condition filter
- `sort`: Sort order (bestMatch, price, -price, etc.)
- `free_shipping_only`: Boolean for free shipping filter
- `top_rated_sellers_only`: Boolean for top-rated sellers
- `item_location_country`: Country code (US, GB, DE, etc.)

### **Categories Endpoint**
```http
GET /api/categories
```
Returns popular eBay categories for filtering.

## 🔧 Technical Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Modern HTML5, CSS3, JavaScript
- **API Integration**: eBay Browse API
- **Styling**: Custom CSS with modern design principles
- **Responsive**: Mobile-first design approach

## 📱 User Experience Features

### **Clean Interface**
- Professional gradient background
- Card-based layout for products
- Intuitive navigation and controls
- Clear typography and spacing

### **Smart Search**
- Auto-suggestion with quick filters
- Intelligent keyword processing
- Real-time search results
- Relevant product recommendations

### **Product Cards**
- High-quality product images
- Clear pricing and condition information
- Seller ratings and badges
- Direct action buttons

### **Responsive Design**
- Optimized for desktop, tablet, and mobile
- Touch-friendly interface elements
- Adaptive grid layouts
- Mobile navigation

## 🎨 Design Philosophy

This application is built with subscriber satisfaction in mind:

- **Simplicity**: Clean, uncluttered interface
- **Speed**: Fast search and responsive interactions
- **Clarity**: Clear product information and pricing
- **Professional**: Premium look and feel
- **Accessibility**: Easy to use for all skill levels

## 🔒 Security & Privacy

- Secure API credential handling
- No personal data collection
- Privacy-focused design
- Secure eBay API integration

## 📈 Perfect for Dropshippers

- **Product Research**: Find trending and profitable products
- **Competition Analysis**: See seller ratings and pricing
- **Market Validation**: Quick access to eBay marketplace data
- **Supplier Discovery**: Identify reliable sellers
- **Profit Opportunities**: Filter by price ranges and conditions

## 🚀 Deployment

### **Railway Deployment**
1. Connect your GitHub repository
2. Set environment variables in Railway dashboard:
   - `EBAY_CLIENT_ID`
   - `EBAY_CLIENT_SECRET`
3. Deploy automatically

### **Local Development**
```bash
# Install dependencies
pip install fastapi uvicorn httpx python-dotenv

# Run development server
uvicorn app.main:app --reload
```

## 📞 Support

For technical support or questions:
- Check the eBay Developer documentation
- Ensure API credentials are correctly set
- Verify network connectivity
- Review server logs for errors

---

**Built for dropshipping entrepreneurs who value simplicity, speed, and results.** 