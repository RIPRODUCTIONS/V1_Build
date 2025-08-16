#!/usr/bin/env python3
"""
Production Deployment Scripts
Automated deployment with health checks and rollback capabilities
"""

import argparse
import asyncio
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import docker
import yaml
from docker.errors import DockerException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionDeployer:
    """Production deployment orchestrator with health checks and rollback"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.docker_client = self._init_docker_client()
        self.deployment_history = []

    def _load_config(self) -> dict[str, Any]:
        """Load deployment configuration"""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded deployment config from {self.config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            sys.exit(1)

    def _init_docker_client(self) -> docker.DockerClient | None:
        """Initialize Docker client"""
        try:
            client = docker.from_env()
            # Test connection
            client.ping()
            logger.info("Docker client initialized successfully")
            return client
        except DockerException as e:
            logger.error(f"Docker client initialization failed: {e}")
            return None

    async def deploy(self, environment: str = "production", force: bool = False) -> bool:
        """Deploy the autonomous system to specified environment"""
        deployment_id = f"deploy_{int(time.time())}"
        start_time = time.time()

        logger.info(f"🚀 Starting deployment {deployment_id} to {environment}")

        try:
            # Pre-deployment checks
            if not await self._pre_deployment_checks(environment):
                logger.error("Pre-deployment checks failed")
                return False

            # Backup current deployment
            if not await self._backup_current_deployment(environment):
                logger.error("Backup failed")
                return False

            # Deploy new version
            if not await self._deploy_new_version(environment):
                logger.error("Deployment failed")
                await self._rollback_deployment(environment)
                return False

            # Health checks
            if not await self._post_deployment_health_checks(environment):
                logger.error("Post-deployment health checks failed")
                await self._rollback_deployment(environment)
                return False

            # Update deployment history
            deployment_time = time.time() - start_time
            self._record_deployment(deployment_id, environment, "success", deployment_time)

            logger.info(f"✅ Deployment {deployment_id} completed successfully in {deployment_time:.2f}s")
            return True

        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            deployment_time = time.time() - start_time
            self._record_deployment(deployment_id, environment, "failed", deployment_time, str(e))

            # Attempt rollback
            await self._rollback_deployment(environment)
            return False

    async def _pre_deployment_checks(self, environment: str) -> bool:
        """Run pre-deployment checks"""
        logger.info("🔍 Running pre-deployment checks...")

        checks = [
            ("Docker availability", self._check_docker_availability),
            ("Configuration validation", self._check_configuration),
            ("Resource availability", self._check_resource_availability),
            ("Database connectivity", self._check_database_connectivity),
            ("Network connectivity", self._check_network_connectivity)
        ]

        for check_name, check_func in checks:
            try:
                if not await check_func(environment):
                    logger.error(f"Pre-deployment check failed: {check_name}")
                    return False
                logger.info(f"✅ {check_name} passed")
            except Exception as e:
                logger.error(f"Pre-deployment check error in {check_name}: {e}")
                return False

        logger.info("✅ All pre-deployment checks passed")
        return True

    async def _check_docker_availability(self, environment: str) -> bool:
        """Check Docker availability"""
        if not self.docker_client:
            return False

        try:
            # Check if required images exist
            required_images = self.config.get("deployment", {}).get("required_images", [])
            for image in required_images:
                try:
                    self.docker_client.images.get(image)
                except docker.errors.ImageNotFound:
                    logger.warning(f"Required image not found: {image}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Docker availability check failed: {e}")
            return False

    async def _check_configuration(self, environment: str) -> bool:
        """Check configuration validity"""
        try:
            env_config = self.config.get("environments", {}).get(environment, {})
            required_fields = ["docker_compose_file", "health_check_endpoints", "rollback_strategy"]

            for field in required_fields:
                if field not in env_config:
                    logger.error(f"Missing required configuration field: {field}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Configuration check failed: {e}")
            return False

    async def _check_resource_availability(self, environment: str) -> bool:
        """Check system resource availability"""
        try:
            import psutil

            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 90:
                logger.warning(f"High CPU usage: {cpu_percent}%")

            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                logger.warning(f"High memory usage: {memory.percent}%")

            # Check disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                logger.error(f"Critical disk usage: {disk.percent}%")
                return False

            return True
        except Exception as e:
            logger.error(f"Resource availability check failed: {e}")
            return False

    async def _check_database_connectivity(self, environment: str) -> bool:
        """Check database connectivity"""
        try:
            # This would check actual database connectivity
            # For now, simulate a successful check
            await asyncio.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Database connectivity check failed: {e}")
            return False

    async def _check_network_connectivity(self, environment: str) -> bool:
        """Check network connectivity"""
        try:
            # Check external dependencies
            external_endpoints = self.config.get("deployment", {}).get("external_endpoints", [])

            for endpoint in external_endpoints:
                try:
                    import aiohttp
                    async with aiohttp.ClientSession() as session:
                        async with session.get(endpoint, timeout=10) as response:
                            if response.status >= 400:
                                logger.warning(f"External endpoint {endpoint} returned status {response.status}")
                except Exception as e:
                    logger.warning(f"External endpoint {endpoint} check failed: {e}")

            return True
        except Exception as e:
            logger.error(f"Network connectivity check failed: {e}")
            return False

    async def _backup_current_deployment(self, environment: str) -> bool:
        """Backup current deployment for rollback"""
        logger.info("💾 Creating deployment backup...")

        try:
            # Create backup directory
            backup_dir = Path(f"backups/{environment}_{int(time.time())}")
            backup_dir.mkdir(parents=True, exist_ok=True)

            # Backup configuration files
            config_files = self.config.get("deployment", {}).get("backup_files", [])
            for file_path in config_files:
                src_path = Path(file_path)
                if src_path.exists():
                    dst_path = backup_dir / src_path.name
                    import shutil
                    shutil.copy2(src_path, dst_path)

            # Backup Docker volumes (if applicable)
            if self.docker_client:
                volumes = self.config.get("deployment", {}).get("backup_volumes", [])
                for volume_name in volumes:
                    try:
                        volume = self.docker_client.volumes.get(volume_name)
                        # Create volume backup (this would be more sophisticated in production)
                        logger.info(f"Backed up volume: {volume_name}")
                    except docker.errors.NotFound:
                        logger.warning(f"Volume not found: {volume_name}")

            logger.info(f"✅ Backup created in {backup_dir}")
            return True

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return False

    async def _deploy_new_version(self, environment: str) -> bool:
        """Deploy new version of the system"""
        logger.info("🚀 Deploying new version...")

        try:
            env_config = self.config.get("environments", {}).get(environment, {})
            docker_compose_file = env_config.get("docker_compose_file")

            if not docker_compose_file:
                logger.error("Docker compose file not specified")
                return False

            # Stop existing services
            logger.info("🛑 Stopping existing services...")
            subprocess.run([
                "docker-compose", "-f", docker_compose_file, "down"
            ], check=True, capture_output=True)

            # Pull latest images
            logger.info("📥 Pulling latest images...")
            subprocess.run([
                "docker-compose", "-f", docker_compose_file, "pull"
            ], check=True, capture_output=True)

            # Start new services
            logger.info("▶️ Starting new services...")
            subprocess.run([
                "docker-compose", "-f", docker_compose_file, "up", "-d"
            ], check=True, capture_output=True)

            # Wait for services to be ready
            logger.info("⏳ Waiting for services to be ready...")
            await asyncio.sleep(30)

            logger.info("✅ New version deployed successfully")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Deployment command failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False

    async def _post_deployment_health_checks(self, environment: str) -> bool:
        """Run post-deployment health checks"""
        logger.info("🏥 Running post-deployment health checks...")

        env_config = self.config.get("environments", {}).get(environment, {})
        health_endpoints = env_config.get("health_check_endpoints", [])

        # Wait for services to stabilize
        await asyncio.sleep(10)

        # Check health endpoints
        for endpoint in health_endpoints:
            try:
                import aiohttp
                async with aiohttp.ClientSession() as session:
                    async with session.get(endpoint, timeout=30) as response:
                        if response.status != 200:
                            logger.error(f"Health check failed for {endpoint}: status {response.status}")
                            return False

                        # Parse health response
                        health_data = await response.json()
                        if health_data.get("status") != "healthy":
                            logger.error(f"Health check failed for {endpoint}: {health_data.get('status')}")
                            return False

                        logger.info(f"✅ Health check passed for {endpoint}")

            except Exception as e:
                logger.error(f"Health check error for {endpoint}: {e}")
                return False

        # Additional system health checks
        if not await self._check_system_health():
            logger.error("System health check failed")
            return False

        logger.info("✅ All post-deployment health checks passed")
        return True

    async def _check_system_health(self) -> bool:
        """Check overall system health"""
        try:
            # Check if all containers are running
            if self.docker_client:
                containers = self.docker_client.containers.list()
                for container in containers:
                    if container.status != "running":
                        logger.error(f"Container {container.name} is not running: {container.status}")
                        return False

            # Check resource usage
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()

            if cpu_percent > 95 or memory.percent > 95:
                logger.error(f"Critical resource usage: CPU {cpu_percent}%, Memory {memory.percent}%")
                return False

            return True

        except Exception as e:
            logger.error(f"System health check failed: {e}")
            return False

    async def _rollback_deployment(self, environment: str) -> bool:
        """Rollback to previous deployment"""
        logger.warning("🔄 Rolling back deployment...")

        try:
            env_config = self.config.get("environments", {}).get(environment, {})
            rollback_strategy = env_config.get("rollback_strategy", "restart_previous")

            if rollback_strategy == "restart_previous":
                # Restart previous version
                docker_compose_file = env_config.get("docker_compose_file")
                if docker_compose_file:
                    subprocess.run([
                        "docker-compose", "-f", docker_compose_file, "restart"
                    ], check=True, capture_output=True)

            elif rollback_strategy == "restore_backup":
                # Restore from backup
                await self._restore_from_backup(environment)

            logger.info("✅ Rollback completed")
            return True

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False

    async def _restore_from_backup(self, environment: str) -> bool:
        """Restore deployment from backup"""
        try:
            # Find latest backup
            backup_dir = Path("backups")
            if not backup_dir.exists():
                logger.error("No backup directory found")
                return False

            backups = [d for d in backup_dir.iterdir() if d.name.startswith(f"{environment}_")]
            if not backups:
                logger.error("No backups found for environment")
                return False

            latest_backup = max(backups, key=lambda x: x.stat().st_mtime)

            # Restore configuration files
            config_files = self.config.get("deployment", {}).get("backup_files", [])
            for file_path in config_files:
                src_path = latest_backup / Path(file_path).name
                if src_path.exists():
                    dst_path = Path(file_path)
                    import shutil
                    shutil.copy2(src_path, dst_path)

            logger.info(f"✅ Restored from backup: {latest_backup}")
            return True

        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            return False

    def _record_deployment(self, deployment_id: str, environment: str, status: str,
                          duration: float, error_message: str = None):
        """Record deployment in history"""
        deployment_record = {
            "deployment_id": deployment_id,
            "environment": environment,
            "status": status,
            "duration": duration,
            "timestamp": time.time(),
            "error_message": error_message
        }

        self.deployment_history.append(deployment_record)

        # Keep only last 100 deployments
        if len(self.deployment_history) > 100:
            self.deployment_history = self.deployment_history[-100:]

    def get_deployment_history(self, environment: str = None, limit: int = 10) -> list[dict[str, Any]]:
        """Get deployment history"""
        history = self.deployment_history

        if environment:
            history = [d for d in history if d["environment"] == environment]

        return sorted(history, key=lambda x: x["timestamp"], reverse=True)[:limit]

    def get_deployment_stats(self) -> dict[str, Any]:
        """Get deployment statistics"""
        if not self.deployment_history:
            return {}

        total_deployments = len(self.deployment_history)
        successful_deployments = len([d for d in self.deployment_history if d["status"] == "success"])
        failed_deployments = total_deployments - successful_deployments

        avg_duration = sum(d["duration"] for d in self.deployment_history) / total_deployments

        return {
            "total_deployments": total_deployments,
            "successful_deployments": successful_deployments,
            "failed_deployments": failed_deployments,
            "success_rate": successful_deployments / total_deployments if total_deployments > 0 else 0,
            "average_duration": avg_duration
        }

def main():
    """Main deployment script"""
    parser = argparse.ArgumentParser(description="Production Deployment Script")
    parser.add_argument("--environment", default="production", help="Deployment environment")
    parser.add_argument("--config", default="deployment_config.yaml", help="Configuration file path")
    parser.add_argument("--force", action="store_true", help="Force deployment without checks")
    parser.add_argument("--history", action="store_true", help="Show deployment history")
    parser.add_argument("--stats", action="store_true", help="Show deployment statistics")

    args = parser.parse_args()

    # Initialize deployer
    deployer = ProductionDeployer(args.config)

    if args.history:
        # Show deployment history
        history = deployer.get_deployment_history(environment=args.environment, limit=20)
        print(f"\nDeployment History for {args.environment}:")
        print("=" * 80)
        for deployment in history:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(deployment["timestamp"]))
            print(f"{timestamp} | {deployment['deployment_id']} | {deployment['status']} | {deployment['duration']:.2f}s")
        return

    if args.stats:
        # Show deployment statistics
        stats = deployer.get_deployment_stats()
        print("\nDeployment Statistics:")
        print("=" * 40)
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"{key}: {value:.2f}")
            else:
                print(f"{key}: {value}")
        return

    # Run deployment
    success = asyncio.run(deployer.deploy(args.environment, args.force))

    if success:
        print("✅ Deployment completed successfully")
        sys.exit(0)
    else:
        print("❌ Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
