terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 2.26"
    }
  }
  # Backend: default to local; switch to S3 when ready
  # backend "s3" {
  #   bucket = "your-tf-state-bucket"
  #   key    = "self-healing-mvp/terraform.tfstate"
  #   region = "us-west-2"
  # }
}

provider "aws" {
  region = var.region
  default_tags {
    tags = {
      project = "self-healing-mvp"
    }
  }
}

provider "kubernetes" {
  host                   = try(module.eks.cluster_endpoint, null)
  cluster_ca_certificate = try(base64decode(module.eks.cluster_certificate_authority_data), null)
  token                  = null # using aws-auth or kubeconfig outside terraform usually
}
