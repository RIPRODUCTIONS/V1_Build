region          = "us-west-2"
vpc_cidr        = "10.42.0.0/16"
allowed_cidrs   = ["0.0.0.0/0"] # toggle: narrow for prod
cluster_min     = 2
cluster_desired = 2
cluster_max     = 6
create_rds      = false # toggle: on when ready
db_instance_class = "db.t4g.micro"
