# Deployment Troubleshooting Guide

## Current Issue: Pip Upgrade Failure

The deployment is failing at the very first step: `python -m pip install --upgrade pip`. This indicates a fundamental issue with the Python environment in Railway.

## Quick Fixes to Try

### 1. Use Simplified Nixpacks Configuration

The updated `nixpacks.toml` removes the problematic pip upgrade step:

```toml
[variables]
PYTHONPATH = "."
ENVIRONMENT = "production"
USE_MOCK_DATA = "false"

[phases.setup]
cmds = [
    "mkdir -p data logs output"
]

[phases.install]
cmds = [
    "pip install -r requirements.txt"
]

[phases.build]
cmds = [
    "python -c 'import sys; print(f\"Python version: {sys.version}\")'",
    "python -c 'print(\"✅ Build verification complete\")'"
]

[start]
cmd = "python start_production.py"
```

### 2. Switch to Docker Deployment

If Nixpacks continues to fail, switch to Docker deployment:

1. **Rename the configuration**:
   ```bash
   mv railway.json railway-nixpacks.json
   mv railway-docker.json railway.json
   ```

2. **Deploy with Docker**: Railway will now use the `Dockerfile` instead of Nixpacks

### 3. Alternative Deployment Commands

Try these alternative start commands in Railway:

**Option A: With dependency verification**
```bash
python deploy_verify.py && python start_production.py
```

**Option B: Minimal deployment**
```bash
python simple_deploy.py
```

**Option C: Manual dependency installation**
```bash
pip install -r requirements.txt && python start_production.py
```

## Common Issues and Solutions

### Issue 1: Pip Upgrade Fails

**Symptoms**: `python -m pip install --upgrade pip` fails

**Solutions**:
1. ✅ **FIXED**: Removed pip upgrade from nixpacks.toml
2. Use Docker deployment instead
3. Try a different Python version
4. Use a simpler requirements.txt

### Issue 2: aiosqlite Installation Fails

**Symptoms**: `aiosqlite missing` error

**Solutions**:
1. Check if the Python version supports aiosqlite
2. Try installing system dependencies first
3. Use an alternative database like SQLite3

### Issue 3: Build Timeout

**Symptoms**: Build process times out

**Solutions**:
1. Reduce the number of dependencies
2. Use a simpler requirements.txt
3. Split the build into smaller phases

### Issue 4: Python Version Compatibility

**Symptoms**: Import errors for basic packages

**Solutions**:
1. Specify Python version in nixpacks.toml
2. Use compatible package versions
3. Test locally with the same Python version

## Debugging Steps

### Step 1: Run Verification Script

```bash
python deploy_verify.py
```

This will show you:
- Python environment details
- Installed packages
- File system access
- Environment variables

### Step 2: Check Local Installation

Test locally to ensure dependencies work:

```bash
pip install -r requirements.txt
python -c "import aiosqlite; print('aiosqlite works')"
```

### Step 3: Simplify Requirements

If the issue persists, try a minimal `requirements.txt`:

```txt
quart==0.19.4
aiosqlite==0.19.0
pydantic==2.5.2
```

## Alternative Deployment Strategies

### Strategy 1: Docker Deployment (RECOMMENDED)

If Railway continues to have issues, use Docker:

1. ✅ **Dockerfile created** with Python 3.11
2. ✅ **railway-docker.json** configuration ready
3. More control over the environment
4. Better dependency management

**To switch to Docker**:
```bash
# Backup current config
mv railway.json railway-nixpacks.json
# Use Docker config
mv railway-docker.json railway.json
# Deploy
```

### Strategy 2: Other Platforms

Consider alternative platforms:
- **Render**: Good Python support
- **Heroku**: Mature Python deployment
- **DigitalOcean App Platform**: Simple deployment

### Strategy 3: Manual Server Setup

For full control:
1. Set up a VPS (DigitalOcean, AWS, etc.)
2. Install dependencies manually
3. Use systemd for process management

## Immediate Action Plan

1. **Try the simplified nixpacks.toml** (removes pip upgrade)
2. **If that fails, switch to Docker deployment**
3. **Check Railway logs** for specific error messages
4. **Run the verification script** to diagnose issues
5. **Consider minimal deployment** if full deployment fails
6. **Explore alternative platforms** if issues persist

## Docker Deployment Benefits

- ✅ **More reliable**: Better control over the environment
- ✅ **Faster builds**: Optimized with .dockerignore
- ✅ **Better caching**: Dependencies cached separately
- ✅ **Health checks**: Built-in health monitoring
- ✅ **System dependencies**: Can install required system packages

## Success Metrics

Your deployment is successful when:
- ✅ Application starts without errors
- ✅ All critical dependencies are available
- ✅ Web interface is accessible
- ✅ Database operations work
- ✅ Scraping functionality is available (if not in minimal mode) 