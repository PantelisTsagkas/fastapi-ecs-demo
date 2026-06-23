output "alb_dns_name" {
  description = "Public URL of the load balancer"
  value       = "http://${aws_lb.app.dns_name}"
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "ecs_service_name" {
  value = aws_ecs_service.app.name
}

output "github_actions_role_arn" {
  description = "Put this in the GitHub Actions workflow / repo variables"
  value       = aws_iam_role.github_actions.arn
}
