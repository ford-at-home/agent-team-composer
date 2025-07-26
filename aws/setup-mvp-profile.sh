#!/bin/bash

# Setup MVP AWS Profile
# This script helps configure the AWS CLI for the MVP account

echo "🔧 Setting up MVP AWS Profile"
echo "Account ID: 984906149037"
echo "Region: us-east-1"
echo ""

# Check if mvp profile already exists
if aws configure list-profiles | grep -q "^mvp$"; then
    echo "✅ MVP profile already exists"
    echo "Current configuration:"
    aws configure list --profile mvp
    echo ""
    read -p "Do you want to reconfigure? (y/N): " reconfigure
    if [[ ! "$reconfigure" =~ ^[Yy]$ ]]; then
        echo "Using existing MVP profile"
        exit 0
    fi
fi

echo "📝 Please provide your MVP account credentials:"
echo ""

# Get AWS credentials
read -p "AWS Access Key ID: " access_key
read -sp "AWS Secret Access Key: " secret_key
echo ""

# Configure the profile
aws configure set aws_access_key_id "$access_key" --profile mvp
aws configure set aws_secret_access_key "$secret_key" --profile mvp
aws configure set region us-east-1 --profile mvp
aws configure set output json --profile mvp

echo "✅ MVP profile configured successfully!"
echo ""

# Test the profile
echo "🧪 Testing MVP profile..."
if aws sts get-caller-identity --profile mvp >/dev/null 2>&1; then
    echo "✅ MVP profile is working correctly"
    aws sts get-caller-identity --profile mvp
    
    # Verify it's the correct account
    account_id=$(aws sts get-caller-identity --query Account --output text --profile mvp)
    if [ "$account_id" = "984906149037" ]; then
        echo "✅ Confirmed: Connected to MVP account (984906149037)"
    else
        echo "❌ Warning: Connected to account $account_id, expected 984906149037"
        echo "Please verify your credentials are for the MVP account"
    fi
else
    echo "❌ MVP profile test failed"
    echo "Please check your credentials and try again"
    exit 1
fi

echo ""
echo "🎉 MVP profile setup complete!"
echo "You can now run: ./deploy.sh --profile mvp"