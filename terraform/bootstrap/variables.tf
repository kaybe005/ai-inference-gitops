variable "aws_region" {
  type    = string
  default = "ap-southeast-2"
}

variable "state_bucket" {
  type = string
}

variable "lock_table" {
  type    = string
  default = "ai-inference-terraform-locks"
}

variable "project_prefix" {
  type    = string
  default = "ai-inference"
}

variable "environment" {
  type    = string
  default = "lab"
}
