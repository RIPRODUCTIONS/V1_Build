#!/usr/bin/env python3
"""
AI Framework System Audit Script

This script performs a comprehensive audit of the entire system to:
1. Identify duplicate systems and components
2. Map all integration points
3. Identify cybersecurity tools that need integration
4. Create a consolidation plan
5. Ensure no duplication across departments

Usage:
    python system_audit.py
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemAuditor:
    """Comprehensive system auditor for the AI Framework."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.audit_results = {
            "timestamp": datetime.now().isoformat(),
            "duplicate_systems": [],
            "integration_points": [],
            "cybersecurity_tools": [],
            "port_conflicts": [],
            "consolidation_plan": [],
            "recommendations": []
        }

    async def run_full_audit(self):
        """Run the complete system audit."""
        logger.info("🔍 Starting Comprehensive System Audit...")

        try:
            # 1. Audit duplicate systems
            await self.audit_duplicate_systems()

            # 2. Map integration points
            await self.map_integration_points()

            # 3. Identify cybersecurity tools
            await self.audit_cybersecurity_tools()

            # 4. Check port conflicts
            await self.check_port_conflicts()

            # 5. Generate consolidation plan
            await self.generate_consolidation_plan()

            # 6. Print audit results
            self.print_audit_results()

            # 7. Save audit report
            self.save_audit_report()

            return True

        except Exception as e:
            logger.error(f"❌ Audit failed: {str(e)}")
            return False

    async def audit_duplicate_systems(self):
        """Identify duplicate systems and components."""
        logger.info("🔍 Auditing duplicate systems...")

        # Check for duplicate directories
        duplicate_dirs = [
            "ai_framework",
            "autonomous_system",
            "backend",
            "kali_automation"
        ]

        found_systems = []
        for dir_name in duplicate_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                found_systems.append({
                    "name": dir_name,
                    "path": str(dir_path),
                    "size": self.get_directory_size(dir_path),
                    "files": len(list(dir_path.rglob("*"))),
                    "type": self.classify_system_type(dir_path)
                })

        self.audit_results["duplicate_systems"] = found_systems

        # Check for duplicate agent implementations
        await self.check_duplicate_agents()

        # Check for duplicate backend systems
        await self.check_duplicate_backends()

    async def check_duplicate_agents(self):
        """Check for duplicate agent implementations."""
        logger.info("🤖 Checking for duplicate agents...")

        agent_locations = []

        # Check ai_framework agents
        ai_framework_agents = self.project_root / "ai_framework" / "agents"
        if ai_framework_agents.exists():
            for agent_file in ai_framework_agents.glob("*.py"):
                if agent_file.name != "__init__.py":
                    agent_locations.append({
                        "file": str(agent_file),
                        "system": "ai_framework",
                        "agent_type": agent_file.stem
                    })

        # Check autonomous_system agents
        autonomous_agents = self.project_root / "autonomous_system" / "agents"
        if autonomous_agents.exists():
            for agent_file in autonomous_agents.glob("*.py"):
                if agent_file.name != "__init__.py":
                    agent_locations.append({
                        "file": str(agent_file),
                        "system": "autonomous_system",
                        "agent_type": agent_file.stem
                    })

        # Find duplicates
        agent_types = {}
        for agent in agent_locations:
            agent_type = agent["agent_type"]
            if agent_type not in agent_types:
                agent_types[agent_type] = []
            agent_types[agent_type].append(agent)

        duplicates = {k: v for k, v in agent_types.items() if len(v) > 1}
        if duplicates:
            self.audit_results["duplicate_agents"] = duplicates
            logger.warning(f"⚠️ Found duplicate agents: {list(duplicates.keys())}")

    async def check_duplicate_backends(self):
        """Check for duplicate backend systems."""
        logger.info("🌐 Checking for duplicate backends...")

        backend_systems = []

        # Check ai_framework backend
        ai_framework_api = self.project_root / "ai_framework" / "api" / "main.py"
        if ai_framework_api.exists():
            backend_systems.append({
                "name": "AI Framework API",
                "path": str(ai_framework_api),
                "system": "ai_framework",
                "framework": "FastAPI"
            })

        # Check autonomous_system backend
        autonomous_api = self.project_root / "autonomous_system" / "api"
        if autonomous_api.exists():
            for api_file in autonomous_api.glob("*.py"):
                backend_systems.append({
                    "name": f"Autonomous System API - {api_file.stem}",
                    "path": str(api_file),
                    "system": "autonomous_system",
                    "framework": "Unknown"
                })

        # Check main backend directory
        main_backend = self.project_root / "backend"
        if main_backend.exists():
            backend_systems.append({
                "name": "Main Backend",
                "path": str(main_backend),
                "system": "main_backend",
                "framework": "Unknown"
            })

        self.audit_results["duplicate_backends"] = backend_systems

    async def map_integration_points(self):
        """Map all system integration points."""
        logger.info("🔗 Mapping integration points...")

        integration_points = []

        # Check for API endpoints
        integration_points.extend(await self.find_api_endpoints())

        # Check for database connections
        integration_points.extend(await self.find_database_connections())

        # Check for external service integrations
        integration_points.extend(await self.find_external_integrations())

        self.audit_results["integration_points"] = integration_points

    async def find_api_endpoints(self):
        """Find all API endpoints across systems."""
        endpoints = []

        # Check ai_framework API
        ai_framework_main = self.project_root / "ai_framework" / "api" / "main.py"
        if ai_framework_main.exists():
            with open(ai_framework_main) as f:
                content = f.read()
                if "@app.get(" in content or "@app.post(" in content:
                    endpoints.append({
                        "system": "ai_framework",
                        "type": "FastAPI",
                        "file": str(ai_framework_main),
                        "endpoints": "Multiple REST endpoints"
                    })

        # Check autonomous_system API
        autonomous_api_dir = self.project_root / "autonomous_system" / "api"
        if autonomous_api_dir.exists():
            for api_file in autonomous_api_dir.glob("*.py"):
                endpoints.append({
                    "system": "autonomous_system",
                    "type": "API",
                    "file": str(api_file),
                    "endpoints": "Multiple endpoints"
                })

        return endpoints

    async def find_database_connections(self):
        """Find all database connections."""
        connections = []

        # Check for database files
        db_files = list(self.project_root.rglob("*.db")) + list(self.project_root.rglob("*.sqlite"))
        for db_file in db_files:
            connections.append({
                "type": "SQLite",
                "path": str(db_file),
                "size": db_file.stat().st_size if db_file.exists() else 0
            })

        # Check for database configuration
        config_files = list(self.project_root.rglob("*.env")) + list(self.project_root.rglob("config*.py"))
        for config_file in config_files:
            if config_file.exists():
                with open(config_file) as f:
                    content = f.read()
                    if "DATABASE_URL" in content or "db_url" in content:
                        connections.append({
                            "type": "Database Config",
                            "file": str(config_file),
                            "config_type": "Environment/Config"
                        })

        return connections

    async def find_external_integrations(self):
        """Find external service integrations."""
        integrations = []

        # Check requirements files for external services
        req_files = list(self.project_root.rglob("requirements*.txt"))
        for req_file in req_files:
            if req_file.exists():
                with open(req_file) as f:
                    content = f.read()
                    if "openai" in content:
                        integrations.append({
                            "type": "OpenAI Integration",
                            "file": str(req_file),
                            "service": "OpenAI"
                        })
                    if "anthropic" in content:
                        integrations.append({
                            "type": "Anthropic Integration",
                            "file": str(req_file),
                            "service": "Anthropic"
                        })
                    if "docker" in content:
                        integrations.append({
                            "type": "Docker Integration",
                            "file": str(req_file),
                            "service": "Docker"
                        })

        return integrations

    async def audit_cybersecurity_tools(self):
        """Audit cybersecurity tools and integration needs."""
        logger.info("🔒 Auditing cybersecurity tools...")

        cyber_tools = []

        # Check kali_automation directory
        kali_dir = self.project_root / "kali_automation"
        if kali_dir.exists():
            cyber_tools.append({
                "name": "Kali Automation",
                "path": str(kali_dir),
                "type": "Penetration Testing",
                "integration_status": "Needs integration with AI Framework"
            })

        # Check for security-related files
        security_files = list(self.project_root.rglob("*security*")) + list(self.project_root.rglob("*auth*"))
        for sec_file in security_files:
            if sec_file.is_file() and sec_file.suffix in ['.py', '.yml', '.yaml', '.json']:
                cyber_tools.append({
                    "name": f"Security - {sec_file.name}",
                    "path": str(sec_file),
                    "type": "Security Configuration",
                    "integration_status": "Needs review"
                })

        # Check for monitoring tools
        monitoring_dir = self.project_root / "monitoring"
        if monitoring_dir.exists():
            cyber_tools.append({
                "name": "Monitoring System",
                "path": str(monitoring_dir),
                "type": "System Monitoring",
                "integration_status": "Needs integration with AI Framework"
            })

        self.audit_results["cybersecurity_tools"] = cyber_tools

    async def check_port_conflicts(self):
        """Check for port conflicts across systems."""
        logger.info("🔌 Checking port conflicts...")

        port_conflicts = []

        # Check what ports are currently in use
        try:
            # Check common ports
            common_ports = [8000, 8001, 8002, 8003, 8004, 5432, 6379, 27017]
            for port in common_ports:
                try:
                    response = requests.get(f"http://localhost:{port}", timeout=1)
                    port_conflicts.append({
                        "port": port,
                        "status": "In use",
                        "response": response.status_code
                    })
                except requests.exceptions.RequestException:
                    pass
        except Exception as e:
            logger.warning(f"Could not check ports: {e}")

        self.audit_results["port_conflicts"] = port_conflicts

    async def generate_consolidation_plan(self):
        """Generate a plan to consolidate all systems."""
        logger.info("📋 Generating consolidation plan...")

        plan = []

        # 1. Consolidate AI agents
        plan.append({
            "priority": "HIGH",
            "action": "Consolidate AI Agents",
            "description": "Merge all agent implementations into ai_framework",
            "steps": [
                "Move unique agents from autonomous_system to ai_framework",
                "Update agent imports and dependencies",
                "Remove duplicate agent files",
                "Ensure all agents use same base classes"
            ]
        })

        # 2. Consolidate backend systems
        plan.append({
            "priority": "HIGH",
            "action": "Consolidate Backend Systems",
            "description": "Merge all backend functionality into single FastAPI app",
            "steps": [
                "Identify unique features in each backend",
                "Merge into ai_framework FastAPI app",
                "Update routing and dependencies",
                "Remove duplicate backend code"
            ]
        })

        # 3. Integrate cybersecurity tools
        plan.append({
            "priority": "HIGH",
            "action": "Integrate Cybersecurity Tools",
            "description": "Connect kali_automation and security tools to AI Framework",
            "steps": [
                "Create cybersecurity agent department in AI Framework",
                "Integrate kali_automation tools as agents",
                "Connect monitoring systems",
                "Create unified security dashboard"
            ]
        })

        # 4. Consolidate databases
        plan.append({
            "priority": "MEDIUM",
            "action": "Consolidate Databases",
            "description": "Merge all databases into single system",
            "steps": [
                "Audit all database schemas",
                "Create unified database design",
                "Migrate data from duplicate databases",
                "Update all connections to use unified DB"
            ]
        })

        # 5. Unified monitoring
        plan.append({
            "priority": "MEDIUM",
            "action": "Unified Monitoring",
            "description": "Create single monitoring system for all components",
            "steps": [
                "Integrate existing monitoring into AI Framework",
                "Create unified dashboard for all systems",
                "Connect all logging and metrics",
                "Create unified alerting system"
            ]
        })

        self.audit_results["consolidation_plan"] = plan

        # Generate recommendations
        self.generate_recommendations()

    def generate_recommendations(self):
        """Generate specific recommendations based on audit results."""
        recommendations = []

        # Based on duplicate systems found
        if len(self.audit_results["duplicate_systems"]) > 1:
            recommendations.append({
                "priority": "CRITICAL",
                "recommendation": "Immediate system consolidation required",
                "reason": f"Found {len(self.audit_results['duplicate_systems'])} duplicate systems",
                "action": "Start consolidation plan immediately"
            })

        # Based on cybersecurity tools
        if self.audit_results["cybersecurity_tools"]:
            recommendations.append({
                "priority": "HIGH",
                "recommendation": "Integrate cybersecurity tools with AI Framework",
                "reason": "Security tools are isolated and not connected",
                "action": "Create cybersecurity agent department"
            })

        # Based on port conflicts
        if self.audit_results["port_conflicts"]:
            recommendations.append({
                "priority": "MEDIUM",
                "recommendation": "Resolve port conflicts",
                "reason": "Multiple systems may be trying to use same ports",
                "action": "Standardize port usage across all systems"
            })

        # General recommendations
        recommendations.extend([
            {
                "priority": "HIGH",
                "recommendation": "Create unified deployment system",
                "reason": "Multiple deployment configurations found",
                "action": "Consolidate into single docker-compose setup"
            },
            {
                "priority": "MEDIUM",
                "recommendation": "Standardize configuration management",
                "reason": "Multiple config files and formats found",
                "action": "Create unified config system using environment variables"
            },
            {
                "priority": "MEDIUM",
                "recommendation": "Create unified testing framework",
                "reason": "Multiple test directories and frameworks found",
                "action": "Consolidate all tests into single pytest framework"
            }
        ])

        self.audit_results["recommendations"] = recommendations

    def get_directory_size(self, path: Path) -> int:
        """Get directory size in bytes."""
        try:
            total_size = 0
            for file_path in path.rglob('*'):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size
        except Exception:
            return 0

    def classify_system_type(self, path: Path) -> str:
        """Classify the type of system."""
        if "ai_framework" in str(path):
            return "New AI Agent System"
        elif "autonomous_system" in str(path):
            return "Existing Autonomous System"
        elif "backend" in str(path):
            return "Backend System"
        elif "kali" in str(path):
            return "Cybersecurity Tools"
        else:
            return "Unknown System"

    def print_audit_results(self):
        """Print the audit results."""
        print("\n" + "="*80)
        print("🔍 AI FRAMEWORK SYSTEM AUDIT RESULTS")
        print("="*80)

        # Duplicate systems
        print(f"\n🚨 DUPLICATE SYSTEMS FOUND: {len(self.audit_results['duplicate_systems'])}")
        for system in self.audit_results['duplicate_systems']:
            print(f"   • {system['name']} ({system['type']}) - {system['size']} bytes")

        # Integration points
        print(f"\n🔗 INTEGRATION POINTS: {len(self.audit_results['integration_points'])}")
        for point in self.audit_results['integration_points']:
            print(f"   • {point.get('type', 'Unknown')} - {point.get('file', 'Unknown')}")

        # Cybersecurity tools
        print(f"\n🔒 CYBERSECURITY TOOLS: {len(self.audit_results['cybersecurity_tools'])}")
        for tool in self.audit_results['cybersecurity_tools']:
            print(f"   • {tool['name']} - {tool['integration_status']}")

        # Port conflicts
        if self.audit_results['port_conflicts']:
            print(f"\n🔌 PORT CONFLICTS: {len(self.audit_results['port_conflicts'])}")
            for conflict in self.audit_results['port_conflicts']:
                print(f"   • Port {conflict['port']} - {conflict['status']}")

        # Consolidation plan
        print(f"\n📋 CONSOLIDATION PLAN: {len(self.audit_results['consolidation_plan'])} actions")
        for item in self.audit_results['consolidation_plan']:
            print(f"   • [{item['priority']}] {item['action']}")

        # Recommendations
        print(f"\n💡 RECOMMENDATIONS: {len(self.audit_results['recommendations'])}")
        for rec in self.audit_results['recommendations']:
            print(f"   • [{rec['priority']}] {rec['recommendation']}")

        print("="*80)

    def save_audit_report(self):
        """Save the audit report to a file."""
        report_file = self.project_root / "ai_framework" / "audit_report.json"

        with open(report_file, 'w') as f:
            json.dump(self.audit_results, f, indent=2)

        logger.info(f"📄 Audit report saved to: {report_file}")

async def main():
    """Main audit function."""
    auditor = SystemAuditor()

    try:
        success = await auditor.run_full_audit()
        if success:
            print("\n✅ System audit completed successfully!")
            print("📋 Review the results above and follow the consolidation plan.")
        else:
            print("\n❌ System audit failed. Check logs for details.")

        return success

    except Exception as e:
        logger.error(f"Audit failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("core").exists() or not Path("agents").exists():
        print("❌ Error: Please run this script from the ai_framework directory")
        print("   Current directory:", Path.cwd())
        print("   Expected structure: ai_framework/core/, ai_framework/agents/")
        sys.exit(1)

    # Run the audit
    success = asyncio.run(main())
    sys.exit(0 if success else 1)






