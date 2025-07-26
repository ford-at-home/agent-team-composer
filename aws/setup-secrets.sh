#!/bin/bash

# Setup AWS Secrets for MVP Backlog Batch Stack
# Usage: ./setup-secrets.sh --profile personal

set -e

AWS_PROFILE="personal"
REGION="us-east-1"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --profile)
            AWS_PROFILE="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "🔐 Setting up AWS Secrets Manager secrets"
echo "Profile: $AWS_PROFILE"
echo "Region: $REGION"

# Check if secrets already exist
check_secret() {
    local secret_name=$1
    if aws secretsmanager describe-secret --secret-id "$secret_name" --profile "$AWS_PROFILE" --region "$REGION" >/dev/null 2>&1; then
        echo "✅ Secret '$secret_name' already exists"
        return 0
    else
        echo "❌ Secret '$secret_name' does not exist"
        return 1
    fi
}

# Create GitHub token secret
if ! check_secret "github-token"; then
    echo "Creating github-token secret..."
    read -sp "Enter your GitHub token: " GITHUB_TOKEN
    echo
    aws secretsmanager create-secret \
        --name "github-token" \
        --description "GitHub personal access token for MVP Backlog operations" \
        --secret-string "$GITHUB_TOKEN" \
        --profile "$AWS_PROFILE" \
        --region "$REGION"
    echo "✅ Created github-token secret"
fi

# Create Anthropic API key secret
if ! check_secret "anthropic_api_key"; then
    echo "Creating anthropic_api_key secret..."
    read -sp "Enter your Anthropic API key: " ANTHROPIC_KEY
    echo
    aws secretsmanager create-secret \
        --name "anthropic_api_key" \
        --description "Anthropic API key for Claude access" \
        --secret-string "$ANTHROPIC_KEY" \
        --profile "$AWS_PROFILE" \
        --region "$REGION"
    echo "✅ Created anthropic_api_key secret"
fi

echo "🎉 Secrets setup complete!"