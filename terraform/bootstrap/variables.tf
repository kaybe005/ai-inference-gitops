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
