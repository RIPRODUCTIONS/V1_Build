#!/bin/bash

# n8n Backup and Monitoring Script
# Automated backup solution for n8n data and configurations

set -euo pipefail

# Configuration
BACKUP_DIR="/backups"
N8N_DATA_DIR="/home/node/.n8n"
RETENTION_DAYS=30
LOG_FILE="/var/log/n8n-backup.log"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Health check function
health_check() {
    local url="http://localhost:5678/healthz"
    if curl -f -s "$url" > /dev/null 2>&1; then
        log "✅ n8n health check passed"
        return 0
    else
        log "❌ n8n health check failed"
        return 1
    fi
}

# Backup function
backup_n8n() {
    log "🔄 Starting n8n backup..."
    
    local backup_file="$BACKUP_DIR/n8n_backup_$TIMESTAMP.tar.gz"
    
    # Check if n8n is healthy before backup
    if ! health_check; then
        log "⚠️  n8n is not healthy, proceeding with backup anyway"
    fi
    
    # Create backup
    if tar -czf "$backup_file" -C "$(dirname "$N8N_DATA_DIR")" "$(basename "$N8N_DATA_DIR")" 2>/dev/null; then
        log "✅ Backup created: $backup_file"
        
        # Verify backup
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            log "✅ Backup verification passed"
            
            # Set permissions
            chmod 600 "$backup_file"
            
            # Calculate backup size
            local size=$(du -h "$backup_file" | cut -f1)
            log "📊 Backup size: $size"
            
            return 0
        else
            log "❌ Backup verification failed"
            rm -f "$backup_file"
            return 1
        fi
    else
        log "❌ Backup creation failed"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "🧹 Cleaning up old backups..."
    
    local deleted_count=0
    
    # Find and delete old backups
    find "$BACKUP_DIR" -name "n8n_backup_*.tar.gz" -type f -mtime +$RETENTION_DAYS -print0 | \
    while IFS= read -r -d '' file; do
        if rm "$file"; then
            log "🗑️  Deleted old backup: $(basename "$file")"
            ((deleted_count++))
        else
            log "❌ Failed to delete: $(basename "$file")"
        fi
    done
    
    log "🧹 Cleanup completed. Deleted $deleted_count old backups"
}

# Monitor disk space
monitor_disk_space() {
    log "💾 Monitoring disk space..."
    
    local backup_usage=$(df "$BACKUP_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    local data_usage=$(df "$N8N_DATA_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
    
    log "📊 Backup directory usage: ${backup_usage}%"
    log "📊 Data directory usage: ${data_usage}%"
    
    # Alert if usage is high
    if [ "$backup_usage" -gt 80 ]; then
        log "⚠️  WARNING: Backup directory usage is high (${backup_usage}%)"
    fi
    
    if [ "$data_usage" -gt 80 ]; then
        log "⚠️  WARNING: Data directory usage is high (${data_usage}%)"
    fi
}

# Send status notification (placeholder for integration with notification systems)
send_notification() {
    local status="$1"
    local message="$2"
    
    # TODO: Integrate with Slack, email, or other notification systems
    log "📢 Notification: [$status] $message"
    
    # Example webhook notification (uncomment and configure)
    # curl -X POST -H 'Content-type: application/json' \
    #     --data "{\"text\":\"n8n Backup Status: [$status] $message\"}" \
    #     "$SLACK_WEBHOOK_URL"
}

# Main execution
main() {
    log "🚀 Starting n8n backup and monitoring cycle"
    
    # Monitor system health
    monitor_disk_space
    
    # Perform backup
    if backup_n8n; then
        send_notification "SUCCESS" "Backup completed successfully"
    else
        send_notification "FAILURE" "Backup failed - check logs"
        exit 1
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    log "✅ Backup and monitoring cycle completed"
}

# Error handling
trap 'log "❌ Script failed with error on line $LINENO"; exit 1' ERR

# Run main function
main "$@"