output "cluster_name" {
  value = module.eks.cluster_name
}

output "cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "cluster_certificate_authority_data" {
  value = module.eks.cluster_certificate_authority_data
}

output "region" {
  value = var.region
}

output "ecr_api_url" {
  value = aws_ecr_repository.api.repository_url
}

output "ecr_worker_url" {
  value = aws_ecr_repository.worker.repository_url
}

output "db_url" {
  value       = var.create_rds ? "postgresql://builder:builderbuilder@${try(aws_db_instance.pg[0].address, "")}:5432/builder" : null
  description = "Postgres connection URL if RDS is enabled"
}
