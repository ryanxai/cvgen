# Deployment Guide

This guide explains how to set up automatic deployment to Fly.io using GitHub Actions with secrets management.

## Prerequisites

1. **Fly.io Account**: You need a Fly.io account and the `flyctl` CLI installed
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **API Keys**: You need the required API keys for your application

## Setting Up GitHub Secrets

### 1. Required Secrets

You need to add the following secrets to your GitHub repository:

#### FLY_API_TOKEN
- **Purpose**: Allows GitHub Actions to deploy to Fly.io
- **How to get it**: Run `flyctl auth token` locally
- **Where to add**: GitHub repository → Settings → Secrets and variables → Actions → New repository secret

#### OPENROUTER_API_KEY
- **Purpose**: API key for OpenRouter (used for LLM features)
- **How to get it**: Sign up at https://openrouter.ai/ and get your API key
- **Where to add**: GitHub repository → Settings → Secrets and variables → Actions → New repository secret

### 2. How to Add Secrets

1. Go to your GitHub repository
2. Click on **Settings** tab
3. In the left sidebar, click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add each secret:
   - **Name**: `FLY_API_TOKEN`
   - **Value**: Your Fly.io API token
   - **Name**: `OPENROUTER_API_KEY`
   - **Value**: Your OpenRouter API key

## Automatic Deployment

### How It Works

1. **Push to main branch**: Any push to the `main` branch triggers deployment
2. **Manual deployment**: You can also trigger deployment manually from the Actions tab
3. **Secrets management**: The workflow automatically sets Fly.io secrets from GitHub secrets
4. **Health check**: After deployment, it performs a health check to ensure the app is running

### Workflow Steps

1. **Checkout code**: Gets the latest code from your repository
2. **Setup Fly.io CLI**: Installs and configures the Fly.io CLI
3. **Set secrets**: Transfers GitHub secrets to Fly.io secrets
4. **Deploy**: Deploys the application to Fly.io
5. **Health check**: Verifies the deployment was successful

## Manual Deployment

If you need to deploy manually:

```bash
# Set secrets manually
flyctl secrets set OPENROUTER_API_KEY=your_api_key_here

# Deploy
flyctl deploy
```

## Troubleshooting

### Common Issues

1. **"OPENROUTER_API_KEY secret not found"**
   - Solution: Add the secret to your GitHub repository secrets

2. **"FLY_API_TOKEN not found"**
   - Solution: Generate a new token with `flyctl auth token` and add it to GitHub secrets

3. **Deployment fails**
   - Check the GitHub Actions logs for detailed error messages
   - Verify all secrets are properly set

### Checking Deployment Status

- **GitHub Actions**: Go to Actions tab in your repository
- **Fly.io Dashboard**: https://fly.io/apps/cvgen-c-jysq/monitoring
- **Health Check**: https://cvgen-c-jysq.fly.dev/health

## Environment Variables

The application supports these environment variables:

- `OPENROUTER_API_KEY`: Required for LLM features
- `PORT`: Port to run the application on (default: 8000)
- `OUTPUT_DIR`: Directory for generated files (default: current directory)

## Security Notes

- Never commit API keys to your repository
- Use GitHub secrets for sensitive data
- Regularly rotate your API keys
- Monitor your Fly.io usage and costs 