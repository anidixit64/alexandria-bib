# Vercel Deployment Guide

This guide explains how to deploy the Alexandria-Bib project on Vercel as a single project with both frontend and backend.

## Project Structure

The project has been restructured for Vercel deployment:

```
alexandria-bib/
├── api/
│   ├── index.py          # Main serverless function handling all API routes
│   └── requirements.txt  # Python dependencies for serverless functions
├── src/                  # React frontend source code
├── public/              # Static assets
├── package.json         # Frontend dependencies and build scripts
├── vercel.json          # Vercel configuration
└── README.md
```

## Deployment Steps

### 1. Install Vercel CLI (if not already installed)

```bash
npm install -g vercel
```

### 2. Login to Vercel

```bash
vercel login
```

### 3. Deploy the Project

From the project root directory:

```bash
vercel
```

Or for production deployment:

```bash
vercel --prod
```

### 4. Environment Variables (Optional)

If you need to set environment variables (like Redis configuration), you can do so in the Vercel dashboard or via CLI:

```bash
vercel env add REDIS_HOST
vercel env add REDIS_PORT
vercel env add REDIS_DB
```

## How It Works

### Backend (Serverless Functions)
- The Flask backend has been converted to serverless functions in the `api/` directory
- All API routes are handled by `api/index.py`
- The functions are automatically deployed and scaled by Vercel

### Frontend (Static Build)
- The React frontend is built using `npm run build`
- The built files are served as static assets
- The frontend automatically uses relative URLs for API calls in production

### Routing
- API routes (`/api/*`) are routed to the serverless functions
- All other routes are served the React app (for client-side routing)

## Configuration Files

### vercel.json
```json
{
  "version": 2,
  "builds": [
    {
      "src": "api/**/*.py",
      "use": "@vercel/python"
    },
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/index.py"
    },
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### package.json
The build script has been updated to include:
```json
{
  "scripts": {
    "vercel-build": "npm run build"
  }
}
```

## Local Development

For local development, you can still use the original setup:

```bash
# Install dependencies
npm run dev:install

# Start both frontend and backend
npm run start
```

## Troubleshooting

### Common Issues

1. **Build Failures**: Make sure all dependencies are properly listed in `package.json` and `api/requirements.txt`

2. **API Errors**: Check that the serverless functions are properly handling CORS and request formats

3. **Routing Issues**: Ensure the `vercel.json` routes are correctly configured

### Debugging

- Check Vercel function logs in the dashboard
- Use `vercel logs` to view deployment logs
- Test API endpoints directly using the Vercel function URLs

## Performance Considerations

- Serverless functions have cold start times
- Consider implementing caching strategies for frequently accessed data
- Monitor function execution times and memory usage

## Security

- API keys and sensitive data should be stored as environment variables
- CORS is configured to allow requests from the frontend domain
- Rate limiting is implemented in the serverless functions 