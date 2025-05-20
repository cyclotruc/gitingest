#!/bin/bash

# This script runs during Heroku's build process before the app is deployed

# Install Git if it's not already installed
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    apt-get update -y
    apt-get install -y git
fi

# Create necessary directories
mkdir -p /tmp/gitingest

# Make sure directories are writable
chmod -R 777 /tmp/gitingest

echo "Pre-build setup completed successfully!" 