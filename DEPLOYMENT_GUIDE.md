# 🚀 Deployment Guide: prepandhire.com

## Overview
This guide will help you deploy your Intelligent Interview System to:
- **Frontend**: Netlify (React app)
- **Backend**: Render (FastAPI app)
- **Domain**: prepandhire.com

## Prerequisites
- GitHub repository with your code
- Netlify account
- Render account
- Domain access to prepandhire.com
- API keys for Groq and OpenAI

## Step 1: Prepare Your Repository

### 1.1 Push to GitHub
```bash
cd /Users/aarsheebhattacharya/Downloads/New\ Project_2
git init
git add .
git commit -m "Initial commit for deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/prepandhire.git
git push -u origin main
```

### 1.2 Environment Variables
Create a `.env` file in your project root:
```bash
# OpenAI API Configuration
OPENAI_API_KEY=sk-your-actual-openai-key
OPENAI_MODEL=gpt-4o

# Groq API Configuration
GROQ_API_KEY=gsk-your-actual-groq-key

# Server Configuration
BACKEND_PORT=8000
FRONTEND_PORT=3000

# CORS Configuration (will be updated after deployment)
CORS_ORIGINS=https://prepandhire.netlify.app,https://prepandhire.com
```

## Step 2: Deploy Backend to Render

### 2.1 Create Render Service
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `prepandhire-backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && python main.py`
   - **Plan**: Free (or paid for better performance)

### 2.2 Environment Variables in Render
Add these environment variables in Render dashboard:
```
GROQ_API_KEY = gsk-your-actual-groq-key
OPENAI_API_KEY = sk-your-actual-openai-key
CORS_ORIGINS = https://prepandhire.netlify.app,https://prepandhire.com
BACKEND_PORT = 8000
```

### 2.3 Deploy
Click "Create Web Service" and wait for deployment to complete.
Note the URL: `https://prepandhire-backend.onrender.com`

## Step 3: Deploy Frontend to Netlify

### 3.1 Create Netlify Site
1. Go to [netlify.com](https://netlify.com) and sign up/login
2. Click "New site from Git"
3. Connect your GitHub repository
4. Configure build settings:
   - **Build command**: `cd frontend && npm install && npm run build`
   - **Publish directory**: `frontend/build`
   - **Node version**: 18

### 3.2 Environment Variables in Netlify
Add these environment variables in Netlify dashboard:
```
NODE_ENV = production
REACT_APP_API_URL = https://prepandhire-backend.onrender.com
```

### 3.3 Deploy
Click "Deploy site" and wait for deployment to complete.
Note the URL: `https://prepandhire.netlify.app`

## Step 4: Configure Domain (prepandhire.com)

### 4.1 Remove Existing Website
1. Access your domain registrar (GoDaddy, Namecheap, etc.)
2. Remove current DNS records pointing to the old website
3. Note down any important DNS records you want to keep

### 4.2 Point Domain to Netlify
1. In Netlify dashboard, go to "Domain settings"
2. Click "Add custom domain"
3. Enter `prepandhire.com`
4. Follow Netlify's DNS configuration instructions
5. Update your domain's DNS records as instructed

### 4.3 SSL Certificate
Netlify will automatically provision SSL certificates for your domain.

## Step 5: Update CORS Configuration

After both services are deployed, update the CORS origins in Render:
```
CORS_ORIGINS = https://prepandhire.netlify.app,https://prepandhire.com,https://www.prepandhire.com
```

## Step 6: Test Your Deployment

### 6.1 Test Backend
Visit: `https://prepandhire-backend.onrender.com/health`
Should return: `{"status": "healthy", ...}`

### 6.2 Test Frontend
Visit: `https://prepandhire.com`
Should load your React application

### 6.3 Test Full Flow
1. Start an interview
2. Test WebSocket connection
3. Test API calls
4. Test file uploads (resume, audio)

## Step 7: Performance Optimization

### 7.1 Render Optimization
- Upgrade to paid plan for better performance
- Enable auto-deploy from main branch
- Set up health checks

### 7.2 Netlify Optimization
- Enable form handling if needed
- Set up redirects for SPA routing
- Configure build caching

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Check CORS_ORIGINS in Render environment variables
   - Ensure all domains are included

2. **WebSocket Connection Failed**
   - Verify WebSocket URL in frontend config
   - Check if Render supports WebSockets (it does)

3. **API Calls Failing**
   - Check API_BASE_URL in frontend config
   - Verify backend is running and accessible

4. **Build Failures**
   - Check Node.js version compatibility
   - Verify all dependencies are in package.json

### Debug Commands
```bash
# Test backend locally
cd backend
python main.py

# Test frontend locally
cd frontend
npm start

# Check environment variables
echo $GROQ_API_KEY
echo $OPENAI_API_KEY
```

## Monitoring and Maintenance

### 7.1 Logs
- **Render**: Check logs in dashboard
- **Netlify**: Check deploy logs and function logs

### 7.2 Updates
- Push changes to main branch
- Both services will auto-deploy
- Test in staging environment first

## Cost Estimation

### Free Tier
- **Render**: 750 hours/month (free tier)
- **Netlify**: 100GB bandwidth/month (free tier)
- **Domain**: Your existing domain

### Paid Plans (if needed)
- **Render**: $7/month for always-on
- **Netlify**: $19/month for Pro features

## Security Considerations

1. **API Keys**: Never commit API keys to repository
2. **Environment Variables**: Use secure environment variable storage
3. **HTTPS**: Both services provide free SSL
4. **CORS**: Properly configure CORS origins

## Support

If you encounter issues:
1. Check service logs
2. Verify environment variables
3. Test API endpoints individually
4. Check domain DNS propagation (can take 24-48 hours)

---

**🎉 Congratulations!** Your Intelligent Interview System should now be live at prepandhire.com!
