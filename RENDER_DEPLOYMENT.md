# Deploying Genshin Impact Personal Assistant API to Render.com

This guide will help you deploy your Genshin Impact API to Render.com.

## Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **Render.com Account**: Sign up at [render.com](https://render.com)
3. **MongoDB Atlas**: Set up a MongoDB database (free tier available)
4. **Google API Keys**: For Gemini AI and Custom Search

## Step 1: Prepare Your Environment Variables

You'll need these environment variables in Render:

### Required Variables:
```
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
MONGODB_PASSWORD=your_mongodb_password
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
GOOGLE_CSE_API_KEY=your_custom_search_api_key
```

### Optional Variables:
```
REDIS_URL=redis://localhost:6379  # Or use Render Redis add-on
ENVIRONMENT=production
```

## Step 2: Deploy to Render

### Option A: Using render.yaml (Recommended)

1. **Push your code** to GitHub with the `render.yaml` file
2. **Go to Render Dashboard** → "New" → "Blueprint"
3. **Connect your GitHub repository**
4. **Render will automatically detect** the `render.yaml` file
5. **Set your environment variables** in the Render dashboard
6. **Deploy!**

### Option B: Manual Setup

1. **Go to Render Dashboard** → "New" → "Web Service"
2. **Connect your GitHub repository**
3. **Configure the service:**
   - **Name**: `genshin-lm-api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python render_start.py`
   - **Plan**: Free (or higher for production)

4. **Set Environment Variables** in the "Environment" tab
5. **Deploy!**

## Step 3: Set Up External Services

### MongoDB Atlas (Free Tier)
1. Go to [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Create a free cluster
3. Create a database user
4. Get your connection string
5. Add it as `MONGODB_URL` in Render

### Redis (Optional)
- **Option 1**: Use Render's Redis add-on
- **Option 2**: Use Redis Cloud free tier
- **Option 3**: Skip Redis (some caching features won't work)

### Google APIs
1. **Google AI Studio**: Get your Gemini API key
2. **Google Custom Search**: Set up CSE for web search features

## Step 4: Configure Your Service

### Health Checks
The API includes a health check endpoint at `/health` that Render will use to monitor your service.

### Logs
View logs in the Render dashboard under your service → "Logs"

### Custom Domain (Optional)
You can add a custom domain in the Render dashboard under "Settings"

## Step 5: Post-Deployment

### Test Your API
Your API will be available at: `https://your-service-name.onrender.com`

Test endpoints:
- `GET /health` - Health check
- `GET /api/endpoints` - API documentation
- `POST /users` - Create user profile

### Monitor Performance
- Check logs for any errors
- Monitor response times
- Set up alerts if needed

## Troubleshooting

### Common Issues:

1. **Build Fails**
   - Check `requirements.txt` for invalid packages
   - Ensure Python version compatibility

2. **Service Won't Start**
   - Check environment variables are set correctly
   - Verify MongoDB connection string
   - Check logs for specific errors

3. **Database Connection Issues**
   - Verify MongoDB Atlas IP whitelist (set to 0.0.0.0/0 for Render)
   - Check connection string format
   - Ensure database user has proper permissions

4. **API Key Issues**
   - Verify all required API keys are set
   - Check API key permissions and quotas

### Performance Tips:

1. **Free Tier Limitations**:
   - Service sleeps after 15 minutes of inactivity
   - 750 hours/month limit
   - Consider upgrading for production use

2. **Optimization**:
   - Use Redis for caching
   - Implement proper error handling
   - Monitor API usage

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `MONGODB_URL` | Yes | MongoDB connection string |
| `MONGODB_PASSWORD` | Yes | MongoDB password |
| `GOOGLE_API_KEY` | Yes | Google Gemini API key |
| `GOOGLE_CSE_ID` | Yes | Custom Search Engine ID |
| `GOOGLE_CSE_API_KEY` | Yes | Custom Search API key |
| `REDIS_URL` | No | Redis connection string |
| `ENVIRONMENT` | No | Set to "production" |
| `PORT` | No | Auto-set by Render |

## Support

If you encounter issues:
1. Check the Render logs
2. Verify all environment variables
3. Test locally first
4. Check Render's status page for outages

Your API should now be live and accessible! 🚀 