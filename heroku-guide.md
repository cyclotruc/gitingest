# Deploying Gitingest to Heroku with Custom Domain

This guide walks you through deploying your Gitingest app to Heroku and configuring your gitdocs.tech domain.

## Deployment Process Overview

```mermaid
flowchart TD
    A[Prepare Application] --> B[Create Heroku App]
    B --> C[Configure Environment Variables]
    C --> D[Deploy Application]
    D --> E[Configure Custom Domain]
    E --> F[Test Deployment]
    F --> G[Monitor & Scale]
```

## 1. Preparation for Heroku Deployment

The following files have been created/updated for Heroku deployment:

- **Procfile**: Tells Heroku how to run the application
- **runtime.txt**: Specifies the Python version

## 2. Creating a Heroku App

```mermaid
flowchart LR
    A[Login to Heroku] --> B[Create App]
    B --> C[Set Remote]
```

Run these commands:

```bash
# Login to Heroku
heroku login

# Create app (use a unique name)
heroku create gitdocs
```

## 3. Configuring Environment Variables

```mermaid
flowchart TD
    A[Required Variables] --> B[S3 Configuration]
    A --> C[Allowed Hosts]
    A --> D[Optional App Settings]
    B --> E[Set on Heroku]
    C --> E
    D --> E
```

Based on the project code, you'll need to set these environment variables:

```bash
# S3 Configuration (required for cloud storage)
heroku config:set GITINGEST_S3_BUCKET=your-s3-bucket-name
heroku config:set AWS_ACCESS_KEY_ID=your-aws-access-key
heroku config:set AWS_SECRET_ACCESS_KEY=your-aws-secret-key
heroku config:set AWS_REGION=your-aws-region

# Allowed hosts for the application
heroku config:set ALLOWED_HOSTS=gitdocs.tech,*.gitdocs.tech,herokuapp.com,*.herokuapp.com
```

## 4. Manual Deployment to Heroku

```mermaid
flowchart TD
    A[Commit Changes] --> B[Push to Heroku]
    B --> C[Wait for Build]
    C --> D[Check Logs]
```

To deploy:

```bash
# Commit any changes
git add .
git commit -m "Prepare for Heroku deployment"

# Push to Heroku
git push heroku main

# If you're on a different branch
# git push heroku yourbranchname:main
```

## 5. Configuring Custom Domain (gitdocs.tech)

```mermaid
flowchart TD
    A[Add Domain to Heroku] --> B[Get DNS Settings]
    B --> C[Configure DNS Records]
    C --> D[Enable SSL]
```

Steps to configure your domain:

```bash
# Add your domain
heroku domains:add gitdocs.tech

# Add www subdomain (recommended)
heroku domains:add www.gitdocs.tech

# Get Heroku's DNS settings
heroku domains
```

You'll receive DNS target information from Heroku. Configure your domain with:

1. Create a CNAME record for `www.gitdocs.tech` pointing to the Heroku DNS target
2. Create an ALIAS/ANAME record for `gitdocs.tech` (apex domain) pointing to the same target
3. If ALIAS/ANAME isn't supported, use the IP addresses provided by Heroku with A records

Then enable SSL:

```bash
heroku certs:auto:enable
```

## 6. Testing Your Deployment

```mermaid
flowchart LR
    A[Open App] --> B[Check Logs]
    B --> C[Verify Functionality]
```

```bash
# Open your app
heroku open

# Check logs if there are issues
heroku logs --tail
```

## 7. Monitoring and Scaling

```mermaid
flowchart TD
    A[Monitor Usage] --> B[Scale if Needed]
    B --> C[Adjust Resources]
```

```bash
# Check app status
heroku ps

# Scale dynos if needed (uses more dyno hours)
heroku ps:scale web=2
```

## 8. Automation (Optional)

You can automate deployments with GitHub Actions:

1. Create `.github/workflows/heroku-deploy.yml`
2. Configure GitHub secrets for Heroku
3. Push changes to trigger automatic deployments

## Heroku vs AWS Architecture

```mermaid
flowchart TD
    subgraph "Heroku Architecture"
        A1[GitHub Repository] --> B1[GitHub Actions/Manual Push]
        B1 --> C1[Heroku Build Process]
        C1 --> D1[Heroku Dynos]
        D1 --> E1[Custom Domain]
    end
    
    subgraph "Traditional AWS Architecture"
        A2[GitHub Repository] --> B2[CI/CD Pipeline]
        B2 --> C2[AWS Service/Server]
        C2 --> D2[Load Balancer]
        D2 --> E2[Custom Domain]
    end
```

## Troubleshooting Common Issues

1. **Application Error or Crashed**: Check logs with `heroku logs --tail`
2. **Domain Not Working**: Verify DNS settings with `heroku domains`
3. **SSL Certificate Issues**: Run `heroku certs:auto`
4. **Build Failures**: Check build logs during deployment 