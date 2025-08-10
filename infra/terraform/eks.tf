module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = ">= 20.8.4"

  cluster_name    = "self-healing-mvp"
  cluster_version = "1.29"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = concat(module.vpc.private_subnets, module.vpc.public_subnets)

  enable_irsa = true

  eks_managed_node_groups = {
    default = {
      desired_size = var.cluster_desired
      min_size     = var.cluster_min
      max_size     = var.cluster_max
      instance_types = ["t3.medium", "t3.large"]
      capacity_type  = "SPOT"
      labels = {
        worker = "true"
      }
    }
  }
}

resource "aws_iam_policy" "alb_ingress_controller" {
  name        = "AWSLoadBalancerControllerIAMPolicy"
  description = "Policy for AWS Load Balancer Controller"
  policy      = file("${path.module}/policies/aws-load-balancer-controller.json")
}
