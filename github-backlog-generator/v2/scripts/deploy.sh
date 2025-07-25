#!/bin/bash
set -e

# GitHub Backlog Generator v2 Deployment Script
# Deploys the complete stack to AWS using Terraform and Docker

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_DIR}/infrastructure/terraform"
DOCKER_DIR="${PROJECT_DIR}/docker"
FRONTEND_DIR="${PROJECT_DIR}/frontend"
BACKEND_DIR="${PROJECT_DIR}/backend"

# AWS Configuration
AWS_REGION=${AWS_REGION:-"us-east-1"}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="github-backlog-generator"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

# Parse arguments
ACTION="apply"
ENVIRONMENT="production"
SKIP_BUILD=false
SKIP_FRONTEND=false
AUTO_APPROVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --destroy)
            ACTION="destroy"
            shift
            ;;
        --plan)
            ACTION="plan"
            shift
            ;;
        --env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo "Options:"
            echo "  --destroy        Destroy all resources"
            echo "  --plan           Show deployment plan only"
            echo "  --env ENV        Environment (default: production)"
            echo "  --skip-build     Skip Docker image build"
            echo "  --skip-frontend  Skip frontend deployment"
            echo "  --auto-approve   Auto-approve Terraform changes"
            echo "  --help, -h       Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

check_requirements() {
    log "Checking deployment requirements..."
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is required but not installed"
        exit 1
    fi
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        error "Terraform is required but not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is required but not installed"
        exit 1
    fi
    
    # Check Node.js for frontend
    if [ "$SKIP_FRONTEND" != "true" ] && ! command -v npm &> /dev/null; then
        error "Node.js/npm is required for frontend deployment"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured or invalid"
        exit 1
    fi
    
    # Check required environment variables
    if [ -z "$ANTHROPIC_API_KEY" ]; then
        error "ANTHROPIC_API_KEY environment variable is required"
        exit 1
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        error "GITHUB_TOKEN environment variable is required"
        exit 1
    fi
    
    log "All requirements satisfied"
}

create_ecr_repository() {
    log "Ensuring ECR repository exists..."
    
    if aws ecr describe-repositories --repository-names "$ECR_REPOSITORY" \
        --region "$AWS_REGION" &> /dev/null; then
        log "ECR repository already exists"
    else
        log "Creating ECR repository..."
        aws ecr create-repository \
            --repository-name "$ECR_REPOSITORY" \
            --region "$AWS_REGION" \
            --tags Key=Project,Value=github-backlog-generator Key=Environment,Value="$ENVIRONMENT"
    fi
}

build_and_push_docker_image() {
    if [ "$SKIP_BUILD" == "true" ]; then
        log "Skipping Docker build (--skip-build flag)"
        return 0
    fi
    
    log "Building Docker image..."
    
    # Build the image
    cd "$DOCKER_DIR"
    docker build -t "$ECR_REPOSITORY:latest" \
        --build-arg ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
        --build-arg GITHUB_TOKEN="$GITHUB_TOKEN" \
        -f Dockerfile ..
    
    # Tag for ECR
    docker tag "$ECR_REPOSITORY:latest" "$ECR_URI:latest"
    docker tag "$ECR_REPOSITORY:latest" "$ECR_URI:$(date +%Y%m%d%H%M%S)"
    
    # Login to ECR
    log "Logging in to ECR..."
    aws ecr get-login-password --region "$AWS_REGION" | \
        docker login --username AWS --password-stdin "$ECR_URI"
    
    # Push images
    log "Pushing Docker image to ECR..."
    docker push "$ECR_URI:latest"
    docker push "$ECR_URI:$(date +%Y%m%d%H%M%S)"
    
    cd - > /dev/null
    log "Docker image pushed successfully"
}

deploy_infrastructure() {
    log "Deploying infrastructure with Terraform..."
    
    cd "$TERRAFORM_DIR"
    
    # Initialize Terraform
    if [ ! -d ".terraform" ]; then
        log "Initializing Terraform..."
        terraform init
    fi
    
    # Create tfvars file
    cat > "terraform.tfvars" << EOF
project_name = "github-backlog-generator"
environment = "$ENVIRONMENT"
aws_region = "$AWS_REGION"

# Secrets
anthropic_api_key = "$ANTHROPIC_API_KEY"
github_token = "$GITHUB_TOKEN"

# Container configuration
container_image = "$ECR_URI:latest"
task_cpu = "1024"
task_memory = "2048"

# API configuration
api_key = "${API_KEY:-$(openssl rand -hex 32)}"

# Tags
tags = {
  Project     = "github-backlog-generator"
  Environment = "$ENVIRONMENT"
  ManagedBy   = "terraform"
  DeployedBy  = "$(whoami)"
  DeployedAt  = "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    # Run Terraform
    case "$ACTION" in
        plan)
            log "Running Terraform plan..."
            terraform plan -var-file="terraform.tfvars"
            ;;
        apply)
            log "Applying Terraform configuration..."
            if [ "$AUTO_APPROVE" == "true" ]; then
                terraform apply -var-file="terraform.tfvars" -auto-approve
            else
                terraform apply -var-file="terraform.tfvars"
            fi
            ;;
        destroy)
            warning "Destroying all infrastructure..."
            if [ "$AUTO_APPROVE" == "true" ]; then
                terraform destroy -var-file="terraform.tfvars" -auto-approve
            else
                terraform destroy -var-file="terraform.tfvars"
            fi
            ;;
    esac
    
    # Clean up tfvars
    rm -f terraform.tfvars
    
    cd - > /dev/null
}

get_terraform_outputs() {
    cd "$TERRAFORM_DIR"
    
    # Get outputs
    API_GATEWAY_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
    S3_BUCKET_NAME=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "")
    CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain 2>/dev/null || echo "")
    
    cd - > /dev/null
}

deploy_frontend() {
    if [ "$SKIP_FRONTEND" == "true" ] || [ "$ACTION" != "apply" ]; then
        return 0
    fi
    
    log "Building and deploying frontend..."
    
    # Get S3 bucket from Terraform outputs
    get_terraform_outputs
    
    if [ -z "$S3_BUCKET_NAME" ]; then
        warning "S3 bucket not found, skipping frontend deployment"
        return 0
    fi
    
    cd "$FRONTEND_DIR"
    
    # Install dependencies
    log "Installing frontend dependencies..."
    npm install
    
    # Build with API URL
    log "Building frontend with API URL: $API_GATEWAY_URL"
    REACT_APP_API_URL="$API_GATEWAY_URL" npm run build
    
    # Upload to S3
    log "Uploading frontend to S3..."
    aws s3 sync dist/ "s3://$S3_BUCKET_NAME/" \
        --delete \
        --cache-control "public, max-age=3600"
    
    # Invalidate CloudFront cache
    if [ -n "$CLOUDFRONT_DOMAIN" ]; then
        log "Invalidating CloudFront cache..."
        DISTRIBUTION_ID=$(aws cloudfront list-distributions \
            --query "DistributionList.Items[?DomainName=='$CLOUDFRONT_DOMAIN'].Id" \
            --output text)
        
        if [ -n "$DISTRIBUTION_ID" ]; then
            aws cloudfront create-invalidation \
                --distribution-id "$DISTRIBUTION_ID" \
                --paths "/*"
        fi
    fi
    
    cd - > /dev/null
    log "Frontend deployed successfully"
}

deploy_lambda_code() {
    if [ "$ACTION" != "apply" ]; then
        return 0
    fi
    
    log "Updating Lambda function code..."
    
    cd "$BACKEND_DIR/lambdas"
    
    # Package each Lambda function
    for func in start_task check_status get_logs; do
        log "Packaging $func Lambda..."
        
        # Create deployment package
        cp "${func}.py" "index.py"
        zip -q "${func}.zip" index.py
        rm index.py
        
        # Update function code
        aws lambda update-function-code \
            --function-name "github-backlog-${func//_/-}" \
            --zip-file "fileb://${func}.zip" \
            --region "$AWS_REGION" > /dev/null
        
        rm "${func}.zip"
    done
    
    cd - > /dev/null
    log "Lambda functions updated successfully"
}

print_deployment_summary() {
    if [ "$ACTION" != "apply" ]; then
        return 0
    fi
    
    get_terraform_outputs
    
    info "Deployment Summary"
    info "=================="
    info "Environment: $ENVIRONMENT"
    info "AWS Region: $AWS_REGION"
    info "ECR Repository: $ECR_URI"
    
    if [ -n "$API_GATEWAY_URL" ]; then
        info "API Gateway URL: $API_GATEWAY_URL"
    fi
    
    if [ -n "$CLOUDFRONT_DOMAIN" ]; then
        info "Frontend URL: https://$CLOUDFRONT_DOMAIN"
    fi
    
    info ""
    info "Next Steps:"
    info "1. Test the API: curl -X POST $API_GATEWAY_URL/start -H 'x-api-key: YOUR_API_KEY' -d '{\"repo_url\":\"https://github.com/test/repo\",\"phase\":\"planning\"}'"
    info "2. View logs: aws logs tail /ecs/github-backlog-generator --follow"
    info "3. Monitor tasks: aws ecs list-tasks --cluster github-backlog-cluster"
}

cleanup_on_error() {
    error "Deployment failed! Cleaning up..."
    
    # You might want to add cleanup logic here
    # For example, deleting half-deployed resources
    
    exit 1
}

# Set up error handling
trap cleanup_on_error ERR

# Main deployment flow
main() {
    log "GitHub Backlog Generator v2 Deployment"
    log "====================================="
    
    # Check requirements
    check_requirements
    
    if [ "$ACTION" == "apply" ]; then
        # Create ECR repository
        create_ecr_repository
        
        # Build and push Docker image
        build_and_push_docker_image
    fi
    
    # Deploy infrastructure
    deploy_infrastructure
    
    if [ "$ACTION" == "apply" ]; then
        # Deploy Lambda code
        deploy_lambda_code
        
        # Deploy frontend
        deploy_frontend
    fi
    
    # Print summary
    print_deployment_summary
    
    log "Deployment completed successfully!"
}

# Run main function
main