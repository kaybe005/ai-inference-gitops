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

variable "github_oidc_subject" {
  type        = string
  description = "Exact OIDC sub claim for the GitHub Actions workflow allowed to publish images."
  default     = "repo:kaybe005@190797454/ai-inference-gitops@1422890393:ref:refs/heads/main"
}
