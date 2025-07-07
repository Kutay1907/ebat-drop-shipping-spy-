# Simple eBay Dropshipping App for Railway

This is a minimal Flask web application designed specifically for Railway deployment to get a URL for the eBay Developer Program.

## Features

- ✅ Simple web interface for eBay dropshipping
- ✅ Basic search functionality
- ✅ API endpoints for eBay integration
- ✅ Webhook support for eBay notifications
- ✅ Health check endpoint

## Quick Deploy to Railway

1. Push this folder to a new GitHub repository
2. Connect Railway to your GitHub repo
3. Railway will automatically deploy the app
4. You'll get a URL like: `https://your-app.railway.app`

## API Endpoints

Use these endpoints in your eBay Developer Application:

- `GET /api/health` - Health check
- `POST /api/search` - Search products
- `GET /api/products` - List products
- `GET /api/webhook` - eBay webhook verification
- `POST /api/webhook` - Receive eBay notifications

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

The app will be available at `http://localhost:5000`

## Environment Variables

No environment variables required! The app uses Railway's automatic PORT assignment.

## Files

- `app.py` - Main Flask application
- `requirements.txt` - Python dependencies (just Flask and Gunicorn)
- `Procfile` - Tells Railway how to run the app
- `railway.json` - Railway configuration

## Why This Works

- **Minimal dependencies** - Only Flask and Gunicorn
- **No database required** - Uses mock data
- **Simple deployment** - Railway handles everything
- **eBay ready** - Has all the endpoints eBay needs 