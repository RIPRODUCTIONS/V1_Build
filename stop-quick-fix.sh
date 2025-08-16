#!/bin/bash
# Quick Stop for M3 Max Quick Fix

echo "🛑 Stopping Quick Fix Environment..."

# Stop containers
docker-compose -f docker-compose.quick-fix.yml down --remove-orphans

# Clean up networks
docker network prune -f

echo "✅ Quick Fix Environment stopped and cleaned up"
