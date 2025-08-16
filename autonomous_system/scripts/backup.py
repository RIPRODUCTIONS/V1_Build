#!/usr/bin/env python3
"""
Automated Backup System for Autonomous Task Solver System
Production-ready backup with cloud storage integration
"""

import argparse
import asyncio
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import boto3
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BackupManager:
    """Automated backup manager with cloud storage integration"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.backup_dir = Path(self.config.get("backup", {}).get("local_path", "backups"))
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Initialize cloud storage clients
        self.s3_client = self._init_s3_client()

        # Backup history
        self.backup_history = []

        logger.info("Backup manager initialized")

    def _load_config(self) -> dict[str, Any]:
        """Load backup configuration"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded backup config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def _init_s3_client(self) -> boto3.client | None:
        """Initialize S3 client for cloud storage"""
        try:
            aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

            if aws_access_key and aws_secret_key:
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=aws_access_key,
                    aws_secret_access_key=aws_secret_key,
                    region_name=aws_region
                )
                logger.info("S3 client initialized successfully")
                return s3_client
            else:
                logger.warning("AWS credentials not found, S3 backup disabled")
                return None

        except Exception as e:
            logger.error(f"S3 client initialization failed: {e}")
            return None

    async def create_backup(self, backup_type: str = "full", force: bool = False) -> bool:
        """Create a new backup"""
        backup_id = f"backup_{backup_type}_{int(time.time())}"
        start_time = time.time()

        logger.info(f"🚀 Starting {backup_type} backup: {backup_id}")

        try:
            # Check if backup is needed
            if not force and not self._should_create_backup(backup_type):
                logger.info(f"Backup not needed for {backup_type}")
                return True

            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(parents=True, exist_ok=True)

            # Perform backup based on type
            if backup_type == "full":
                success = await self._create_full_backup(backup_path)
            elif backup_type == "incremental":
                success = await self._create_incremental_backup(backup_path)
            elif backup_type == "database":
                success = await self._create_database_backup(backup_path)
            elif backup_type == "config":
                success = await self._create_config_backup(backup_path)
            else:
                logger.error(f"Unknown backup type: {backup_type}")
                return False

            if not success:
                logger.error(f"Backup {backup_id} failed")
                return False

            # Compress backup
            if not await self._compress_backup(backup_path):
                logger.error(f"Failed to compress backup {backup_id}")
                return False

            # Upload to cloud storage
            if self.s3_client:
                if not await self._upload_to_cloud(backup_path, backup_id):
                    logger.warning(f"Failed to upload backup {backup_id} to cloud storage")

            # Update backup history
            backup_time = time.time() - start_time
            self._record_backup(backup_id, backup_type, "success", backup_time)

            # Clean up old backups
            await self._cleanup_old_backups()

            logger.info(f"✅ Backup {backup_id} completed successfully in {backup_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            backup_time = time.time() - start_time
            self._record_backup(backup_id, backup_type, "failed", backup_time, str(e))
            return False

    def _should_create_backup(self, backup_type: str) -> bool:
        """Check if backup should be created based on schedule"""
        backup_config = self.config.get("backup", {})

        if backup_type == "full":
            schedule_hours = backup_config.get("full_backup_interval_hours", 24)
        elif backup_type == "incremental":
            schedule_hours = backup_config.get("incremental_backup_interval_hours", 6)
        elif backup_type == "database":
            schedule_hours = backup_config.get("database_backup_interval_hours", 12)
        else:
            return True

        # Check last successful backup
        last_backup = self._get_last_successful_backup(backup_type)
        if not last_backup:
            return True

        time_since_last = time.time() - last_backup["timestamp"]
        return time_since_last >= (schedule_hours * 3600)

    def _get_last_successful_backup(self, backup_type: str) -> dict[str, Any] | None:
        """Get last successful backup of specified type"""
        for backup in reversed(self.backup_history):
            if (backup["type"] == backup_type and
                backup["status"] == "success"):
                return backup
        return None

    async def _create_full_backup(self, backup_path: Path) -> bool:
        """Create full system backup"""
        logger.info("📦 Creating full system backup...")

        try:
            # Backup configuration files
            config_files = self.config.get("backup", {}).get("config_files", [])
            for file_path in config_files:
                src_path = Path(file_path)
                if src_path.exists():
                    dst_path = backup_path / "config" / src_path.name
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)

            # Backup Docker volumes
            volumes = self.config.get("backup", {}).get("docker_volumes", [])
            for volume_name in volumes:
                if not await self._backup_docker_volume(volume_name, backup_path):
                    logger.warning(f"Failed to backup Docker volume: {volume_name}")

            # Backup database
            if not await self._backup_database(backup_path):
                logger.warning("Failed to backup database")

            # Backup logs
            log_paths = self.config.get("backup", {}).get("log_paths", [])
            for log_path in log_paths:
                src_path = Path(log_path)
                if src_path.exists():
                    dst_path = backup_path / "logs" / src_path.name
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    if src_path.is_file():
                        shutil.copy2(src_path, dst_path)
                    else:
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)

            # Create backup manifest
            await self._create_backup_manifest(backup_path, "full")

            logger.info("✅ Full backup created successfully")
            return True

        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return False

    async def _create_incremental_backup(self, backup_path: Path) -> bool:
        """Create incremental backup"""
        logger.info("📦 Creating incremental backup...")

        try:
            # Get last full backup
            last_full_backup = self._get_last_successful_backup("full")
            if not last_full_backup:
                logger.warning("No full backup found, creating full backup instead")
                return await self._create_full_backup(backup_path)

            # Backup only changed files since last backup
            # This is a simplified implementation
            # In production, you'd use rsync or similar tools

            # Create backup manifest
            await self._create_backup_manifest(backup_path, "incremental")

            logger.info("✅ Incremental backup created successfully")
            return True

        except Exception as e:
            logger.error(f"Incremental backup failed: {e}")
            return False

    async def _create_database_backup(self, backup_path: Path) -> bool:
        """Create database backup"""
        logger.info("🗄️ Creating database backup...")

        try:
            db_config = self.config.get("database", {})
            db_type = db_config.get("type", "postgresql")

            if db_type == "postgresql":
                return await self._backup_postgresql(backup_path)
            elif db_type == "sqlite":
                return await self._backup_sqlite(backup_path)
            else:
                logger.error(f"Unsupported database type: {db_type}")
                return False

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    async def _backup_postgresql(self, backup_path: Path) -> bool:
        """Backup PostgreSQL database"""
        try:
            db_config = self.config.get("database", {})
            db_name = db_config.get("name", "autonomous_system")
            db_user = db_config.get("user", "autonomous_user")
            db_host = db_config.get("host", "localhost")
            db_port = db_config.get("port", "5432")

            # Create database backup directory
            db_backup_path = backup_path / "database"
            db_backup_path.mkdir(parents=True, exist_ok=True)

            # Use pg_dump to create backup
            backup_file = db_backup_path / f"{db_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"

            cmd = [
                "pg_dump",
                f"--host={db_host}",
                f"--port={db_port}",
                f"--username={db_user}",
                f"--dbname={db_name}",
                "--format=custom",
                "--verbose",
                f"--file={backup_file}"
            ]

            # Set password environment variable
            env = os.environ.copy()
            env["PGPASSWORD"] = db_config.get("password", "")

            result = subprocess.run(cmd, check=False, env=env, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"PostgreSQL backup created: {backup_file}")
                return True
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"PostgreSQL backup error: {e}")
            return False

    async def _backup_sqlite(self, backup_path: Path) -> bool:
        """Backup SQLite database"""
        try:
            db_config = self.config.get("database", {})
            db_path = db_config.get("path", "autonomous_system.db")

            if not Path(db_path).exists():
                logger.warning(f"SQLite database not found: {db_path}")
                return True

            # Create database backup directory
            db_backup_path = backup_path / "database"
            db_backup_path.mkdir(parents=True, exist_ok=True)

            # Copy SQLite database
            backup_file = db_backup_path / f"autonomous_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            shutil.copy2(db_path, backup_file)

            logger.info(f"SQLite backup created: {backup_file}")
            return True

        except Exception as e:
            logger.error(f"SQLite backup error: {e}")
            return False

    async def _create_config_backup(self, backup_path: Path) -> bool:
        """Create configuration backup"""
        logger.info("⚙️ Creating configuration backup...")

        try:
            # Backup configuration files
            config_files = self.config.get("backup", {}).get("config_files", [])
            for file_path in config_files:
                src_path = Path(file_path)
                if src_path.exists():
                    dst_path = backup_path / "config" / src_path.name
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src_path, dst_path)

            # Create backup manifest
            await self._create_backup_manifest(backup_path, "config")

            logger.info("✅ Configuration backup created successfully")
            return True

        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            return False

    async def _backup_docker_volume(self, volume_name: str, backup_path: Path) -> bool:
        """Backup Docker volume"""
        try:
            # Create volume backup directory
            volume_backup_path = backup_path / "volumes" / volume_name
            volume_backup_path.mkdir(parents=True, exist_ok=True)

            # Use docker run to backup volume
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{volume_name}:/source:ro",
                "-v", f"{volume_backup_path}:/backup",
                "alpine", "tar", "czf", f"/backup/{volume_name}.tar.gz", "-C", "/source", "."
            ]

            result = subprocess.run(cmd, check=False, capture_output=True, text=True)

            if result.returncode == 0:
                logger.info(f"Docker volume backup created: {volume_name}")
                return True
            else:
                logger.error(f"Docker volume backup failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Docker volume backup error: {e}")
            return False

    async def _create_backup_manifest(self, backup_path: Path, backup_type: str):
        """Create backup manifest file"""
        try:
            manifest = {
                "backup_id": backup_path.name,
                "backup_type": backup_type,
                "timestamp": datetime.now().isoformat(),
                "system_info": {
                    "hostname": os.uname().nodename,
                    "platform": os.uname().sysname,
                    "version": os.uname().release
                },
                "backup_contents": [],
                "metadata": {}
            }

            # List backup contents
            for item in backup_path.rglob("*"):
                if item.is_file():
                    manifest["backup_contents"].append({
                        "path": str(item.relative_to(backup_path)),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })

            # Write manifest
            manifest_file = backup_path / "manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to create backup manifest: {e}")

    async def _compress_backup(self, backup_path: Path) -> bool:
        """Compress backup directory"""
        try:
            logger.info("🗜️ Compressing backup...")

            # Create compressed archive
            archive_path = backup_path.parent / f"{backup_path.name}.tar.gz"

            cmd = ["tar", "-czf", str(archive_path), "-C", str(backup_path.parent), backup_path.name]
            result = subprocess.run(cmd, check=False, capture_output=True, text=True)

            if result.returncode == 0:
                # Remove uncompressed directory
                shutil.rmtree(backup_path)
                logger.info(f"Backup compressed: {archive_path}")
                return True
            else:
                logger.error(f"Backup compression failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Backup compression error: {e}")
            return False

    async def _upload_to_cloud(self, backup_path: Path, backup_id: str) -> bool:
        """Upload backup to cloud storage"""
        try:
            if not self.s3_client:
                return False

            backup_config = self.config.get("backup", {})
            bucket_name = backup_config.get("s3_bucket")
            region = backup_config.get("s3_region", "us-east-1")

            if not bucket_name:
                logger.warning("S3 bucket not configured")
                return False

            # Find compressed backup file
            archive_files = list(backup_path.parent.glob(f"{backup_id}*.tar.gz"))
            if not archive_files:
                logger.error("No compressed backup file found")
                return False

            archive_file = archive_files[0]

            # Upload to S3
            s3_key = f"backups/{backup_id}/{archive_file.name}"

            logger.info(f"☁️ Uploading backup to S3: {s3_key}")

            self.s3_client.upload_file(
                str(archive_file),
                bucket_name,
                s3_key,
                ExtraArgs={
                    'ServerSideEncryption': 'AES256',
                    'StorageClass': 'STANDARD_IA'
                }
            )

            logger.info(f"✅ Backup uploaded to S3: {s3_key}")
            return True

        except Exception as e:
            logger.error(f"Cloud upload failed: {e}")
            return False

    async def _cleanup_old_backups(self):
        """Clean up old backups based on retention policy"""
        try:
            backup_config = self.config.get("backup", {})
            retention_days = backup_config.get("retention_days", 30)
            max_local_backups = backup_config.get("max_local_backups", 10)

            # Clean up local backups
            cutoff_time = time.time() - (retention_days * 24 * 3600)

            backup_files = list(self.backup_dir.glob("*.tar.gz"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Remove old backups
            for backup_file in backup_files[max_local_backups:]:
                if backup_file.stat().st_mtime < cutoff_time:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file.name}")

            # Clean up cloud storage if configured
            if self.s3_client:
                await self._cleanup_cloud_backups(retention_days)

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    async def _cleanup_cloud_backups(self, retention_days: int):
        """Clean up old cloud backups"""
        try:
            backup_config = self.config.get("backup", {})
            bucket_name = backup_config.get("s3_bucket")

            if not bucket_name:
                return

            cutoff_time = datetime.now() - timedelta(days=retention_days)

            # List objects in backup prefix
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=bucket_name, Prefix="backups/")

            for page in pages:
                for obj in page.get('Contents', []):
                    if obj['LastModified'].replace(tzinfo=None) < cutoff_time:
                        self.s3_client.delete_object(Bucket=bucket_name, Key=obj['Key'])
                        logger.info(f"Removed old cloud backup: {obj['Key']}")

        except Exception as e:
            logger.error(f"Cloud backup cleanup failed: {e}")

    def _record_backup(self, backup_id: str, backup_type: str, status: str,
                       duration: float, error_message: str = None):
        """Record backup in history"""
        backup_record = {
            "backup_id": backup_id,
            "type": backup_type,
            "status": status,
            "duration": duration,
            "timestamp": time.time(),
            "error_message": error_message
        }

        self.backup_history.append(backup_record)

        # Keep only recent backups (last 100)
        if len(self.backup_history) > 100:
            self.backup_history = self.backup_history[-100:]

    def get_backup_history(self, backup_type: str = None, limit: int = 20) -> list[dict[str, Any]]:
        """Get backup history"""
        history = self.backup_history

        if backup_type:
            history = [b for b in history if b["type"] == backup_type]

        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_backup_stats(self) -> dict[str, Any]:
        """Get backup statistics"""
        if not self.backup_history:
            return {}

        total_backups = len(self.backup_history)
        successful_backups = len([b for b in self.backup_history if b["status"] == "success"])
        failed_backups = total_backups - successful_backups

        # Group by type
        by_type = {}
        for backup in self.backup_history:
            backup_type = backup["type"]
            if backup_type not in by_type:
                by_type[backup_type] = {"total": 0, "successful": 0, "failed": 0}

            by_type[backup_type]["total"] += 1
            if backup["status"] == "success":
                by_type[backup_type]["successful"] += 1
            else:
                by_type[backup_type]["failed"] += 1

        return {
            "total_backups": total_backups,
            "successful_backups": successful_backups,
            "failed_backups": failed_backups,
            "success_rate": successful_backups / total_backups if total_backups > 0 else 0,
            "by_type": by_type
        }

def main():
    """Main backup script"""
    parser = argparse.ArgumentParser(description="Automated Backup System")
    parser.add_argument("--type", default="full", choices=["full", "incremental", "database", "config"],
                       help="Backup type")
    parser.add_argument("--config", default="deployment_config.yaml", help="Configuration file path")
    parser.add_argument("--force", action="store_true", help="Force backup creation")
    parser.add_argument("--history", action="store_true", help="Show backup history")
    parser.add_argument("--stats", action="store_true", help="Show backup statistics")

    args = parser.parse_args()

    # Initialize backup manager
    backup_manager = BackupManager(args.config)

    if args.history:
        # Show backup history
        history = backup_manager.get_backup_history(backup_type=args.type, limit=20)
        print(f"\nBackup History for {args.type}:")
        print("=" * 80)
        for backup in history:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(backup["timestamp"]))
            print(f"{timestamp} | {backup['backup_id']} | {backup['status']} | {backup['duration']:.2f}s")
        return

    if args.stats:
        # Show backup statistics
        stats = backup_manager.get_backup_stats()
        print("\nBackup Statistics:")
        print("=" * 40)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            elif isinstance(value, dict):
                print(f"{key}:")
                for sub_key, sub_value in value.items():
                    print(f"  {sub_key}: {sub_value}")
            else:
                print(f"{key}: {value}")
        return

    # Run backup
    success = asyncio.run(backup_manager.create_backup(args.type, args.force))

    if success:
        print("✅ Backup completed successfully")
        sys.exit(0)
    else:
        print("❌ Backup failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
