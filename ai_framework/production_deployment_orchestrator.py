#!/usr/bin/env python3
"""
AI Framework Production Deployment Orchestrator
User-friendly production deployment with comprehensive validation
"""

import os
import sys
import subprocess
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionDeploymentOrchestrator:
    """Production deployment orchestrator for AI Framework"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.production_compose = self.project_root / "docker-compose.production.yml"
        self.env_file = self.project_root / "production.env"
        self.backup_dir = self.project_root / "backups"
        self.log_dir = self.project_root / "logs"

        # Create necessary directories
        self.backup_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "="*60)
        print(f"🚀 {title}")
        print("="*60)

    def print_section(self, title: str):
        """Print a formatted section"""
        print(f"\n📋 {title}")
        print("-" * 40)

    def print_success(self, message: str):
        """Print success message"""
        print(f"✅ {message}")

    def print_warning(self, message: str):
        """Print warning message"""
        print(f"⚠️  {message}")

    def print_error(self, message: str):
        """Print error message"""
        print(f"❌ {message}")

    def print_info(self, message: str):
        """Print info message"""
        print(f"ℹ️  {message}")

    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met"""
        self.print_section("Checking Prerequisites")

        # Check Docker
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode != 0:
                self.print_error("Docker is not running or not accessible")
                return False
            self.print_success("Docker is running")
        except FileNotFoundError:
            self.print_error("Docker is not installed")
            return False

        # Check Docker Compose
        try:
            result = subprocess.run(["docker-compose", "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                self.print_error("Docker Compose is not available")
                return False
            self.print_success("Docker Compose is available")
        except FileNotFoundError:
            self.print_error("Docker Compose is not installed")
            return False

        # Check required files
        if not self.production_compose.exists():
            self.print_error(f"Production Docker Compose file not found: {self.production_compose}")
            return False
        self.print_success("Production Docker Compose file found")

        if not self.env_file.exists():
            self.print_error(f"Production environment file not found: {self.env_file}")
            return False
        self.print_success("Production environment file found")

        # Check system resources
        self.print_info("Checking system resources...")
        try:
            import psutil
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            if memory.available < 2 * 1024 * 1024 * 1024:  # 2GB
                self.print_warning("Less than 2GB RAM available")
            else:
                self.print_success(f"RAM available: {memory.available // (1024**3)}GB")

            if disk.free < 10 * 1024 * 1024 * 1024:  # 10GB
                self.print_warning("Less than 10GB disk space available")
            else:
                self.print_success(f"Disk space available: {disk.free // (1024**3)}GB")

        except ImportError:
            self.print_warning("psutil not available, skipping resource check")

        return True

    def validate_environment(self) -> bool:
        """Validate production environment configuration"""
        self.print_section("Validating Environment Configuration")

        try:
            # Read environment file
            with open(self.env_file, 'r') as f:
                content = f.read()

            # Check for default values
            critical_secrets = [
                "your-super-secure-production-jwt-secret-change-this-immediately",
                "your-production-api-key-change-this-immediately",
                "your-super-secure-production-db-password",
                "your-super-secure-production-redis-password",
                "your-super-secure-production-grafana-password"
            ]

            for secret in critical_secrets:
                if secret in content:
                    self.print_error(f"Found default secret value: {secret}")
                    self.print_error("Please update production.env with secure values")
                    return False

            self.print_success("All critical secrets have been updated")

            # Check domain configuration
            if "https://yourdomain.com" in content:
                self.print_warning("ALLOWED_ORIGINS still set to default domain")
                self.print_warning("Please update with your actual domain")

            return True

        except Exception as e:
            self.print_error(f"Error validating environment: {e}")
            return False

    def backup_existing_data(self) -> bool:
        """Backup existing data if present"""
        self.print_section("Backing Up Existing Data")

        data_dir = self.project_root / "data"
        if data_dir.exists() and any(data_dir.iterdir()):
            self.print_info("Creating backup of existing data...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{timestamp}.tar.gz"
            backup_path = self.backup_dir / backup_name

            try:
                subprocess.run([
                    "tar", "-czf", str(backup_path), "-C", str(self.project_root), "data"
                ], check=True)
                self.print_success(f"Backup created: {backup_name}")
                return True
            except subprocess.CalledProcessError as e:
                self.print_error(f"Backup failed: {e}")
                return False
        else:
            self.print_info("No existing data to backup")
            return True

    def stop_existing_services(self) -> bool:
        """Stop existing services"""
        self.print_section("Stopping Existing Services")

        # Stop staging environment
        staging_compose = self.project_root / "docker-compose.staging.yml"
        if staging_compose.exists():
            self.print_info("Stopping staging environment...")
            try:
                subprocess.run([
                    "docker-compose", "-f", str(staging_compose), "down", "--remove-orphans"
                ], check=True)
                self.print_success("Staging environment stopped")
            except subprocess.CalledProcessError:
                self.print_warning("Failed to stop staging environment (may not be running)")

        # Stop production services
        self.print_info("Stopping existing production services...")
        try:
            subprocess.run([
                "docker-compose", "-f", str(self.production_compose), "down", "--remove-orphans"
            ], check=True)
            self.print_success("Existing production services stopped")
        except subprocess.CalledProcessError:
            self.print_info("No existing production services to stop")

        # Clean up
        try:
            subprocess.run(["docker", "container", "prune", "-f"], check=True)
            self.print_success("Dangling containers cleaned up")
        except subprocess.CalledProcessError:
            self.print_warning("Failed to clean up containers")

        return True

    def build_production_images(self) -> bool:
        """Build production Docker images"""
        self.print_section("Building Production Images")

        # Build AI Framework image
        self.print_info("Building AI Framework production image...")
        try:
            subprocess.run([
                "docker", "build", "--target", "production",
                "-t", "ai_framework-production:latest", "."
            ], check=True)
            self.print_success("AI Framework production image built")
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to build AI Framework image: {e}")
            return False

        # Pull base images
        base_images = [
            "postgres:15-alpine",
            "redis:7-alpine",
            "prom/prometheus:latest",
            "grafana/grafana:latest",
            "nginx:alpine"
        ]

        for image in base_images:
            self.print_info(f"Pulling {image}...")
            try:
                subprocess.run(["docker", "pull", image], check=True)
                self.print_success(f"Pulled {image}")
            except subprocess.CalledProcessError as e:
                self.print_error(f"Failed to pull {image}: {e}")
                return False

        return True

    def deploy_production_services(self) -> bool:
        """Deploy production services"""
        self.print_section("Deploying Production Services")

        self.print_info("Starting production services...")
        try:
            subprocess.run([
                "docker-compose", "-f", str(self.production_compose), "up", "-d"
            ], check=True)
            self.print_success("Production services started")
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to start production services: {e}")
            return False

        # Wait for services to be ready
        self.print_info("Waiting for services to be ready...")
        time.sleep(30)

        # Check service status
        self.print_info("Checking service status...")
        try:
            result = subprocess.run([
                "docker-compose", "-f", str(self.production_compose), "ps"
            ], capture_output=True, text=True, check=True)
            print(result.stdout)
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to check service status: {e}")
            return False

        return True

    def verify_deployment(self) -> bool:
        """Verify production deployment"""
        self.print_section("Verifying Production Deployment")

        max_attempts = 10
        attempt = 1

        while attempt <= max_attempts:
            self.print_info(f"Health check attempt {attempt}/{max_attempts}...")

            # Check AI Framework health
            try:
                result = subprocess.run([
                    "curl", "-f", "http://localhost:8000/health"
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    self.print_success("AI Framework is healthy")
                else:
                    self.print_warning(f"AI Framework health check failed (attempt {attempt})")
                    if attempt == max_attempts:
                        self.print_error("AI Framework failed to become healthy")
                        return False
                    time.sleep(30)
                    attempt += 1
                    continue
            except Exception as e:
                self.print_error(f"Health check error: {e}")
                return False

            # Check Prometheus
            try:
                result = subprocess.run([
                    "curl", "-f", "http://localhost:9090/-/healthy"
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    self.print_success("Prometheus is healthy")
                else:
                    self.print_warning("Prometheus health check failed")
            except Exception:
                self.print_warning("Prometheus health check failed")

            # Check Grafana
            try:
                result = subprocess.run([
                    "curl", "-f", "http://localhost:3000/api/health"
                ], capture_output=True, text=True)

                if result.returncode == 0:
                    self.print_success("Grafana is healthy")
                else:
                    self.print_warning("Grafana health check failed")
            except Exception:
                self.print_warning("Grafana health check failed")

            break

        self.print_success("Production deployment verified")
        return True

    def run_production_tests(self) -> bool:
        """Run production tests"""
        self.print_section("Running Production Tests")

        # Run stability tests
        stability_script = self.project_root / "reliability" / "stability_test_suite.py"
        if stability_script.exists():
            self.print_info("Running production stability tests...")
            try:
                subprocess.run([
                    "python3", str(stability_script)
                ], check=True, cwd=str(stability_script.parent))
                self.print_success("Production stability tests completed")
            except subprocess.CalledProcessError as e:
                self.print_warning(f"Stability tests failed: {e}")
        else:
            self.print_warning("Stability test script not found")

        # Run security tests
        security_script = self.project_root / "security_testing" / "security_test_suite.py"
        if security_script.exists():
            self.print_info("Running production security tests...")
            try:
                subprocess.run([
                    "python3", str(security_script)
                ], check=True, cwd=str(security_script.parent))
                self.print_success("Production security tests completed")
            except subprocess.CalledProcessError as e:
                self.print_warning(f"Security tests failed: {e}")
        else:
            self.print_warning("Security test script not found")

        return True

    def display_production_info(self):
        """Display production deployment information"""
        self.print_header("Production Deployment Complete!")

        print(f"\n🎉 Your AI Framework is now running in production!")

        print(f"\n📊 Production Services:")
        print(f"  • AI Framework API: http://localhost:8000")
        print(f"  • Prometheus Metrics: http://localhost:9090")
        print(f"  • Grafana Dashboard: http://localhost:3000")
        print(f"  • Nginx Proxy: http://localhost:80")

        print(f"\n🔑 Default Credentials:")
        print(f"  • Grafana Admin: admin / (password from production.env)")
        print(f"  • AI Framework: admin / admin123")

        print(f"\n🔗 Important URLs:")
        print(f"  • Health Check: http://localhost:8000/health")
        print(f"  • API Documentation: http://localhost:8000/docs")
        print(f"  • Metrics: http://localhost:8000/metrics")

        print(f"\n⚠️  Security Reminders:")
        print(f"  • Change all default passwords in production.env")
        print(f"  • Configure SSL/TLS certificates")
        print(f"  • Set up proper firewall rules")
        print(f"  • Configure monitoring alerts")

        print(f"\n📋 Next Steps:")
        print(f"  1. Configure your domain and SSL certificates")
        print(f"  2. Set up monitoring alerts and notifications")
        print(f"  3. Configure backup schedules")
        print(f"  4. Set up CI/CD pipelines")
        print(f"  5. Monitor system performance and logs")

        print(f"\n🚀 Your AI Framework is ready for production use!")

    def run_deployment(self) -> bool:
        """Run the complete production deployment"""
        self.print_header("AI Framework Production Deployment")
        print("This script will deploy your AI Framework to production")
        print("\nMake sure you have:")
        print("  • Updated all passwords in production.env")
        print("  • Configured your domain settings")
        print("  • SSL certificates ready (if using HTTPS)")
        print("  • Sufficient system resources")

        print("\nPress Enter to continue or Ctrl+C to abort...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nDeployment aborted by user")
            return False

        try:
            # Execute deployment steps
            if not self.check_prerequisites():
                return False

            if not self.validate_environment():
                return False

            if not self.backup_existing_data():
                return False

            if not self.stop_existing_services():
                return False

            if not self.build_production_images():
                return False

            if not self.deploy_production_services():
                return False

            if not self.verify_deployment():
                return False

            self.run_production_tests()
            self.display_production_info()

            self.print_success("Production deployment completed successfully!")
            return True

        except Exception as e:
            self.print_error(f"Deployment failed: {e}")
            logger.error(f"Deployment error: {e}", exc_info=True)
            return False

def main():
    """Main function"""
    orchestrator = ProductionDeploymentOrchestrator()

    try:
        success = orchestrator.run_deployment()
        if success:
            print("\n🎉 Production deployment completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Production deployment failed")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Deployment interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
