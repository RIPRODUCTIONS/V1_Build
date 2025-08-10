module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = ">= 5.5.0"

  name = "self-healing-mvp-vpc"
  cidr = var.vpc_cidr

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  public_subnets  = [for i in range(3) : cidrsubnet(var.vpc_cidr, 4, i)]
  private_subnets = [for i in range(3, 6) : cidrsubnet(var.vpc_cidr, 4, i)]

  enable_nat_gateway   = true
  single_nat_gateway   = true
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    "kubernetes.io/cluster/self-healing-mvp" = "shared"
    "kubernetes.io/role/elb"                 = "1"
    "kubernetes.io/role/internal-elb"        = "1"
  }
}
