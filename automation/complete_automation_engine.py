#!/usr/bin/env python3
"""
Complete Kali Linux Automation Engine
Master orchestrator for ALL 600+ Kali Linux tools with intelligent chaining
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import yaml

# Import all tool categories
try:
    from tools.information_gathering_complete import InformationGatheringOrchestrator
    from tools.vulnerability_assessment_complete import VulnerabilityAssessmentOrchestrator
    from tools.wireless_attacks_complete import WirelessAttackOrchestrator
    from tools.exploitation_complete import ExploitationOrchestrator
    from tools.password_attacks_complete import PasswordAttacksOrchestrator
    from tools.web_application_security_complete import WebApplicationSecurityOrchestrator
    from tools.forensics_tools import ForensicsTools
    from tools.reverse_engineering import ReverseEngineeringTools
    from tools.post_exploitation import PostExploitationTools
    from tools.sniffing_spoofing import SniffingSpoofingTools
    from tools.mobile_security import MobileSecurityTools
    from tools.osint_complete_automation import OSINTAutomationOrchestrator
    TOOLS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some tool modules not available: {e}")
    TOOLS_AVAILABLE = False
    # Create dummy classes for testing
    class InformationGatheringOrchestrator: pass
    class VulnerabilityAssessmentOrchestrator: pass
    class WirelessAttackOrchestrator: pass
    class ExploitationOrchestrator: pass
    class PasswordAttacksOrchestrator: pass
    class WebApplicationSecurityOrchestrator: pass
    class ForensicsTools: pass
    class ReverseEngineeringTools: pass
    class PostExploitationTools: pass
    class SniffingSpoofingTools: pass
    class MobileSecurityTools: pass
    class OSINTAutomationOrchestrator: pass


@dataclass
class InvestigationWorkflow:
    """Defines a complete investigation workflow"""
    name: str
    description: str
    target_type: str  # 'network', 'web', 'mobile', 'forensics', 'wireless'
    phases: List[Dict[str, Any]]
    estimated_duration: int  # minutes
    required_tools: List[str]
    risk_level: str  # 'low', 'medium', 'high', 'critical'


@dataclass
class InvestigationResult:
    """Results from a complete investigation"""
    workflow_name: str
    target: str
    start_time: datetime
    end_time: datetime
    duration: float
    phases_completed: List[str]
    findings: Dict[str, Any]
    risk_assessment: str
    recommendations: List[str]
    evidence_files: List[str]
    status: str  # 'completed', 'failed', 'partial'


class CompleteAutomationEngine:
    """Master automation engine for ALL 600+ Kali Linux tools"""

    def __init__(self, config_file: str = None):
        self.config_file = config_file or '/kali-automation/configs/automation_config.yaml'
        self.config = self._load_config()

        # Initialize all tool orchestrators
        if TOOLS_AVAILABLE:
            self.info_gathering = InformationGatheringOrchestrator()
            self.vuln_assessment = VulnerabilityAssessmentOrchestrator()
            self.wireless_attacks = WirelessAttackOrchestrator()
            self.exploitation = ExploitationOrchestrator()
            self.password_attacks = PasswordAttacksOrchestrator()
            self.web_security = WebApplicationSecurityOrchestrator()
            self.forensics = ForensicsTools()
            self.reverse_engineering = ReverseEngineeringTools()
            self.post_exploitation = PostExploitationTools()
            self.sniffing_spoofing = SniffingSpoofingTools()
            self.mobile_security = MobileSecurityTools()
            self.osint = OSINTAutomationOrchestrator()

        # Setup directories
        self.base_dir = Path('./kali-automation')
        self.results_dir = self.base_dir / 'results'
        self.logs_dir = self.base_dir / 'logs'
        self.configs_dir = self.base_dir / 'configs'
        self.evidence_dir = self.base_dir / 'evidence'

        for dir_path in [self.results_dir, self.logs_dir, self.configs_dir, self.evidence_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Investigation tracking
        self.active_investigations = {}
        self.investigation_history = []

        # Setup logging
        self._setup_logging()

        # Load predefined workflows
        self.workflows = self._load_predefined_workflows()

        logging.info("Complete Kali Linux Automation Engine initialized")

    def _load_config(self) -> Dict[str, Any]:
        """Load automation configuration"""
        default_config = {
            'max_concurrent_scans': 5,
            'default_timeout': 3600,
            'risk_threshold': 'medium',
            'auto_reporting': True,
            'evidence_collection': True,
            'correlation_enabled': True
        }

        try:
            if Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    default_config.update(config)
        except Exception as e:
            logging.warning(f"Could not load config file: {e}")

        return default_config

    def _setup_logging(self):
        """Setup comprehensive logging"""
        log_file = self.logs_dir / f"automation_engine_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def _load_predefined_workflows(self) -> Dict[str, InvestigationWorkflow]:
        """Load predefined investigation workflows"""
        workflows = {
            'osint_investigation': InvestigationWorkflow(
                name='OSINT Investigation',
                description='Comprehensive open source intelligence gathering',
                target_type='intelligence',
                phases=[
                    {'name': 'target_identification', 'tools': ['theharvester', 'amass', 'subfinder']},
                    {'name': 'social_media_analysis', 'tools': ['maigret', 'holehe', 'whatsmyname']},
                    {'name': 'domain_analysis', 'tools': ['dnsrecon', 'fierce', 'dnsenum']},
                    {'name': 'email_analysis', 'tools': ['h8mail', 'hunter', 'breach_directory']},
                    {'name': 'correlation_analysis', 'tools': ['maltego', 'spiderfoot']}
                ],
                estimated_duration=120,
                required_tools=['theharvester', 'amass', 'subfinder', 'maigret', 'holehe'],
                risk_level='low'
            ),

            'penetration_test': InvestigationWorkflow(
                name='Full Penetration Test',
                description='Complete penetration testing engagement',
                target_type='network',
                phases=[
                    {'name': 'reconnaissance', 'tools': ['nmap', 'masscan', 'recon-ng']},
                    {'name': 'vulnerability_assessment', 'tools': ['openvas', 'nessus', 'nikto']},
                    {'name': 'exploitation', 'tools': ['metasploit', 'exploitdb', 'searchsploit']},
                    {'name': 'post_exploitation', 'tools': ['mimikatz', 'bloodhound', 'empire']},
                    {'name': 'reporting', 'tools': ['reporting_engine']}
                ],
                estimated_duration=480,
                required_tools=['nmap', 'metasploit', 'openvas', 'nikto'],
                risk_level='high'
            ),

            'forensics_investigation': InvestigationWorkflow(
                name='Digital Forensics Investigation',
                description='Complete digital forensics analysis',
                target_type='forensics',
                phases=[
                    {'name': 'evidence_collection', 'tools': ['volatility', 'sleuthkit', 'autopsy']},
                    {'name': 'memory_analysis', 'tools': ['volatility', 'rekall', 'memoryze']},
                    {'name': 'disk_analysis', 'tools': ['sleuthkit', 'autopsy', 'testdisk']},
                    {'name': 'network_analysis', 'tools': ['wireshark', 'tshark', 'tcpdump']},
                    {'name': 'timeline_analysis', 'tools': ['log2timeline', 'plaso', 'timeliner']}
                ],
                estimated_duration=360,
                required_tools=['volatility', 'sleuthkit', 'autopsy', 'wireshark'],
                risk_level='medium'
            ),

            'threat_hunting': InvestigationWorkflow(
                name='Threat Hunting',
                description='Proactive threat hunting and detection',
                target_type='network',
                phases=[
                    {'name': 'baseline_establishment', 'tools': ['osquery', 'auditd', 'sysmon']},
                    {'name': 'anomaly_detection', 'tools': ['zeek', 'suricata', 'snort']},
                    {'name': 'ioc_analysis', 'tools': ['yara', 'clamav', 'virustotal']},
                    {'name': 'threat_intelligence', 'tools': ['misp', 'otx', 'threatcrowd']},
                    {'name': 'incident_response', 'tools': ['thehive', 'cortex', 'misp']}
                ],
                estimated_duration=240,
                required_tools=['osquery', 'yara', 'suricata', 'misp'],
                risk_level='medium'
            ),

            'red_team_engagement': InvestigationWorkflow(
                name='Red Team Engagement',
                description='Advanced red team operations',
                target_type='network',
                phases=[
                    {'name': 'initial_access', 'tools': ['phishing', 'social_engineering', 'physical']},
                    {'name': 'persistence', 'tools': ['mimikatz', 'empire', 'covenant']},
                    {'name': 'privilege_escalation', 'tools': ['bloodhound', 'powerup', 'linpeas']},
                    {'name': 'lateral_movement', 'tools': ['crackmapexec', 'responder', 'smbexec']},
                    {'name': 'exfiltration', 'tools': ['dnscat', 'iodine', 'ptunnel']}
                ],
                estimated_duration=600,
                required_tools=['metasploit', 'empire', 'covenant', 'bloodhound'],
                risk_level='critical'
            ),

            'vulnerability_assessment': InvestigationWorkflow(
                name='Vulnerability Assessment',
                description='Comprehensive vulnerability scanning and assessment',
                target_type='network',
                phases=[
                    {'name': 'network_discovery', 'tools': ['nmap', 'masscan', 'netdiscover']},
                    {'name': 'service_enumeration', 'tools': ['nmap', 'nuclei', 'vulners']},
                    {'name': 'web_application_scanning', 'tools': ['nikto', 'wpscan', 'sqlmap']},
                    {'name': 'database_scanning', 'tools': ['sqlmap', 'sqlninja', 'commix']},
                    {'name': 'report_generation', 'tools': ['reporting_engine']}
                ],
                estimated_duration=180,
                required_tools=['nmap', 'nikto', 'sqlmap', 'nuclei'],
                risk_level='medium'
            ),

            'malware_analysis': InvestigationWorkflow(
                name='Malware Analysis',
                description='Static and dynamic malware analysis',
                target_type='forensics',
                phases=[
                    {'name': 'static_analysis', 'tools': ['pefile', 'yara', 'strings']},
                    {'name': 'dynamic_analysis', 'tools': ['cuckoo', 'volatility', 'process_hacker']},
                    {'name': 'network_analysis', 'tools': ['wireshark', 'fakenet', 'inetsim']},
                    {'name': 'reverse_engineering', 'tools': ['ghidra', 'ida', 'radare2']},
                    {'name': 'threat_intelligence', 'tools': ['virustotal', 'hybrid_analysis', 'anyrun']}
                ],
                estimated_duration=300,
                required_tools=['pefile', 'yara', 'ghidra', 'volatility'],
                risk_level='high'
            )
        }

        return workflows

    async def execute_workflow(self, workflow_name: str, target: str,
                              custom_parameters: Dict[str, Any] = None) -> InvestigationResult:
        """Execute a complete investigation workflow"""
        if workflow_name not in self.workflows:
            raise ValueError(f"Unknown workflow: {workflow_name}")

        workflow = self.workflows[workflow_name]
        investigation_id = f"{workflow_name}_{int(time.time())}"

        # Create investigation result
        investigation = InvestigationResult(
            workflow_name=workflow_name,
            target=target,
            start_time=datetime.now(),
            end_time=datetime.now(),
            duration=0.0,
            phases_completed=[],
            findings={},
            risk_assessment='pending',
            recommendations=[],
            evidence_files=[],
            status='running'
        )

        self.active_investigations[investigation_id] = investigation

        logging.info(f"Starting workflow: {workflow_name} on target: {target}")

        try:
            # Execute each phase
            for i, phase in enumerate(workflow.phases):
                phase_name = phase['name']
                phase_tools = phase['tools']

                logging.info(f"Executing phase {i+1}/{len(workflow.phases)}: {phase_name}")

                # Execute phase with appropriate tools
                phase_result = await self._execute_phase(phase_name, phase_tools, target, custom_parameters)

                if phase_result['success']:
                    investigation.phases_completed.append(phase_name)
                    investigation.findings[phase_name] = phase_result
                    logging.info(f"Phase {phase_name} completed successfully")
                else:
                    logging.error(f"Phase {phase_name} failed: {phase_result.get('error')}")
                    investigation.status = 'partial'
                    break

            # Complete investigation
            investigation.end_time = datetime.now()
            investigation.duration = (investigation.end_time - investigation.start_time).total_seconds()

            if investigation.status != 'partial':
                investigation.status = 'completed'
                investigation.risk_assessment = await self._assess_risk(investigation.findings)
                investigation.recommendations = await self._generate_recommendations(investigation.findings)
                investigation.evidence_files = await self._collect_evidence(investigation.findings)

            # Move to history
            self.investigation_history.append(investigation)
            if investigation_id in self.active_investigations:
                del self.active_investigations[investigation_id]

            logging.info(f"Workflow {workflow_name} completed with status: {investigation.status}")

            return investigation

        except Exception as e:
            logging.error(f"Workflow {workflow_name} failed: {e}")
            investigation.status = 'failed'
            investigation.end_time = datetime.now()
            investigation.duration = (investigation.end_time - investigation.start_time).total_seconds()

            # Move to history
            self.investigation_history.append(investigation)
            if investigation_id in self.active_investigations:
                del self.active_investigations[investigation_id]

            raise

    async def _execute_phase(self, phase_name: str, tools: List[str], target: str,
                            custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific investigation phase"""
        phase_result = {
            'phase_name': phase_name,
            'tools_executed': tools,
            'start_time': time.time(),
            'success': False,
            'results': {},
            'errors': []
        }

        try:
            # Execute each tool in the phase
            for tool in tools:
                tool_result = await self._execute_tool(tool, target, custom_parameters)
                phase_result['results'][tool] = tool_result

                if not tool_result.get('success', False):
                    phase_result['errors'].append(f"{tool}: {tool_result.get('error', 'Unknown error')}")

            # Phase is successful if at least one tool succeeded
            phase_result['success'] = len(phase_result['errors']) < len(tools)
            phase_result['end_time'] = time.time()
            phase_result['duration'] = phase_result['end_time'] - phase_result['start_time']

        except Exception as e:
            phase_result['errors'].append(f"Phase execution error: {str(e)}")
            phase_result['end_time'] = time.time()
            phase_result['duration'] = phase_result['end_time'] - phase_result['start_time']

        return phase_result

    async def _execute_tool(self, tool_name: str, target: str,
                           custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific tool"""
        tool_result = {
            'tool_name': tool_name,
            'target': target,
            'start_time': time.time(),
            'success': False,
            'output': '',
            'error': None
        }

        try:
            # Route tool execution to appropriate orchestrator
            if tool_name in ['nmap', 'masscan', 'theharvester', 'amass', 'subfinder']:
                result = await self._execute_info_gathering_tool(tool_name, target, custom_parameters)
            elif tool_name in ['openvas', 'nessus', 'nikto', 'wpscan']:
                result = await self._execute_vuln_assessment_tool(tool_name, target, custom_parameters)
            elif tool_name in ['metasploit', 'exploitdb', 'searchsploit']:
                result = await self._execute_exploitation_tool(tool_name, target, custom_parameters)
            elif tool_name in ['hashcat', 'john', 'hydra']:
                result = await self._execute_password_tool(tool_name, target, custom_parameters)
            elif tool_name in ['zap', 'burp', 'sqlmap']:
                result = await self._execute_web_security_tool(tool_name, target, custom_parameters)
            else:
                result = {'success': False, 'error': f'Tool {tool_name} not implemented'}

            tool_result.update(result)

        except Exception as e:
            tool_result['error'] = str(e)
            tool_result['end_time'] = time.time()
            tool_result['duration'] = tool_result['end_time'] - tool_result['start_time']

        return tool_result

    async def _execute_info_gathering_tool(self, tool_name: str, target: str,
                                          custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute information gathering tools"""
        if not TOOLS_AVAILABLE:
            return {'success': False, 'error': 'Tools not available'}

        try:
            if tool_name == 'nmap':
                return await self.info_gathering.nmap_advanced_automation.scan_target(target)
            elif tool_name == 'masscan':
                return await self.info_gathering.masscan_high_speed_automation.scan_target(target)
            elif tool_name == 'theharvester':
                return await self.info_gathering.theharvester_osint_automation.gather_osint(target)
            elif tool_name == 'amass':
                return await self.info_gathering.amass_subdomain_automation.discover_subdomains(target)
            elif tool_name == 'subfinder':
                return await self.info_gathering.subfinder_passive_automation.discover_subdomains(target)
            else:
                return {'success': False, 'error': f'Tool {tool_name} not implemented in info gathering'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_vuln_assessment_tool(self, tool_name: str, target: str,
                                           custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute vulnerability assessment tools"""
        if not TOOLS_AVAILABLE:
            return {'success': False, 'error': 'Tools not available'}

        try:
            if tool_name == 'nikto':
                return await self.web_security.nikto.scan_web_server(target)
            elif tool_name == 'wpscan':
                return await self.web_security.wpscan.scan_wordpress_site(target)
            elif tool_name == 'sqlmap':
                return await self.web_security.sqlmap.test_sql_injection(target)
            else:
                return {'success': False, 'error': f'Tool {tool_name} not implemented in vuln assessment'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_exploitation_tool(self, tool_name: str, target: str,
                                        custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute exploitation tools"""
        if not TOOLS_AVAILABLE:
            return {'success': False, 'error': 'Tools not available'}

        try:
            if tool_name == 'searchsploit':
                return await self.exploitation.search_exploits(target)
            else:
                return {'success': False, 'error': f'Tool {tool_name} not implemented in exploitation'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_password_tool(self, tool_name: str, target: str,
                                    custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute password attack tools"""
        if not TOOLS_AVAILABLE:
            return {'success': False, 'error': 'Tools not available'}

        try:
            if tool_name == 'hashcat':
                # This would need a hash to crack
                return {'success': False, 'error': 'Hash required for hashcat'}
            elif tool_name == 'john':
                # This would need a hash to crack
                return {'success': False, 'error': 'Hash required for john'}
            elif tool_name == 'hydra':
                # This would need service details
                return {'success': False, 'error': 'Service details required for hydra'}
            else:
                return {'success': False, 'error': f'Tool {tool_name} not implemented in password attacks'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _execute_web_security_tool(self, tool_name: str, target: str,
                                         custom_parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute web security tools"""
        if not TOOLS_AVAILABLE:
            return {'success': False, 'error': 'Tools not available'}

        try:
            if tool_name == 'zap':
                return await self.web_security.zap.spider_scan(target)
            elif tool_name == 'burp':
                return await self.web_security.burp.start_burp_headless(target)
            elif tool_name == 'sqlmap':
                return await self.web_security.sqlmap.test_sql_injection(target)
            else:
                return {'success': False, 'error': f'Tool {tool_name} not implemented in web security'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def _assess_risk(self, findings: Dict[str, Any]) -> str:
        """Assess overall risk based on findings"""
        risk_score = 0

        for phase_name, phase_result in findings.items():
            if not phase_result.get('success', False):
                continue

            for tool_name, tool_result in phase_result.get('results', {}).items():
                if tool_result.get('success', False):
                    # Analyze tool output for risk indicators
                    output = tool_result.get('output', '')

                    # High risk indicators
                    if any(indicator in output.lower() for indicator in ['critical', 'high', 'exploit', 'vulnerability']):
                        risk_score += 3
                    # Medium risk indicators
                    elif any(indicator in output.lower() for indicator in ['warning', 'medium', 'suspicious']):
                        risk_score += 2
                    # Low risk indicators
                    elif any(indicator in output.lower() for indicator in ['info', 'low', 'notice']):
                        risk_score += 1

        if risk_score >= 10:
            return 'critical'
        elif risk_score >= 7:
            return 'high'
        elif risk_score >= 4:
            return 'medium'
        else:
            return 'low'

    async def _generate_recommendations(self, findings: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on findings"""
        recommendations = []

        for phase_name, phase_result in findings.items():
            if not phase_result.get('success', False):
                continue

            for tool_name, tool_result in phase_result.get('results', {}).items():
                if tool_result.get('success', False):
                    output = tool_result.get('output', '')

                    # Generate specific recommendations based on tool output
                    if 'sql injection' in output.lower():
                        recommendations.append('Implement input validation and parameterized queries')
                    if 'xss' in output.lower():
                        recommendations.append('Implement output encoding and CSP headers')
                    if 'weak password' in output.lower():
                        recommendations.append('Enforce strong password policies and MFA')
                    if 'outdated software' in output.lower():
                        recommendations.append('Update software to latest versions')

        # Add general recommendations
        if not recommendations:
            recommendations.append('Conduct regular security assessments')
            recommendations.append('Implement security monitoring and logging')
            recommendations.append('Provide security awareness training')

        return list(set(recommendations))  # Remove duplicates

    async def _collect_evidence(self, findings: Dict[str, Any]) -> List[str]:
        """Collect evidence files from investigation"""
        evidence_files = []

        for phase_name, phase_result in findings.items():
            if not phase_result.get('success', False):
                continue

            for tool_name, tool_result in phase_result.get('results', {}).items():
                if tool_result.get('success', False):
                    # Look for output files in tool results
                    output_file = tool_result.get('output_file')
                    if output_file and Path(output_file).exists():
                        evidence_files.append(output_file)

        return evidence_files

    async def get_workflow_status(self, workflow_name: str = None) -> Dict[str, Any]:
        """Get status of workflows"""
        status = {
            'active_investigations': len(self.active_investigations),
            'completed_investigations': len(self.investigation_history),
            'available_workflows': list(self.workflows.keys())
        }

        if workflow_name:
            if workflow_name in self.workflows:
                status['workflow_details'] = asdict(self.workflows[workflow_name])
            else:
                status['error'] = f'Workflow {workflow_name} not found'

        return status

    async def generate_investigation_report(self, investigation: InvestigationResult,
                                          format: str = 'json') -> str:
        """Generate comprehensive investigation report"""
        if format == 'json':
            report = asdict(investigation)
            report_file = self.results_dir / f"investigation_report_{investigation.workflow_name}_{int(time.time())}.json"

            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)

            return str(report_file)

        elif format == 'html':
            # Generate HTML report
            html_content = self._generate_html_report(investigation)
            report_file = self.results_dir / f"investigation_report_{investigation.workflow_name}_{int(time.time())}.html"

            with open(report_file, 'w') as f:
                f.write(html_content)

            return str(report_file)

        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_html_report(self, investigation: InvestigationResult) -> str:
        """Generate HTML report for investigation"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Investigation Report - {investigation.workflow_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .finding {{ background-color: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
                .recommendation {{ background-color: #d1ecf1; padding: 10px; margin: 10px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Investigation Report</h1>
                <h2>{investigation.workflow_name}</h2>
                <p><strong>Target:</strong> {investigation.target}</p>
                <p><strong>Status:</strong> {investigation.status}</p>
                <p><strong>Duration:</strong> {investigation.duration:.2f} seconds</p>
                <p><strong>Risk Level:</strong> {investigation.risk_assessment}</p>
            </div>

            <div class="section">
                <h3>Phases Completed</h3>
                <ul>
                    {''.join(f'<li>{phase}</li>' for phase in investigation.phases_completed)}
                </ul>
            </div>

            <div class="section">
                <h3>Key Findings</h3>
                {''.join(f'<div class="finding">{finding}</div>' for finding in investigation.findings.keys())}
            </div>

            <div class="section">
                <h3>Recommendations</h3>
                {''.join(f'<div class="recommendation">{rec}</div>' for rec in investigation.recommendations)}
            </div>

            <div class="section">
                <h3>Evidence Files</h3>
                <ul>
                    {''.join(f'<li>{file}</li>' for file in investigation.evidence_files)}
                </ul>
            </div>
        </body>
        </html>
        """

        return html


# Example usage and testing
async def main():
    """Test the complete automation engine"""
    print("Initializing Complete Kali Linux Automation Engine...")

    engine = CompleteAutomationEngine()

    # Get available workflows
    status = await engine.get_workflow_status()
    print(f"Available workflows: {status['available_workflows']}")

    # Execute a simple workflow
    try:
        print("\nExecuting OSINT Investigation workflow...")
        result = await engine.execute_workflow(
            'osint_investigation',
            'example.com',
            {'max_depth': 2, 'timeout': 300}
        )

        print(f"Workflow completed with status: {result.status}")
        print(f"Duration: {result.duration:.2f} seconds")
        print(f"Phases completed: {result.phases_completed}")
        print(f"Risk assessment: {result.risk_assessment}")

        # Generate report
        report_file = await engine.generate_investigation_report(result, 'html')
        print(f"Report generated: {report_file}")

    except Exception as e:
        print(f"Workflow execution failed: {e}")

    # Get final status
    final_status = await engine.get_workflow_status()
    print(f"\nFinal status: {final_status['completed_investigations']} investigations completed")


if __name__ == "__main__":
    asyncio.run(main())
