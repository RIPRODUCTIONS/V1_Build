#!/bin/bash
echo "Starting backup process..."
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB > /backups/backup_$(date +%Y%m%d_%H%M%S).sql
echo "Backup completed!"
