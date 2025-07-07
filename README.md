# 🔍 eBay Scraper & Market Analyzer

A sophisticated eBay scraping application built with **Clean Architecture** principles, featuring advanced bot protection, multi-format exports, and comprehensive market analysis.

## ✨ Features

### 🏗️ **Clean Architecture & SOLID Principles**
- **Domain-driven design** with clear separation of concerns
- **Dependency injection** with IoC container
- **Interface-based programming** for easy testing and extension
- **Async-first** architecture for high performance

### 📊 **Advanced Scraping Capabilities**
- **Multi-source scraping**: Terapeak (authenticated) + fallback public search
- **Multi-marketplace support**: eBay.com, eBay.co.uk, eBay.de, etc.
- **Comprehensive data extraction**: Product details, sold counts, seller info
- **Market analysis**: Price trends, sell-through rates, seller analytics

### 🛡️ **Sophisticated Bot Protection**
- **Intelligent user agent rotation** with health tracking
- **Human-like behavior simulation**: Mouse movements, scrolling patterns
- **CAPTCHA detection & manual intervention** workflow
- **Rate limiting** with exponential backoff
- **Session management** with cookie persistence

### 💾 **Persistent Storage & Data Management**
- **SQLite database** for historical data storage
- **Structured logging** with JSON output and rotation
- **Data export** in multiple formats (CSV, XLSX, HTML, JSON)
- **CLI interface** for data management and analysis

### 🔐 **Authentication & Session Management**
- **Automated eBay login** with 2FA support
- **Session cookie persistence** and refresh
- **Multi-marketplace authentication**

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js** (for Playwright browser installation)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd ebay-scraper
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Playwright browsers:**
```bash
playwright install chromium
```

4. **Create environment file:**
```bash
cp .env.example .env
# Edit .env with your eBay credentials (optional)
```

### 🏃‍♂️ **Quick Demo**
```bash
# Start the simple demo server
python simple_app.py
```
Visit `http://localhost:8000` for a quick demo with mock data.

### 🎯 **Production Usage**

#### **Web Interface**
```bash
# Start the full application
python main.py
```
Access the web interface at `http://localhost:8000`

#### **Command Line Interface**
```bash
# View scraping history
python -m src history --keyword "phone case" --limit 10

# Export results
python -m src export <result_id> --format csv --output my_export.csv

# Search historical data
python -m src search --keyword "wireless" --min-price 10 --max-price 50

# System status
python -m src status --detailed

# Usage statistics
python -m src stats --days 30
```

## 📋 API Documentation

### **Web API Endpoints**

#### **Search & Scraping**
```http
POST /api/v1/scrape
Content-Type: application/json

{
  "keyword": "wireless headphones",
  "marketplace": "ebay.com",
  "max_results": 20,
  "min_price": 10.00,
  "max_price": 100.00,
  "condition": "new",
  "sold_listings_only": true
}
```

#### **Historical Data**
```http
GET /api/v1/history?keyword=phone&limit=10
GET /api/v1/export?result_id=<id>&format=csv
GET /api/v1/health
```

#### **CAPTCHA Management**
```http
POST /api/v1/captcha/solve
{
  "event_id": "captcha-event-id"
}
```

### **Response Format**
```json
{
  "status": "success",
  "result_id": "uuid-string",
  "data": {
    "products_found": 15,
    "scraping_duration": 12.3,
    "market_analysis": {
      "avg_sold_price": 45.99,
      "sell_through_rate": 78.5
    }
  }
}
```

## 🛠️ Architecture Overview

```
┌─────────────────────────────────────────┐
│           Presentation Layer            │  ← Web UI, CLI, API
├─────────────────────────────────────────┤
│           Application Layer             │  ← Business Logic, Orchestration
├─────────────────────────────────────────┤
│              Domain Layer               │  ← Core Models, Interfaces
├─────────────────────────────────────────┤
│          Infrastructure Layer           │  ← External Services, Database
└─────────────────────────────────────────┘
```

### **Key Components**

#### **Domain Layer** (`src/domain/`)
- **Models**: `Product`, `ScrapingResult`, `SearchCriteria`
- **Interfaces**: 15+ service contracts
- **Exceptions**: Custom error hierarchy

#### **Application Layer** (`src/application/`)
- **ScrapingOrchestrator**: Main workflow coordination
- **KeywordInputService**: Input validation and processing

#### **Infrastructure Layer** (`src/infrastructure/`)
- **DatabaseStorageService**: SQLite persistence
- **EbayLoginService**: Automated authentication
- **CaptchaHandlerService**: CAPTCHA detection & handling
- **UserAgentHealthTracker**: Intelligent UA rotation
- **ExportService**: Multi-format data export
- **BotProtectionService**: Anti-detection measures

## 🔧 Configuration

### **Environment Variables**
```env
# eBay Authentication (Optional)
EBAY_USERNAME=your_username
EBAY_PASSWORD=your_password

# Scraping Configuration
SCRAPING_MAX_CONCURRENT_REQUESTS=3
SCRAPING_REQUEST_TIMEOUT=30.0

# Bot Protection
BOT_PROTECTION_MIN_DELAY=1.0
BOT_PROTECTION_MAX_DELAY=5.0

# Web Server
WEB_HOST=127.0.0.1
WEB_PORT=8000
WEB_DEBUG=false

# Database
DATABASE_PATH=data/ebay_scraper.db

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true
LOG_FILE_PATH=logs/ebay_scraper.log
```

### **Advanced Configuration**
See `config/settings.py` for comprehensive configuration options including:
- Retry logic parameters
- Rate limiting settings
- User agent rotation
- Export formats
- Marketplace configurations

## 📊 Data Export Formats

### **CSV Export**
```bash
python -m src export <result_id> --format csv
```
- Flat table structure
- Configurable columns
- Metadata file included

### **Excel Export**
```bash
python -m src export <result_id> --format xlsx
```
- Multiple sheets (Products, Analysis, Summary)
- Rich formatting and charts
- Statistical analysis

### **HTML Report**
```bash
python -m src export <result_id> --format html
```
- Bootstrap-styled report
- Interactive tables
- Embedded charts and statistics

### **JSON Export**
```bash
python -m src export <result_id> --format json
```
- Complete structured data
- API-friendly format
- Hierarchical organization

## 🛡️ Bot Protection Features

### **Multi-Layer Defense**
1. **Request Timing**: Random delays with jitter
2. **User Agent Rotation**: Health-tracked rotation pool
3. **Behavioral Simulation**: Mouse movements, scrolling
4. **CAPTCHA Handling**: Automatic detection + manual solving
5. **Session Management**: Cookie persistence and refresh

### **User Agent Health Tracking**
```bash
# View user agent health statistics
python -m src status --detailed
```

The system automatically tracks:
- Detection events per user agent
- Success/failure ratios
- Automatic rotation of "tainted" agents
- Health score calculation

### **CAPTCHA Workflow**
1. **Automatic Detection**: Multiple detection methods
2. **Manual Intervention**: Web UI for manual solving
3. **Workflow Pause**: Scraping pauses until resolved
4. **Automatic Resume**: Continues after manual solve

## 📈 Market Analysis Features

### **Comprehensive Analytics**
- **Price Statistics**: Min, max, average, median prices
- **Sell-Through Rates**: Success rates and demand metrics
- **Seller Analytics**: Top sellers, feedback analysis
- **Trend Analysis**: Historical price and volume trends
- **Market Segmentation**: By condition, category, location

### **Data Visualization**
- **Price Distribution**: Histograms and box plots
- **Sold Count Analysis**: Volume distribution charts
- **Seller Performance**: Top performer rankings
- **Time Series**: Historical trend analysis

## 🧪 Testing & Development

### **Running Tests**
```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

### **Code Quality**
```bash
# Format code
black src/

# Type checking
mypy src/

# Linting
flake8 src/
```

### **Development Mode**
```bash
# Start with hot reload
python main.py --debug
```

## 🔮 Advanced Usage

### **Custom Marketplace Configuration**
```python
# Add new marketplace
from src.domain.models import Marketplace

class CustomMarketplace:
    BASE_URL = "https://ebay.ca"
    SEARCH_PATH = "/sch/"
    TERAPEAK_URL = "https://ebay.ca/sch/research"
```

### **Custom Export Formats**
```python
# Implement IExportService
class CustomExportService(IExportService):
    async def export_to_xml(self, result: ScrapingResult, file_path: str):
        # Custom XML export implementation
        pass
```

### **Plugin Architecture**
The clean architecture supports easy extension:
- Custom scrapers via `IProductScraper`
- New storage backends via `IDataStorage`
- Custom analyzers via `IMarketAnalyzer`

## 📚 CLI Reference

### **History Commands**
```bash
# View all history
python -m src history

# Filter by keyword
python -m src history --keyword "phone"

# JSON output
python -m src history --format json --limit 50

# CSV export
python -m src history --format csv > history.csv
```

### **Export Commands**
```bash
# Basic export
python -m src export abc123 --format csv

# Custom output path
python -m src export abc123 --format xlsx --output /path/to/export.xlsx

# Multiple formats
for fmt in csv xlsx html json; do
    python -m src export abc123 --format $fmt
done
```

### **Search Commands**
```bash
# Basic search
python -m src search --keyword "wireless"

# Price filtering
python -m src search --min-price 10 --max-price 100

# Large result set
python -m src search --keyword "phone" --limit 1000
```

### **System Commands**
```bash
# Basic status
python -m src status

# Detailed status
python -m src status --detailed

# Usage statistics
python -m src stats --days 7
```

## 🤝 Contributing

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow SOLID principles** and clean architecture
4. **Add tests** for new functionality
5. **Update documentation**
6. **Submit pull request**

### **Development Guidelines**
- Follow **Clean Architecture** patterns
- Use **dependency injection** for all services
- Write **comprehensive tests**
- Document **public APIs**
- Follow **PEP 8** style guidelines

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Users are responsible for complying with eBay's Terms of Service and robots.txt. Use responsibly and respect rate limits.

## 🆘 Support & Troubleshooting

### **Common Issues**

**CAPTCHA Detected**
```bash
# Check CAPTCHA status
python -m src status --detailed

# Manual intervention required via web UI
# Navigate to http://localhost:8000/captcha
```

**Rate Limited**
```bash
# Check current delays
python -m src status

# Increase delays in configuration
# Edit BOT_PROTECTION_MIN_DELAY and BOT_PROTECTION_MAX_DELAY
```

**Database Issues**
```bash
# Reset database
rm data/ebay_scraper.db
python -m src status  # Will recreate database
```

### **Performance Tuning**
- Adjust `SCRAPING_MAX_CONCURRENT_REQUESTS` (1-5)
- Increase `BOT_PROTECTION_MIN_DELAY` for better stealth
- Use `--headless=false` for debugging login issues

### **Debugging**
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python main.py

# View detailed logs
tail -f logs/ebay_scraper.log
```

---

**Built with ❤️ using Clean Architecture and SOLID principles** 