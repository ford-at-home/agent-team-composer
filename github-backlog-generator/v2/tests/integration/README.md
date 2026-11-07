# Integration Test Specifications

This directory contains integration test specifications for the GitHub Backlog Generator v2 Fargate deployment.

## Test Phases

### Phase 1: Infrastructure Tests
**Goal**: Verify all AWS resources are created correctly

#### Test Cases:
1. **VPC and Networking**
   - Verify VPC is created with correct CIDR
   - Check public/private subnets in 2 AZs
   - Verify Internet Gateway attachment
   - Test NAT Gateway connectivity
   - Validate route tables

2. **ECS Cluster**
   - Verify cluster creation
   - Check CloudWatch Container Insights enabled
   - Validate capacity providers

3. **Lambda Functions**
   - Test function deployment
   - Verify IAM roles and permissions
   - Check environment variables
   - Test CloudWatch Logs integration

4. **API Gateway**
   - Verify REST API creation
   - Test CORS configuration
   - Check request/response models
   - Validate stage deployment

### Phase 2: Component Integration Tests
**Goal**: Test individual components work correctly

#### Test Cases:
1. **Lambda Function Tests**
   ```bash
   # Test start_task Lambda
   aws lambda invoke \
     --function-name github-backlog-start-task \
     --payload '{"repo_url":"https://github.com/test/repo","phase":"planning"}' \
     response.json
   
   # Verify response contains taskArn and logStream
   ```

2. **ECS Task Execution**
   ```bash
   # Start a test task directly
   aws ecs run-task \
     --cluster github-backlog-cluster \
     --task-definition github-backlog-generator:latest \
     --launch-type FARGATE \
     --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx]}"
   ```

3. **CloudWatch Logs Streaming**
   ```bash
   # Test log retrieval
   aws logs filter-log-events \
     --log-group-name /ecs/github-backlog-generator \
     --log-stream-name-prefix ecs/github-backlog-generator/
   ```

### Phase 3: End-to-End Tests
**Goal**: Test complete user workflow

#### Test Cases:
1. **Full Workflow Test**
   ```javascript
   // Automated E2E test script
   const axios = require('axios');
   
   async function runE2ETest() {
     // 1. Start a task
     const startResponse = await axios.post(`${API_URL}/start`, {
       repo_url: 'https://github.com/test/repo',
       phase: 'planning'
     });
     
     const { taskId, logStream } = startResponse.data;
     console.log(`Started task: ${taskId}`);
     
     // 2. Poll status
     let status = 'RUNNING';
     while (status === 'RUNNING' || status === 'PROVISIONING') {
       const statusResponse = await axios.get(`${API_URL}/status?task_id=${taskId}`);
       status = statusResponse.data.lastStatus;
       console.log(`Task status: ${status}`);
       await new Promise(resolve => setTimeout(resolve, 5000));
     }
     
     // 3. Retrieve logs
     const logsResponse = await axios.get(`${API_URL}/logs?log_stream=${logStream}`);
     console.log(`Retrieved ${logsResponse.data.events.length} log entries`);
     
     // 4. Verify completion
     assert(status === 'STOPPED', 'Task should complete successfully');
   }
   ```

2. **Error Handling Test**
   - Test with invalid repository URL
   - Test with missing API key
   - Test with invalid phase
   - Verify appropriate error responses

3. **Performance Test**
   - Measure task startup time (< 60s)
   - Verify log streaming latency (< 5s)
   - Check API response times (< 1s)

### Phase 4: Frontend Integration Tests
**Goal**: Test UI functionality with backend

#### Test Cases:
1. **Log Viewer Component**
   ```javascript
   // Cypress test example
   describe('LogViewer Integration', () => {
     it('should stream logs in real-time', () => {
       // Start a task via API
       cy.request('POST', '/api/start', {
         repo_url: 'https://github.com/test/repo',
         phase: 'planning'
       }).then((response) => {
         const { taskId } = response.body;
         
         // Navigate to log viewer
         cy.visit(`/?taskId=${taskId}`);
         
         // Verify logs appear
         cy.contains('Starting GitHub Backlog Generator', { timeout: 10000 });
         cy.contains('Fetching repository information');
         
         // Test filtering
         cy.get('.filter-input').type('repository');
         cy.get('.log-entry').should('have.length.greaterThan', 0);
         
         // Wait for completion
         cy.contains('✓ Complete', { timeout: 120000 });
       });
     });
   });
   ```

2. **UI Functionality Tests**
   - Test log filtering
   - Test copy to clipboard
   - Test download logs
   - Test auto-scroll behavior
   - Test error states

### Phase 5: Security Tests
**Goal**: Verify security configurations

#### Test Cases:
1. **API Security**
   - Test without API key (should fail)
   - Test with invalid API key
   - Test CORS from unauthorized domain
   - Verify rate limiting

2. **ECS Security**
   - Verify task runs with minimal IAM permissions
   - Check no SSH access to containers
   - Validate secrets management
   - Test network isolation

3. **Data Security**
   - Verify logs don't contain sensitive data
   - Check API responses are sanitized
   - Test input validation

## Running Integration Tests

### Prerequisites
```bash
# Install test dependencies
npm install -g jest axios aws-sdk
pip install pytest boto3 requests

# Set environment variables
export API_URL=https://your-api-gateway-url
export AWS_REGION=us-east-1
```

### Execute Test Suite
```bash
# Run all integration tests
./scripts/run-integration-tests.sh

# Run specific phase
./scripts/run-integration-tests.sh --phase 1

# Run with verbose output
./scripts/run-integration-tests.sh --verbose
```

### Test Reports
Test results are saved to:
- `./test-results/junit.xml` - JUnit format for CI
- `./test-results/report.html` - HTML report
- `./test-results/logs/` - Detailed logs

## CI/CD Integration

### GitHub Actions
```yaml
name: Integration Tests
on:
  workflow_dispatch:
  schedule:
    - cron: '0 */4 * * *'  # Every 4 hours

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Run integration tests
        run: |
          cd v2/tests/integration
          ./scripts/run-integration-tests.sh
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        if: always()
        with:
          name: test-results
          path: v2/tests/integration/test-results/
```

## Troubleshooting

### Common Issues

1. **Task fails to start**
   - Check ECS task definition
   - Verify subnet has internet access
   - Check security group rules
   - Review CloudWatch Logs for errors

2. **Logs not appearing**
   - Verify CloudWatch Logs permissions
   - Check log group exists
   - Ensure task is writing to stdout
   - Check log stream name format

3. **API Gateway timeouts**
   - Increase Lambda timeout
   - Check Lambda memory allocation
   - Verify VPC configuration
   - Review API Gateway logs

### Debug Commands
```bash
# Check ECS task status
aws ecs describe-tasks \
  --cluster github-backlog-cluster \
  --tasks arn:aws:ecs:region:account:task/cluster/taskid

# View Lambda logs
aws logs tail /aws/lambda/github-backlog-start-task --follow

# Test API Gateway
curl -X POST https://api-id.execute-api.region.amazonaws.com/prod/start \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"repo_url":"https://github.com/test/repo","phase":"planning"}'
```