variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "github-backlog-generator"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "task_cpu" {
  description = "CPU units for the task"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Memory for the task in MB"
  type        = number
  default     = 1024
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "anthropic_api_key" {
  description = "Anthropic API key (stored in AWS Secrets Manager)"
  type        = string
  sensitive   = true
}

variable "github_token" {
  description = "GitHub token (stored in AWS Secrets Manager)"
  type        = string
  sensitive   = true
}