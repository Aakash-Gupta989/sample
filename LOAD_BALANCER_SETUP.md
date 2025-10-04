# 🔄 Load Balancer Setup Guide

## Overview
This guide sets up a **free load balancer** using multiple Render instances and frontend load balancing.

## Architecture
```
Frontend (Vercel) → Load Balancer → Multiple Backend Instances
                                    ├── Backend 1 (Render)
                                    ├── Backend 2 (Render) 
                                    └── Backend 3 (Render)
```

## Step 1: Create Additional Render Instances

### 1.1 Create Backend 2
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New +" → "Web Service"
3. Connect to your GitHub repository
4. Configure:
   - **Name**: `prepandhire-backend-2`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements-render.txt`
   - **Start Command**: `cd backend && python start_render.py`
   - **Plan**: Free
5. Add Environment Variables:
   - `GROQ_API_KEY`: (same as backend 1)
   - `INSTANCE_ID`: `backend-2`
6. Deploy

### 1.2 Create Backend 3
1. Repeat steps 1.1 but with:
   - **Name**: `prepandhire-backend-3`
   - `INSTANCE_ID`: `backend-3`

## Step 2: Update Frontend Configuration

### 2.1 Update Load Balancer URLs
Edit `frontend/src/utils/loadBalancer.js`:
```javascript
this.backends = [
  {
    name: 'backend-1',
    url: 'https://prepandhirebackend.onrender.com', // Your actual URL
    healthy: true,
    lastCheck: Date.now(),
    weight: 1
  },
  {
    name: 'backend-2', 
    url: 'https://prepandhirebackend2.onrender.com', // Your actual URL
    healthy: true,
    lastCheck: Date.now(),
    weight: 1
  },
  {
    name: 'backend-3',
    url: 'https://prepandhirebackend3.onrender.com', // Your actual URL
    healthy: true,
    lastCheck: Date.now(),
    weight: 1
  }
];
```

## Step 3: Test Load Balancer

### 3.1 Health Check
Visit each backend's health endpoint:
- `https://prepandhirebackend.onrender.com/health`
- `https://prepandhirebackend2.onrender.com/health`
- `https://prepandhirebackend3.onrender.com/health`

### 3.2 Load Balancer Status
Open browser console and run:
```javascript
import loadBalancer from './utils/loadBalancer';
console.log(loadBalancer.getStatus());
```

## Step 4: Deploy Updates

### 4.1 Commit Changes
```bash
git add .
git commit -m "Add load balancer support"
git push origin main
```

### 4.2 Verify Deployment
1. Check Vercel deployment status
2. Test interview flow
3. Monitor console for load balancer logs

## Benefits

✅ **High Availability**: 3x better uptime
✅ **Automatic Failover**: If 1 backend fails, others continue
✅ **Load Distribution**: Requests spread across backends
✅ **Zero Cost**: All free tier services
✅ **Health Monitoring**: Automatic backend health checks

## Monitoring

### Backend Health
- Each backend has `/health` endpoint
- Frontend checks health every 30 seconds
- Unhealthy backends are automatically excluded

### Load Balancer Logs
- Check browser console for load balancer activity
- Look for `🔄 Load Balancer:` messages
- Monitor failover events

## Troubleshooting

### Backend Not Responding
1. Check Render dashboard for service status
2. Verify environment variables
3. Check logs for errors

### Load Balancer Issues
1. Check browser console for errors
2. Verify backend URLs in loadBalancer.js
3. Test individual backend endpoints

### Performance Issues
1. Monitor Render service metrics
2. Check for memory/CPU limits
3. Consider upgrading to paid plans if needed

## Next Steps

1. **Monitor Performance**: Track response times and error rates
2. **Scale Up**: Add more backends if needed
3. **Optimize**: Fine-tune load balancing algorithm
4. **Alerting**: Set up monitoring alerts for failures
