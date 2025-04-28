# Heroku Deployment Guide

## 1. Create Heroku App

```bash
# Login to Heroku
heroku login

# Create a new app
heroku create gitdocs

# Or to use a specific app name (replace "your-app-name" with your preferred name)
heroku create your-app-name
```

## 2. Configure Environment Variables

Based on the project configuration, set these environment variables:

```bash
# S3 Configuration (required for cloud storage)
heroku config:set GITINGEST_S3_BUCKET=your-s3-bucket-name
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
heroku config:set AWS_REGION=your-aws-region

# Optional configuration
heroku config:set GITINGEST_MAX_FILES=1000
heroku config:set GITINGEST_MAX_TOTAL_SIZE_MB=50
heroku config:set GITINGEST_MAX_FILE_SIZE_MB=1
heroku config:set GITINGEST_MAX_DIRECTORY_DEPTH=10

# Allowed hosts for the application
heroku config:set ALLOWED_HOSTS=gitdocs.tech,*.gitdocs.tech,herokuapp.com,*.herokuapp.com
```

## 3. Deploy Manually

```bash
# Push to Heroku
git push heroku main

# If you're on a different branch
git push heroku yourbranchname:main
```

## 4. Open the App

```bash
heroku open
```

## 5. Check Logs if Needed

```bash
heroku logs --tail
```

## 6. Configure Custom Domain

```bash
# Add your domain
heroku domains:add gitdocs.tech

# Add www subdomain if needed
heroku domains:add www.gitdocs.tech

# Get DNS settings
heroku domains

# Configure SSL
heroku certs:auto:enable
```

Follow the DNS configuration instructions provided by Heroku to point your domain to the app.

## 7. Monitor and Scale

```bash
# Check app status
heroku ps

# Scale dynos if needed
heroku ps:scale web=2
```

## 8. GitHub Actions Setup (Optional)

Create a `.github/workflows/heroku-deploy.yml` file to automate deployments:

```yaml
name: Deploy to Heroku

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Heroku
        uses: akhileshns/heroku-deploy@v3.13.15
        with:
          heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
          heroku_app_name: "your-app-name"
          heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

Add the following secrets to your GitHub repository:
- `HEROKU_API_KEY`: Your Heroku API key
- `HEROKU_EMAIL`: Your Heroku account email 