variable "role_name" {
  type = string
}

variable "oidc_provider_arn" {
  type        = string
  description = "Existing GitHub Actions OIDC provider ARN in the AWS account."
}

variable "oidc_subject" {
  type        = string
  description = "Exact GitHub OIDC subject claim allowed to assume this role."
}

variable "ecr_repository_arn" {
  type = string
}

resource "aws_iam_role" "github_actions" {
  name = var.role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          "token.actions.githubusercontent.com:sub" = var.oidc_subject
        }
      }
    }]
  })
}

resource "aws_iam_role_policy" "github_actions" {
  name = "github-actions-ecr-push"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "EcrPush"
        Effect   = "Allow"
        Action   = ["ecr:BatchCheckLayerAvailability", "ecr:CompleteLayerUpload", "ecr:InitiateLayerUpload", "ecr:PutImage", "ecr:UploadLayerPart"]
        Resource = var.ecr_repository_arn
      },
      {
        Sid      = "EcrLogin"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      }
    ]
  })
}

output "role_arn" {
  value = aws_iam_role.github_actions.arn
}
