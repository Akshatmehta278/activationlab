variable "aws_region" {
  description = "AWS region for the reference deployment."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Resource-name prefix."
  type        = string
  default     = "activationlab"
}

variable "environment" {
  description = "Deployment environment label."
  type        = string
  default     = "demo"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "backend_image" {
  description = "Published backend container image, for example an ECR image URI."
  type        = string
}

variable "frontend_image" {
  description = "Published frontend container image, for example an ECR image URI."
  type        = string
}

variable "database_name" {
  type    = string
  default = "activationlab"
}

variable "database_username" {
  type    = string
  default = "activationlab"
}

variable "database_password" {
  description = "Demo database password. Supply through TF_VAR_database_password or a secure Terraform variable store."
  type        = string
  sensitive   = true
}

variable "rabbitmq_username" {
  type    = string
  default = "activationlab"
}

variable "rabbitmq_password" {
  description = "RabbitMQ password. Supply through TF_VAR_rabbitmq_password or a secure Terraform variable store."
  type        = string
  sensitive   = true
}

variable "django_secret_key" {
  description = "Django signing secret. Supply securely."
  type        = string
  sensitive   = true
}

variable "desired_backend_count" {
  type    = number
  default = 2
}

variable "desired_frontend_count" {
  type    = number
  default = 2
}

variable "desired_worker_count" {
  type    = number
  default = 1
}
