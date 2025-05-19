#!/bin/bash

# This script helps you set up your Heroku app for gittodoc deployment

# Check if logged in to Heroku
echo "Checking Heroku login status..."
heroku whoami || (echo "Please log in to Heroku first using 'heroku login'" && exit 1)

# Ask for app name
read -p "Enter the Heroku app name (leave blank for a random name): " app_name

if [ -z "$app_name" ]; then
  echo "Creating Heroku app with random name..."
  heroku create
else
  echo "Creating Heroku app with name $app_name..."
  heroku create $app_name
fi

# Get the app name if it was randomly generated
if [ -z "$app_name" ]; then
  app_name=$(heroku apps:info | grep "=== " | cut -d" " -f2)
  echo "App created with name: $app_name"
fi

# Configure environment variables
echo "Setting up required environment variables..."

# S3 Configuration
read -p "Enter your S3 bucket name: " s3_bucket
read -p "Enter your AWS access key: " aws_access_key
read -p "Enter your AWS secret key: " aws_secret_key
read -p "Enter your AWS region (default: us-east-1): " aws_region
aws_region=${aws_region:-us-east-1}

echo "Setting S3 configuration..."
heroku config:set GITINGEST_S3_BUCKET=$s3_bucket -a $app_name
heroku config:set AWS_ACCESS_KEY_ID=$aws_access_key -a $app_name
heroku config:set AWS_SECRET_ACCESS_KEY=$aws_secret_key -a $app_name
heroku config:set AWS_REGION=$aws_region -a $app_name

# Allowed hosts configuration
read -p "Enter your custom domain (e.g., gittodoc.com): " custom_domain

if [ -n "$custom_domain" ]; then
  echo "Setting allowed hosts for custom domain..."
  heroku config:set ALLOWED_HOSTS="$custom_domain,*.$custom_domain,$app_name.herokuapp.com,herokuapp.com" -a $app_name
  
  # Ask if user wants to add the domain now
  read -p "Do you want to add the custom domain to Heroku now? (y/n): " add_domain
  if [ "$add_domain" = "y" ]; then
    echo "Adding custom domain $custom_domain to Heroku app..."
    heroku domains:add $custom_domain -a $app_name
    
    # Ask about www subdomain
    read -p "Do you also want to add www.$custom_domain? (y/n): " add_www
    if [ "$add_www" = "y" ]; then
      echo "Adding www.$custom_domain to Heroku app..."
      heroku domains:add www.$custom_domain -a $app_name
    fi
    
    # Show domain info
    echo "Domain information:"
    heroku domains -a $app_name
    
    # Setup SSL
    echo "Setting up SSL..."
    heroku certs:auto:enable -a $app_name
  fi
else
  echo "Setting allowed hosts for Heroku domain only..."
  heroku config:set ALLOWED_HOSTS="$app_name.herokuapp.com,herokuapp.com" -a $app_name
fi

echo "Environment variables set successfully!"

# Suggest next steps
echo ""
echo "Next steps to deploy your app:"
echo "1. Commit any changes you've made:"
echo "   git add ."
echo "   git commit -m 'Prepare for Heroku deployment'"
echo ""
echo "2. Deploy to Heroku:"
echo "   git push heroku main"
echo ""
echo "3. Check the app status:"
echo "   heroku open -a $app_name"
echo ""
echo "4. View logs if needed:"
echo "   heroku logs --tail -a $app_name"
echo "" 