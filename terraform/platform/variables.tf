variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "repository_name" {
  type    = string
  default = "ai-inference-proxy"
}

variable "github_oidc_provider_arn" {
  type        = string
  description = "Existing IAM OIDC provider ARN for token.actions.githubusercontent.com."
}

variable "github_repository" {
  type    = string
  default = "kaybe005/ai-inference-gitops"
}
