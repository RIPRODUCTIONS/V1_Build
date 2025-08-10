resource "aws_db_subnet_group" "db" {
  count      = var.create_rds ? 1 : 0
  name       = "self-healing-mvp-db"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_db_instance" "pg" {
  count                    = var.create_rds ? 1 : 0
  identifier               = "self-healing-mvp-pg"
  engine                   = "postgres"
  engine_version           = "15"
  instance_class           = var.db_instance_class
  allocated_storage        = 20
  db_name                  = "builder"
  username                 = "builder"
  password                 = "builderbuilder"
  skip_final_snapshot      = true
  publicly_accessible      = false
  vpc_security_group_ids   = [] # toggle: add SGs when ready
  db_subnet_group_name     = aws_db_subnet_group.db[0].name
  deletion_protection      = false
  apply_immediately        = true
  backup_retention_period  = 0
  auto_minor_version_upgrade = true
}
