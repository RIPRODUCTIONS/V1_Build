variable "region" {
  type        = string
  description = "AWS region"
  default     = "us-west-2"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.42.0.0/16"
}

variable "allowed_cidrs" {
  type        = list(string)
  description = "Allowed CIDRs for public access (e.g., to DB). Keep minimal in prod."
  default     = ["0.0.0.0/0"]
}

variable "cluster_desired" {
  type        = number
  description = "Desired node count"
  default     = 2
}

variable "cluster_min" {
  type        = number
  description = "Min node count"
  default     = 2
}

variable "cluster_max" {
  type        = number
  description = "Max node count"
  default     = 6
}

variable "create_rds" {
  type        = bool
  description = "Toggle to create RDS Postgres"
  default     = false
}

variable "db_instance_class" {
  type        = string
  description = "RDS instance class"
  default     = "db.t4g.micro"
}
