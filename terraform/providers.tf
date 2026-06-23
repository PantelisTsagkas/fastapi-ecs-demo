terraform {
  required_version = ">= 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Once this is past the demo stage, move state off your laptop:
  # backend "s3" {
  #   bucket         = "your-tfstate-bucket"
  #   key            = "fastapi-ecs-demo/terraform.tfstate"
  #   region         = "eu-west-2"
  #   dynamodb_table = "terraform-locks"
  #   encrypt        = true
  # }
}

provider "aws" {
  region = var.aws_region
}
