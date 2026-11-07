# GitHub Backlog Generator v2 - AWS Fargate Deployment Project Plan

## 🎯 Project Overview

Deploy the GitHub Backlog Generator as a cloud-native application using AWS ECS Fargate with real-time log streaming capabilities.

### Key Objectives
- Containerize the CLI tool for ECS Fargate deployment
- Implement real-time log streaming via CloudWatch Logs
- Create a web UI component for embedded log viewing
- Ensure cost-effectiveness (~$0.02 per 30-minute run)
- Maintain simplicity with minimal custom code

## 📋 Project Phases

### Phase 1: Local Development & Containerization (Day 1)
**Goal**: Get the tool running in a container locally with proper logging

#### Milestone 1.1: Docker Setup (2 hours)
- [ ] Create Dockerfile for the CLI tool
- [ ] Add proper logging configuration
- [ ] Test container builds successfully
- [ ] Verify tool runs inside container with test repo

**Integration Test 1.1**:
```bash
# Build and run locally
docker build -t github-backlog-generator:v2 .
docker run -e REPO_URL="https://github.com/facebook/react" \
           -e PHASE="1" \
           -e ANTHROPIC_API_KEY="test-key" \
           -e GITHUB_TOKEN="test-token" \
           github-backlog-generator:v2
# Verify: Should see logs output to console
```

#### Milestone 1.2: CloudWatch Logs Format (1 hour)
- [ ] Configure structured logging format
- [ ] Add timestamps and log levels
- [ ] Test JSON log output
- [ ] Verify multiline log handling

**Integration Test 1.2**:
```bash
# Run with JSON logging
docker run --env LOG_FORMAT=json \
           github-backlog-generator:v2 | jq .
# Verify: Each log line is valid JSON with timestamp
```

### Phase 2: AWS Infrastructure Setup (Day 1-2)
**Goal**: Create core AWS resources for running containers

#### Milestone 2.1: Networking & Security (2 hours)
- [ ] Create VPC with public/private subnets
- [ ] Configure security groups for ECS
- [ ] Set up NAT Gateway for outbound traffic
- [ ] Create IAM roles for ECS tasks

**Integration Test 2.1**:
```bash
# Apply networking infrastructure
cd infrastructure
terraform plan -target=module.networking
terraform apply -target=module.networking
# Verify: VPC and subnets created successfully
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=github-backlog-vpc"
```

#### Milestone 2.2: ECS Cluster & ECR (1 hour)
- [ ] Create ECS cluster
- [ ] Set up ECR repository
- [ ] Configure CloudWatch Log Group
- [ ] Test ECR push permissions

**Integration Test 2.2**:
```bash
# Create ECS resources
terraform apply -target=module.ecs_cluster
# Push test image
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
docker tag github-backlog-generator:v2 $ECR_URL:latest
docker push $ECR_URL:latest
# Verify: Image uploaded successfully
```

#### Milestone 2.3: Task Definition (1 hour)
- [ ] Create ECS task definition
- [ ] Configure CPU/memory limits
- [ ] Set up CloudWatch logging
- [ ] Add environment variables

**Integration Test 2.3**:
```bash
# Register task definition
aws ecs register-task-definition --cli-input-json file://task-definition.json
# Run a test task
aws ecs run-task \
  --cluster github-backlog-cluster \
  --task-definition github-backlog-generator:1 \
  --launch-type FARGATE \
  --network-configuration file://network-config.json
# Verify: Task starts and logs appear in CloudWatch
```

### Phase 3: API Layer Implementation (Day 2)
**Goal**: Create APIs for starting tasks and streaming logs

#### Milestone 3.1: Task Management Lambda (2 hours)
- [ ] Create Lambda function for starting ECS tasks
- [ ] Add input validation
- [ ] Implement task tagging
- [ ] Return task metadata

**Integration Test 3.1**:
```bash
# Deploy Lambda
cd backend/lambdas
zip start_task.zip start_task.py
aws lambda create-function --cli-input-json file://start-task-config.json
# Test invocation
aws lambda invoke \
  --function-name github-backlog-start-task \
  --payload '{"repo_url":"https://github.com/facebook/react","phase":1}' \
  response.json
# Verify: Task ARN returned, task running in ECS
```

#### Milestone 3.2: Log Streaming Lambda (2 hours)
- [ ] Create Lambda for fetching CloudWatch logs
- [ ] Implement pagination support
- [ ] Add real-time tail functionality
- [ ] Handle log stream discovery

**Integration Test 3.2**:
```bash
# Deploy log streaming Lambda
zip stream_logs.zip stream_logs.py
aws lambda create-function --cli-input-json file://stream-logs-config.json
# Test with running task
aws lambda invoke \
  --function-name github-backlog-stream-logs \
  --payload '{"log_group":"/ecs/github-backlog-generator","log_stream":"ecs/backlog-generator/task-id"}' \
  logs.json
# Verify: Logs returned with proper formatting
```

#### Milestone 3.3: API Gateway Setup (1 hour)
- [ ] Create REST API endpoints
- [ ] Configure CORS
- [ ] Add request/response models
- [ ] Set up API keys (optional)

**Integration Test 3.3**:
```bash
# Deploy API Gateway
aws apigateway create-rest-api --name github-backlog-api
# Test endpoints
curl -X POST https://api-id.execute-api.region.amazonaws.com/prod/start-task \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/facebook/react","phase":1}'
# Verify: 200 response with task details
```

### Phase 4: Frontend Development (Day 3)
**Goal**: Create reusable React component for log viewing

#### Milestone 4.1: Basic Log Viewer Component (2 hours)
- [ ] Create React component structure
- [ ] Implement log fetching logic
- [ ] Add auto-scrolling
- [ ] Style terminal appearance

**Integration Test 4.1**:
```bash
# Run component in isolation
cd frontend
npm run storybook
# Verify: Component renders with mock data
# Check: Auto-scroll works, styling matches terminal
```

#### Milestone 4.2: Real-time Streaming (2 hours)
- [ ] Add polling mechanism
- [ ] Implement incremental updates
- [ ] Handle connection errors
- [ ] Add streaming status indicator

**Integration Test 4.2**:
```bash
# Test against real API
REACT_APP_API_URL=https://api-id.execute-api.region.amazonaws.com/prod \
npm start
# Start a real task and verify:
# - Logs appear within 2 seconds
# - No duplicate entries
# - Streaming stops when task completes
```

#### Milestone 4.3: UI Polish & Features (1 hour)
- [ ] Add copy-to-clipboard
- [ ] Implement log filtering
- [ ] Add download logs option
- [ ] Create loading states

**Integration Test 4.3**:
```bash
# Full UI test
npm run test:e2e
# Verify all features:
# - Copy button works
# - Filter highlights matches
# - Download creates valid log file
```

### Phase 5: Integration & Testing (Day 4)
**Goal**: Ensure all components work together seamlessly

#### Milestone 5.1: End-to-End Testing (2 hours)
- [ ] Create test scenarios
- [ ] Implement automated tests
- [ ] Test error conditions
- [ ] Verify 30-minute runs

**Integration Test 5.1**:
```bash
# Run full E2E test suite
cd tests
./run-e2e-tests.sh
# Tests should cover:
# - Starting task via UI
# - Watching logs for 30 minutes
# - Handling task failures
# - Multiple concurrent tasks
```

#### Milestone 5.2: Performance Testing (1 hour)
- [ ] Test with large log volumes
- [ ] Verify streaming latency
- [ ] Check memory usage
- [ ] Test concurrent users

**Integration Test 5.2**:
```bash
# Load test the system
artillery run load-test.yml
# Verify:
# - API response time < 500ms
# - Log latency < 2 seconds
# - No memory leaks in UI
```

#### Milestone 5.3: Security Review (1 hour)
- [ ] Audit IAM permissions
- [ ] Review API authentication
- [ ] Check secret management
- [ ] Validate input sanitization

**Integration Test 5.3**:
```bash
# Security scan
npm audit
terraform plan # Review any privilege escalations
# Manual review:
# - No hardcoded secrets
# - Least privilege IAM
# - Input validation in place
```

### Phase 6: Deployment & Documentation (Day 4-5)
**Goal**: Production-ready deployment with documentation

#### Milestone 6.1: Production Deployment (2 hours)
- [ ] Create production environment
- [ ] Set up monitoring/alerts
- [ ] Configure auto-scaling
- [ ] Deploy all components

**Integration Test 6.1**:
```bash
# Deploy to production
./scripts/deploy-production.sh
# Smoke test
curl https://prod-api.your-domain.com/health
# Verify: All systems operational
```

#### Milestone 6.2: Documentation (2 hours)
- [ ] Write deployment guide
- [ ] Create troubleshooting guide
- [ ] Document API endpoints
- [ ] Add architecture diagrams

#### Milestone 6.3: Handoff Package (1 hour)
- [ ] Create runbook
- [ ] List all AWS resources
- [ ] Document costs
- [ ] Provide maintenance guide

## 📁 Deliverables Structure

```
v2/
├── PROJECT_PLAN.md (this file)
├── infrastructure/
│   ├── terraform/
│   │   ├── main.tf
│   │   ├── networking.tf
│   │   ├── ecs.tf
│   │   ├── lambda.tf
│   │   └── api-gateway.tf
│   └── scripts/
│       ├── deploy.sh
│       └── destroy.sh
├── backend/
│   ├── lambdas/
│   │   ├── start_task.py
│   │   ├── stream_logs.py
│   │   └── task_status.py
│   └── shared/
│       └── aws_helpers.py
├── frontend/
│   ├── src/
│   │   ├── LogViewer.jsx
│   │   ├── LogViewer.css
│   │   └── LogViewer.test.js
│   ├── package.json
│   └── webpack.config.js
├── docker/
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── .dockerignore
├── scripts/
│   ├── build-and-push.sh
│   ├── run-local.sh
│   └── deploy-production.sh
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── TROUBLESHOOTING.md
│   └── API.md
└── tests/
    ├── e2e/
    ├── integration/
    └── load/
```

## 🚦 Success Criteria

1. **Functional Requirements**
   - [ ] Tool runs for 30 minutes without interruption
   - [ ] Logs stream in real-time (< 2 second delay)
   - [ ] UI component embeddable in any React app
   - [ ] Handles multiple concurrent runs

2. **Non-Functional Requirements**
   - [ ] Cost per run < $0.03
   - [ ] Deployment time < 30 minutes
   - [ ] Zero maintenance required
   - [ ] 99.9% uptime for API

3. **Quality Gates**
   - [ ] All integration tests passing
   - [ ] Security scan clean
   - [ ] Documentation complete
   - [ ] Runbook tested

## 🎯 Risk Mitigation

1. **CloudWatch Logs Delays**
   - Risk: Logs might have 5-10 second delays
   - Mitigation: Implement CloudWatch Logs Insights for faster queries

2. **Task Failures**
   - Risk: ECS task might fail to start
   - Mitigation: Add retry logic and detailed error messages

3. **Cost Overruns**
   - Risk: Unexpected AWS charges
   - Mitigation: Set up billing alerts and use Fargate Spot

4. **UI Performance**
   - Risk: Browser slowdown with large logs
   - Mitigation: Implement virtual scrolling and log rotation

## 📊 Timeline Summary

- **Day 1**: Local development and containerization
- **Day 2**: AWS infrastructure and API development
- **Day 3**: Frontend component development
- **Day 4**: Integration testing and security
- **Day 5**: Production deployment and documentation

**Total Effort**: 5 days (40 hours) with incremental testing at each milestone