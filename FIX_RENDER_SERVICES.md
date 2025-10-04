# 🔧 Fix Render Services: sample & sample1

## Problem
The `sample` and `sample1` services are returning 404 errors because they were created as **static web services** instead of **backend services**.

## Solution Steps

### Step 1: Delete Existing Services
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Find the `sample` service
3. Click on it → Settings → Delete Service
4. Repeat for `sample1` service

### Step 2: Create New Backend Services

#### For `sample` service:
1. Click "New +" → "Web Service"
2. Connect to your GitHub repository: `Aakash-Gupta989/sample`
3. Configure:
   - **Name**: `sample`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements-render.txt`
   - **Start Command**: `cd backend && python start_render.py`
   - **Plan**: Free
4. Add Environment Variables:
   - `GROQ_API_KEY`: (same as your main backend)
   - `INSTANCE_ID`: `sample`
5. Click "Create Web Service"

#### For `sample1` service:
1. Click "New +" → "Web Service"
2. Connect to your GitHub repository: `Aakash-Gupta989/sample`
3. Configure:
   - **Name**: `sample1`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements-render.txt`
   - **Start Command**: `cd backend && python start_render.py`
   - **Plan**: Free
4. Add Environment Variables:
   - `GROQ_API_KEY`: (same as your main backend)
   - `INSTANCE_ID`: `sample1`
5. Click "Create Web Service"

### Step 3: Wait for Deployment
- Each service will take 5-10 minutes to deploy
- Monitor the build logs for any errors
- Ensure both services show "Live" status

### Step 4: Test Health Endpoints
Once deployed, test these URLs:
- `https://sample.onrender.com/health`
- `https://sample1.onrender.com/health`

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "instance_id": "sample"
}
```

### Step 5: Update Load Balancer
Once both services are working, I'll update the load balancer configuration to include all three backends.

## Alternative: Quick Fix
If you want to keep the existing services, you can:
1. Go to each service's Settings
2. Change the **Build Command** to: `pip install -r backend/requirements-render.txt`
3. Change the **Start Command** to: `cd backend && python start_render.py`
4. Add the environment variables
5. Redeploy the services

## Expected Results
After fixing, you should have:
- ✅ `https://prepandhirebackend.onrender.com/health` (working)
- ✅ `https://sample.onrender.com/health` (working)
- ✅ `https://sample1.onrender.com/health` (working)

All three backends will be healthy and the load balancer will distribute traffic across them.
