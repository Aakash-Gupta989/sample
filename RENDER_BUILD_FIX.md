# 🔧 Render Build Fix Instructions

## Problem
The service is still using cached requirements with Pillow, causing build failures.

## Solution
Update the Build Command in Render dashboard to use the new ultra-light requirements file.

### Step 1: Update Build Command
1. Go to your `sample1` service in Render dashboard
2. Click **Settings** tab
3. Change **Build Command** from:
   ```
   pip install -r backend/requirements-render.txt
   ```
   To:
   ```
   pip install -r backend/requirements-ultra-light.txt
   ```
4. Click **Save Changes**

### Step 2: Redeploy
1. Go to **Manual Deploy** tab
2. Click **Deploy latest commit**
3. Watch the build logs

### Step 3: Expected Results
- ✅ Build should complete in 2-3 minutes
- ✅ No Pillow compilation errors
- ✅ Service shows "Live" status
- ✅ Health endpoint works

### Alternative: Force Fresh Build
If the above doesn't work:
1. **Delete the service completely**
2. **Create a new Web Service** with:
   - **Build Command**: `pip install -r backend/requirements-ultra-light.txt`
   - **Start Command**: `cd backend && python start_render.py`
   - **Environment Variables**: `GROQ_API_KEY` and `INSTANCE_ID=sample1`

## What This Achieves
- **No Compilation**: Only pure Python packages
- **Fast Build**: 2-3 minutes instead of 10+ minutes
- **Reliable**: No Rust/C++ compilation issues
- **Lightweight**: Perfect for Render free tier
