# Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.project_name}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Lambda basic execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# Lambda policy for ECS and CloudWatch
resource "aws_iam_role_policy" "lambda_ecs_cloudwatch" {
  name = "${var.project_name}-lambda-ecs-policy"
  role = aws_iam_role.lambda_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecs:RunTask",
          "ecs:DescribeTasks",
          "ecs:ListTasks"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "iam:PassRole"
        ]
        Resource = [
          aws_iam_role.ecs_task_execution.arn,
          aws_iam_role.ecs_task.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:GetLogEvents",
          "logs:FilterLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "${aws_cloudwatch_log_group.ecs.arn}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeSubnets",
          "ec2:DescribeSecurityGroups",
          "ec2:DescribeVpcs"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda layer for shared code
resource "aws_lambda_layer_version" "shared" {
  filename            = "${path.module}/../../backend/shared/layer.zip"
  layer_name          = "${var.project_name}-shared"
  compatible_runtimes = ["python3.11"]
  description         = "Shared utilities for Lambda functions"
}

# Lambda function to start ECS tasks
resource "aws_lambda_function" "start_task" {
  filename         = "${path.module}/../../backend/lambdas/start_task.zip"
  function_name    = "${var.project_name}-start-task"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "start_task.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../../backend/lambdas/start_task.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      ECS_CLUSTER_NAME     = aws_ecs_cluster.main.name
      TASK_DEFINITION_ARN  = aws_ecs_task_definition.app.arn
      SUBNET_IDS           = join(",", aws_subnet.private[*].id)
      SECURITY_GROUP_ID    = aws_security_group.ecs_tasks.id
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name        = "${var.project_name}-start-task"
    Environment = var.environment
  }
}

# Lambda function to stream logs
resource "aws_lambda_function" "stream_logs" {
  filename         = "${path.module}/../../backend/lambdas/stream_logs.zip"
  function_name    = "${var.project_name}-stream-logs"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "stream_logs.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../../backend/lambdas/stream_logs.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      LOG_GROUP_NAME = aws_cloudwatch_log_group.ecs.name
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name        = "${var.project_name}-stream-logs"
    Environment = var.environment
  }
}

# Lambda function to get task status
resource "aws_lambda_function" "task_status" {
  filename         = "${path.module}/../../backend/lambdas/task_status.zip"
  function_name    = "${var.project_name}-task-status"
  role            = aws_iam_role.lambda_execution.arn
  handler         = "task_status.lambda_handler"
  source_code_hash = filebase64sha256("${path.module}/../../backend/lambdas/task_status.zip")
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  layers = [aws_lambda_layer_version.shared.arn]

  environment {
    variables = {
      ECS_CLUSTER_NAME = aws_ecs_cluster.main.name
    }
  }

  vpc_config {
    subnet_ids         = aws_subnet.private[*].id
    security_group_ids = [aws_security_group.lambda.id]
  }

  tags = {
    Name        = "${var.project_name}-task-status"
    Environment = var.environment
  }
}

# CloudWatch Log Groups for Lambda
resource "aws_cloudwatch_log_group" "lambda_start_task" {
  name              = "/aws/lambda/${aws_lambda_function.start_task.function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "lambda_stream_logs" {
  name              = "/aws/lambda/${aws_lambda_function.stream_logs.function_name}"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_group" "lambda_task_status" {
  name              = "/aws/lambda/${aws_lambda_function.task_status.function_name}"
  retention_in_days = var.log_retention_days
}