# 🚀 Deploy to Railway - Easy Python Web App Hosting

## Why Railway is Perfect for Your eBay Scraper:
- ✅ **Python support** - Runs your Quart server perfectly
- ✅ **Database included** - PostgreSQL or keep SQLite
- ✅ **Playwright support** - Handles browser automation
- ✅ **Easy deployment** - Connect GitHub and deploy
- ✅ **Free tier** - Start free, scale as needed
- ✅ **Custom domain** - Get your own URL

## 🎯 **Step-by-Step Railway Deployment:**

### **Step 1: Prepare Your Project**

Create these files in your project root:

**`requirements.txt`** (if not exists):
```txt
quart==0.19.4
playwright==1.40.0
aiosqlite==0.19.0
pydantic==2.5.2
structlog==23.2.0
```

**`railway.json`** (Railway configuration):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python main.py",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**`Procfile`** (Process configuration):
```
web: python main.py
```

**`.railwayignore`** (Ignore unnecessary files):
```
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.env
.venv
env/
venv/
.git/
.gitignore
README.md
*.md
.DS_Store
data/*.db
logs/
```

### **Step 2: Update main.py for Production**

Update your `main.py` to work with Railway:

```python
import os
import asyncio
from src.presentation.web_app import WebApp

async def main():
    """Main application entry point."""
    app = WebApp()
    await app.initialize()
    
    # Get port from environment (Railway provides this)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"  # Required for Railway
    
    print(f"🚀 Starting eBay Scraper on {host}:{port}")
    
    # Run with Hypercorn for production
    try:
        import hypercorn.asyncio
        config = hypercorn.Config()
        config.bind = [f"{host}:{port}"]
        config.use_reloader = False
        await hypercorn.asyncio.serve(app.app, config)
    except ImportError:
        # Fallback to development server
        await app.app.run_task(host=host, port=port)

if __name__ == "__main__":
    asyncio.run(main())
```

### **Step 3: Deploy to Railway**

1. **Sign up at Railway.app**
   - Visit: https://railway.app/
   - Sign up with GitHub

2. **Create New Project**
   - Click "Deploy from GitHub repo"
   - Select your eBay scraper repository
   - Railway auto-detects it's a Python app

3. **Set Environment Variables**
   ```
   USE_MOCK_DATA=false
   ENVIRONMENT=production
   LOG_LEVEL=INFO
   ```

4. **Install Playwright Browsers**
   Add this to your Railway build:
   ```bash
   playwright install chromium
   ```

5. **Deploy**
   - Railway automatically deploys on git push
   - Your app will be live at: `https://your-app-name.railway.app`

### **Step 4: Access Your Deployed App**

Your eBay scraper will be live at:
```
https://your-project-name.up.railway.app
```

## 🎯 **Railway Benefits:**
- ✅ **$5/month free tier** - Perfect for testing
- ✅ **Automatic deployments** - Push to git = deploy
- ✅ **Custom domains** - Use your own domain
- ✅ **Database included** - PostgreSQL if needed
- ✅ **Metrics & logs** - Monitor your app
- ✅ **Scales automatically** - Handles traffic spikes 