#!/usr/bin/env python3
"""
Kali Linux Automation Platform - Main Entry Point

This script demonstrates the usage of all tool categories in the platform.
It provides a command-line interface for running various security testing workflows.
"""

import argparse
import asyncio
import logging
import os
from typing import Any

from tools.database_security import DatabaseSecurityTools
from tools.exploitation_tools import ExploitationTools
from tools.forensics_tools import ForensicsTools

# Import all tool categories
from tools.information_gathering import InformationGatheringTools
from tools.mobile_security import MobileSecurityTools
from tools.password_attacks import PasswordAttackTools
from tools.post_exploitation import PostExploitationTools
from tools.reverse_engineering import ReverseEngineeringTools
from tools.sniffing_spoofing import SniffingSpoofingTools
from tools.vulnerability_assessment import VulnerabilityAssessmentTools
from tools.web_application_security import WebApplicationSecurityTools
from tools.wireless_attacks import WirelessAttackTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class KaliAutomationPlatform:
    """Main platform class that orchestrates all tool categories."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize the platform with all tool categories."""
        self.config = config or {}

        # Initialize all tool categories
        self.tools = {
            'information_gathering': InformationGatheringTools(config),
            'vulnerability_assessment': VulnerabilityAssessmentTools(config),
            'web_application_security': WebApplicationSecurityTools(config),
            'database_security': DatabaseSecurityTools(config),
            'password_attacks': PasswordAttackTools(config),
            'wireless_attacks': WirelessAttackTools(config),
            'exploitation_tools': ExploitationTools(config),
            'forensics_tools': ForensicsTools(config),
            'reverse_engineering': ReverseEngineeringTools(config),
            'post_exploitation': PostExploitationTools(config),
            'sniffing_spoofing': SniffingSpoofingTools(config),
            'mobile_security': MobileSecurityTools(config)
        }

        logger.info("Kali Linux Automation Platform initialized")
        logger.info(f"Available tool categories: {list(self.tools.keys())}")

    async def run_workflow(self, workflow_name: str, target: str, **kwargs) -> dict[str, Any]:
        """Run a predefined security testing workflow."""
        workflows = {
            'full_penetration_test': self._full_penetration_test,
            'web_app_assessment': self._web_app_assessment,
            'network_security_audit': self._network_security_audit,
            'mobile_app_assessment': self._mobile_app_assessment,
            'forensic_investigation': self._forensic_investigation,
            'malware_analysis': self._malware_analysis
        }

        if workflow_name not in workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        logger.info(f"Starting workflow: {workflow_name} on target: {target}")
        return await workflows[workflow_name](target, **kwargs)

    async def _full_penetration_test(self, target: str, **kwargs) -> dict[str, Any]:
        """Run a full penetration testing workflow."""
        results = {}

        try:
            # Phase 1: Information Gathering
            logger.info("Phase 1: Information Gathering")
            info_tools = self.tools['information_gathering']
            network_info = await info_tools.discover_network(target)
            results['information_gathering'] = network_info

            # Phase 2: Vulnerability Assessment
            logger.info("Phase 2: Vulnerability Assessment")
            vuln_tools = self.tools['vulnerability_assessment']
            vuln_scan = await vuln_tools.scan_target(target)
            results['vulnerability_assessment'] = vuln_scan

            # Phase 3: Web Application Testing (if applicable)
            if 'http' in str(network_info).lower() or 'https' in str(network_info).lower():
                logger.info("Phase 3: Web Application Security Testing")
                web_tools = self.tools['web_application_security']
                web_scan = await web_tools.scan_web_application(f"http://{target}")
                results['web_application_security'] = web_scan

            # Phase 4: Database Testing (if applicable)
            if 'mysql' in str(network_info).lower() or 'postgresql' in str(network_info).lower():
                logger.info("Phase 4: Database Security Testing")
                db_tools = self.tools['database_security']
                db_scan = await db_tools.test_database_security(target)
                results['database_security'] = db_scan

            # Phase 5: Exploitation (if vulnerabilities found)
            if vuln_scan and hasattr(vuln_scan, 'vulnerabilities') and vuln_scan.vulnerabilities:
                logger.info("Phase 5: Exploitation Testing")
                exploit_tools = self.tools['exploitation_tools']
                exploit_results = await exploit_tools.run_automated_exploitation(target, vuln_scan)
                results['exploitation'] = exploit_results

            logger.info("Full penetration test completed successfully")

        except Exception as e:
            logger.error(f"Error during full penetration test: {e}")
            results['error'] = str(e)

        return results

    async def _web_app_assessment(self, target: str, **kwargs) -> dict[str, Any]:
        """Run a web application security assessment workflow."""
        results = {}

        try:
            # Ensure target has protocol
            if not target.startswith(('http://', 'https://')):
                target = f"http://{target}"

            # Web application security testing
            web_tools = self.tools['web_application_security']
            web_scan = await web_tools.scan_web_application(target)
            results['web_application_security'] = web_scan

            # Database testing (if applicable)
            if 'sql' in str(web_scan).lower() or 'injection' in str(web_scan).lower():
                db_tools = self.tools['database_security']
                db_scan = await db_tools.test_database_security(target)
                results['database_security'] = db_scan

            logger.info("Web application assessment completed successfully")

        except Exception as e:
            logger.error(f"Error during web app assessment: {e}")
            results['error'] = str(e)

        return results

    async def _network_security_audit(self, target: str, **kwargs) -> dict[str, Any]:
        """Run a network security audit workflow."""
        results = {}

        try:
            # Network discovery
            info_tools = self.tools['information_gathering']
            network_info = await info_tools.discover_network(target)
            results['network_discovery'] = network_info

            # Vulnerability assessment
            vuln_tools = self.tools['vulnerability_assessment']
            vuln_scan = await vuln_tools.scan_target(target)
            results['vulnerability_assessment'] = vuln_scan

            # Wireless security (if applicable)
            wireless_tools = self.tools['wireless_attacks']
            # Note: This would require specific wireless interface configuration
            results['wireless_security'] = "Wireless testing requires specific interface configuration"

            logger.info("Network security audit completed successfully")

        except Exception as e:
            logger.error(f"Error during network security audit: {e}")
            results['error'] = str(e)

        return results

    async def _mobile_app_assessment(self, target: str, **kwargs) -> dict[str, Any]:
        """Run a mobile application security assessment workflow."""
        results = {}

        try:
            # Mobile app analysis
            mobile_tools = self.tools['mobile_security']

            if target.endswith('.apk'):
                # Android app analysis
                mobile_app = await mobile_tools.analyze_android_app(target)
                results['mobile_app_analysis'] = mobile_app

                # Static analysis
                static_analysis = await mobile_tools.perform_static_analysis(target)
                results['static_analysis'] = static_analysis

                # Malware analysis
                malware_analysis = await mobile_tools.perform_malware_analysis(target)
                results['malware_analysis'] = malware_analysis
            else:
                results['error'] = "Unsupported mobile app format. Use .apk for Android apps."

            logger.info("Mobile app assessment completed successfully")

        except Exception as e:
            logger.error(f"Error during mobile app assessment: {e}")
            results['error'] = str(e)

        return results

    async def _forensic_investigation(self, target: str, **kwargs) -> dict[str, Any]:
        """Run a forensic investigation workflow."""
        results = {}

        try:
            # Forensics tools
            forensics_tools = self.tools['forensics_tools']

            # File analysis
            if os.path.isfile(target):
                file_analysis = await forensics_tools.analyze_file(target)
                results['file_analysis'] = file_analysis

            # Memory analysis (if applicable)
            if target.endswith('.raw') or 'memory' in target.lower():
                memory_analysis = await forensics_tools.analyze_memory_dump(target)
                results['memory_analysis'] = memory_analysis

            # Generate report
            report_file = forensics_tools.generate_report()
            results['report_file'] = report_file

            logger.info("Forensic investigation completed successfully")

        except Exception as e:
            logger.error(f"Error during forensic investigation: {e}")
            results['error'] = str(e)

        return results

    async def _malware_analysis(self, target: str, **kwargs) -> dict[str, Any]:
        """Run a malware analysis workflow."""
        results = {}

        try:
            # Reverse engineering tools
            re_tools = self.tools['reverse_engineering']

            # Static analysis
            static_analysis = await re_tools.perform_static_analysis(target)
            results['static_analysis'] = static_analysis

            # Generate YARA rules
            yara_rules = await re_tools.generate_yara_rules(target)
            results['yara_rules'] = yara_rules

            # Generate report
            report_file = re_tools.generate_report()
            results['report_file'] = report_file

            logger.info("Malware analysis completed successfully")

        except Exception as e:
            logger.error(f"Error during malware analysis: {e}")
            results['error'] = str(e)

        return results

    def list_tools(self) -> dict[str, Any]:
        """List all available tools and their capabilities."""
        tool_info = {}

        for name, tool in self.tools.items():
            tool_info[name] = {
                'class': tool.__class__.__name__,
                'description': tool.__class__.__doc__ or 'No description available',
                'methods': [method for method in dir(tool) if not method.startswith('_')]
            }

        return tool_info

    def get_tool(self, tool_name: str):
        """Get a specific tool by name."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self.tools[tool_name]

    async def cleanup(self):
        """Clean up all tools and resources."""
        logger.info("Cleaning up platform resources...")

        for name, tool in self.tools.items():
            try:
                if hasattr(tool, 'cleanup'):
                    tool.cleanup()
                logger.info(f"Cleaned up {name}")
            except Exception as e:
                logger.error(f"Error cleaning up {name}: {e}")


async def main():
    """Main entry point for the platform."""
    parser = argparse.ArgumentParser(
        description='Kali Linux Automation Platform',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full penetration test
  python main.py --workflow full_penetration_test --target 192.168.1.100

  # Run web application assessment
  python main.py --workflow web_app_assessment --target example.com

  # Run mobile app assessment
  python main.py --workflow mobile_app_assessment --target app.apk

  # List available tools
  python main.py --list-tools

  # Run specific tool
  python main.py --tool information_gathering --method discover_network --target 192.168.1.0/24
        """
    )

    parser.add_argument('--workflow', choices=[
        'full_penetration_test', 'web_app_assessment', 'network_security_audit',
        'mobile_app_assessment', 'forensic_investigation', 'malware_analysis'
    ], help='Security testing workflow to run')

    parser.add_argument('--target', help='Target to test (IP, domain, file, etc.)')

    parser.add_argument('--tool', help='Specific tool to use')

    parser.add_argument('--method', help='Method to call on the tool')

    parser.add_argument('--list-tools', action='store_true', help='List all available tools')

    parser.add_argument('--config', help='Configuration file path')

    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load configuration
    config = {}
    if args.config:
        # Load config from file
        pass

    # Initialize platform
    platform = KaliAutomationPlatform(config)

    try:
        if args.list_tools:
            # List all available tools
            tools = platform.list_tools()
            print("\n🛠️  Available Tools:")
            print("=" * 50)
            for name, info in tools.items():
                print(f"\n📦 {name.upper()}")
                print(f"   Class: {info['class']}")
                print(f"   Description: {info['description']}")
                print(f"   Methods: {', '.join(info['methods'][:5])}...")

            return

        if args.workflow and args.target:
            # Run workflow
            results = await platform.run_workflow(args.workflow, args.target)
            print(f"\n✅ Workflow '{args.workflow}' completed")
            print(f"📊 Results: {len(results)} components")

            for component, result in results.items():
                if hasattr(result, 'success'):
                    status = "✅ Success" if result.success else "❌ Failed"
                    print(f"   {component}: {status}")
                else:
                    print(f"   {component}: {type(result).__name__}")

            return

        if args.tool and args.method and args.target:
            # Run specific tool method
            tool = platform.get_tool(args.tool)
            method = getattr(tool, args.method)

            if asyncio.iscoroutinefunction(method):
                result = await method(args.target)
            else:
                result = method(args.target)

            print(f"\n✅ Tool method '{args.method}' completed")
            print(f"📊 Result: {result}")

            return

        # Show help if no valid arguments
        parser.print_help()

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
    except Exception as e:
        logger.error(f"Error during execution: {e}")
        print(f"\n❌ Error: {e}")
    finally:
        # Cleanup
        await platform.cleanup()


if __name__ == "__main__":
    # Run the main function
    asyncio.run(main())
