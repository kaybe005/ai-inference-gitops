output "ecr_repository_url" {
  description = "AWS ECR Repository URL"
  value       = module.ecr.repository_url
}

output "ecr_repository_arn" {
  description = "AWS ECR Repository ARN"
  value       = module.ecr.repository_arn
}

output "github_actions_role_arn" {
  description = "Role ARN for GitHub Actions OIDC authentication"
  value       = module.github_oidc.role_arn
}
