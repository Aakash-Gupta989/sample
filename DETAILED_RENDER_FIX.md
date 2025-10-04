# 🔧 Detailed Render Service Fix Guide

## Step-by-Step Instructions

### Step 1: Access Render Dashboard
1. Go to https://dashboard.render.com
2. Log in with your account
3. You should see your services listed

### Step 2: Fix `sample` Service
1. **Find the `sample` service** in your dashboard
2. **Click on the service name** (not the URL)
3. **Click "Settings" tab** (usually on the left sidebar)
4. **Update Build Command:**
   - Find "Build Command" field
   - Replace existing command with: `pip install -r backend/requirements-render.txt`
5. **Update Start Command:**
   - Find "Start Command" field  
   - Replace existing command with: `cd backend && python start_render.py`
6. **Click "Save Changes"** button
7. **Go to "Environment" tab**
8. **Add Environment Variables:**
   - Click "Add Environment Variable"
   - Key: `GROQ_API_KEY`, Value: (copy from your main backend)
   - Click "Add Environment Variable" again
   - Key: `INSTANCE_ID`, Value: `sample`
9. **Click "Save Changes"**
10. **Go to "Manual Deploy" tab**
11. **Click "Deploy latest commit"**

### Step 3: Fix `sample1` Service
1. **Find the `sample1` service** in your dashboard
2. **Click on the service name**
3. **Click "Settings" tab**
4. **Update Build Command:** `pip install -r backend/requirements-render.txt`
5. **Update Start Command:** `cd backend && python start_render.py`
6. **Click "Save Changes"**
7. **Go to "Environment" tab**
8. **Add Environment Variables:**
   - `GROQ_API_KEY`: (same value as main backend)
   - `INSTANCE_ID`: `sample1`
9. **Click "Save Changes"**
10. **Go to "Manual Deploy" tab**
11. **Click "Deploy latest commit"**

### Step 4: Monitor Deployment
- Watch the build logs for each service
- Look for "pip install" messages
- Wait for "Live" status
- Each service takes 5-10 minutes

### Step 5: Test Services
Once both are "Live", test these URLs:
- https://sample.onrender.com/health
- https://sample1.onrender.com/health

Expected response:
```json
{
  "status": "healthy",
  "instance_id": "sample"
}
```

## Troubleshooting

### If you can't find the services:
- Check if they're in a different Render account
- Look for services with different names
- Check the "Services" section in dashboard

### If settings are grayed out:
- Make sure you're the owner of the services
- Check if services are paused/suspended
- Try refreshing the page

### If deployment fails:
- Check build logs for errors
- Ensure GROQ_API_KEY is correct
- Verify the repository is connected properly

## What You Should See After Fix:
- ✅ sample.onrender.com/health returns JSON
- ✅ sample1.onrender.com/health returns JSON  
- ✅ Both services show "Live" status
- ✅ Load balancer will show 3/3 healthy backends
