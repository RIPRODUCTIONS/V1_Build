locals {
  region = "us-west-2"
}

remote_state {
  backend = "local"
  generate = {
    path      = "backend.tf"
    if_exists = "overwrite"
  }
  config = {
    path = "terraform.tfstate"
  }
}

terraform {
  source = "../..//terraform"
}

inputs = {
  region = local.region
}
