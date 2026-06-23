variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Used as a prefix for resource names"
  type        = string
  default     = "fastapi-ecs-demo"
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "Fargate task vCPU units. 256 = .25 vCPU, the smallest size available."
  type        = string
  default     = "256"
}

variable "task_memory" {
  description = "Fargate task memory in MiB. 512 is the smallest size paired with 256 CPU."
  type        = string
  default     = "512"
}

variable "desired_count" {
  description = "Number of running tasks"
  type        = number
  default     = 1
}

variable "image_tag" {
  description = "Tag of the image in ECR used on the very first apply. CI manages deploys after that."
  type        = string
  default     = "latest"
}

variable "github_org" {
  description = "GitHub org/user that owns the repo, used to scope the OIDC trust policy"
  type        = string
}

variable "github_repo" {
  description = "GitHub repo name, used to scope the OIDC trust policy"
  type        = string
}
