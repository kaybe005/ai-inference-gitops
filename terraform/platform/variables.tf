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
  default     = ""
}

variable "github_repository" {
  type    = string
  default = "kaybe005/ai-inference-gitops"
}

variable "state_bucket_arn" {
  type    = string
  default = ""
}

variable "lock_table_arn" {
  type    = string
  default = ""
}
