# 1. Instantiate ECR Module
module "ecr" {
  source          = "../modules/ecr"
  repository_name = var.repository_name

}

module "github_oidc" {
  source             = "../modules/github_oidc"
  role_name          = "ai-inference-github-actions"
  oidc_provider_arn  = var.github_oidc_provider_arn
  oidc_subject       = var.github_oidc_subject
  ecr_repository_arn = module.ecr.repository_arn
}

