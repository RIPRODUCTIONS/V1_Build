#!/usr/bin/env python3
"""
ENHANCED MASTER AUTOMATION ENGINE
Comprehensive automation engine integrating all Kali tools, forensics, and threat intelligence
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class InvestigationType(Enum):
    """Types of investigations supported by the engine"""
    OSINT = "osint"
    PENETRATION_TESTING = "penetration_testing"
    FORENSICS = "forensics"
    MALWARE_ANALYSIS = "malware_analysis"
    THREAT_INTELLIGENCE = "threat_intelligence"
    INCIDENT_RESPONSE = "incident_response"
    COMPLIANCE_AUDIT = "compliance_audit"
    RED_TEAM = "red_team"
    BLUE_TEAM = "blue_team"
    PURPLE_TEAM = "purple_team"


class AutomationLevel(Enum):
    """Automation levels for tool execution"""
    STEALTH = "stealth"      # Minimal footprint, passive only
    MEDIUM = "medium"        # Balanced approach
    HIGH = "high"            # Aggressive, comprehensive
    APT_SIMULATION = "apt_simulation"  # Advanced persistent threat simulation


@dataclass
class InvestigationRequest:
    """Request structure for investigations"""
    investigation_type: InvestigationType
    target: str
    automation_level: AutomationLevel
    options: dict[str, Any]
    priority: str = "medium"
    timeline_hours: int = 24
    budget: float | None = None


@dataclass
class InvestigationResult:
    """Result structure for investigations"""
    investigation_id: str
    status: str
    start_time: datetime
    end_time: datetime | None = None
    results: dict[str, Any] = None
    risk_assessment: dict[str, Any] = None
    recommendations: list[str] = None
    artifacts: list[str] = None
    execution_time: float = 0.0


class EnhancedMasterAutomationEngine:
    """Enhanced Master Automation Engine for comprehensive cybersecurity investigations"""

    def __init__(self):
        self.tool_registry = {}
        self.workflow_templates = {}
        self.investigation_history = []
        self.active_investigations = {}
        self.intelligence_correlator = IntelligenceCorrelator()
        self.risk_assessor = RiskAssessor()
        self.report_generator = ReportGenerator()

        # Initialize tool categories
        self._initialize_tool_categories()
        self._load_workflow_templates()

    def _initialize_tool_categories(self):
        """Initialize all tool categories"""
        # Information Gathering Tools
        self.tool_registry['information_gathering'] = {
            'nmap': 'NmapAdvancedAutomation',
            'masscan': 'MasscanHighSpeedAutomation',
            'theharvester': 'TheHarvesterOSINTAutomation',
            'amass': 'AmassSubdomainAutomation',
            'subfinder': 'SubfinderPassiveAutomation',
            'spiderfoot': 'SpiderfootOSINTAutomation',
            'maltego': 'MaltegoOSINTAutomation',
            'recon-ng': 'ReconNgFrameworkAutomation',
            'whatsmyname': 'WhatsMyNameAutomation',
            'maigret': 'MaigretUsernameAutomation',
            'holehe': 'HoleheEmailAutomation',
            'shodan': 'ShodanSearchAutomation',
            'hibp': 'HaveIBeenPwnedAutomation'
        }

        # Penetration Testing Tools
        self.tool_registry['penetration_testing'] = {
            'metasploit': 'MetasploitFrameworkAutomation',
            'burpsuite': 'BurpSuiteAutomation',
            'zap': 'OWASPZAPAutomation',
            'sqlmap': 'SQLMapAutomation',
            'hydra': 'HydraAutomation',
            'john': 'JohnTheRipperAutomation',
            'hashcat': 'HashcatAutomation',
            'aircrack': 'AircrackAutomation'
        }

        # Forensics Tools
        self.tool_registry['forensics'] = {
            'volatility': 'VolatilityAutomation',
            'tsk': 'TheSleuthKitAutomation',
            'autopsy': 'AutopsyAutomation',
            'wireshark': 'WiresharkAutomation',
            'foremost': 'ForemostAutomation',
            'photorec': 'PhotoRecAutomation',
            'bulk_extractor': 'BulkExtractorAutomation'
        }

        # Threat Intelligence Tools
        self.tool_registry['threat_intelligence'] = {
            'misp': 'MISPConnector',
            'virustotal': 'VirusTotalConnector',
            'otx': 'AlienVaultOTXConnector',
            'threatcrowd': 'ThreatCrowdConnector',
            'abuseipdb': 'AbuseIPDBConnector',
            'greynoise': 'GreyNoiseConnector'
        }

        # Malware Analysis Tools
        self.tool_registry['malware_analysis'] = {
            'pefile': 'PEFileAnalyzer',
            'yara': 'YaraScanner',
            'capa': 'CapaAnalyzer',
            'peid': 'PEiDAnalyzer',
            'strings': 'StringsExtractor',
            'binwalk': 'BinwalkAnalyzer'
        }

    def _load_workflow_templates(self):
        """Load predefined workflow templates"""
        self.workflow_templates = {
            InvestigationType.OSINT: self._create_osint_workflow(),
            InvestigationType.PENETRATION_TESTING: self._create_pentest_workflow(),
            InvestigationType.FORENSICS: self._create_forensics_workflow(),
            InvestigationType.MALWARE_ANALYSIS: self._create_malware_workflow(),
            InvestigationType.THREAT_INTELLIGENCE: self._create_threat_intel_workflow(),
            InvestigationType.INCIDENT_RESPONSE: self._create_incident_response_workflow(),
            InvestigationType.COMPLIANCE_AUDIT: self._create_compliance_workflow(),
            InvestigationType.RED_TEAM: self._create_red_team_workflow(),
            InvestigationType.BLUE_TEAM: self._create_blue_team_workflow(),
            InvestigationType.PURPLE_TEAM: self._create_purple_team_workflow()
        }

    async def execute_comprehensive_investigation(self, request: InvestigationRequest) -> InvestigationResult:
        """Execute a comprehensive investigation based on the request"""

        investigation_id = f"inv_{int(time.time())}_{request.investigation_type.value}"
        start_time = datetime.now(UTC)

        # Create investigation result
        result = InvestigationResult(
            investigation_id=investigation_id,
            status="running",
            start_time=start_time,
            results={},
            risk_assessment={},
            recommendations=[],
            artifacts=[]
        )

        try:
            # Get workflow template
            workflow = self.workflow_templates.get(request.investigation_type)
            if not workflow:
                raise ValueError(f"No workflow template found for {request.investigation_type}")

            # Execute workflow phases
            workflow_results = await self._execute_workflow_phases(workflow, request)

            # Correlate all data
            correlated_data = await self.intelligence_correlator.correlate_all_data(workflow_results)

            # Generate risk assessment
            risk_assessment = await self.risk_assessor.assess_comprehensive_risk(
                request.target, correlated_data, request.automation_level
            )

            # Generate recommendations
            recommendations = await self.risk_assessor.generate_recommendations(
                risk_assessment, correlated_data
            )

            # Generate comprehensive report
            report = await self.report_generator.generate_comprehensive_report(
                investigation_id, request, workflow_results, correlated_data,
                risk_assessment, recommendations
            )

            # Update result
            result.status = "completed"
            result.end_time = datetime.now(UTC)
            result.results = workflow_results
            result.risk_assessment = risk_assessment
            result.recommendations = recommendations
            result.artifacts = [report]
            result.execution_time = (result.end_time - result.start_time).total_seconds()

            # Store in history
            self.investigation_history.append(result)

            logger.info(f"Investigation {investigation_id} completed successfully")

        except Exception as e:
            result.status = "failed"
            result.end_time = datetime.now(UTC)
            logger.error(f"Investigation {investigation_id} failed: {e}")
            raise

        return result

    async def _execute_workflow_phases(self, workflow: dict[str, Any], request: InvestigationRequest) -> dict[str, Any]:
        """Execute workflow phases in parallel where possible"""
        workflow_results = {}

        # Execute phases based on automation level
        if request.automation_level == AutomationLevel.STEALTH:
            # Sequential execution for stealth
            for phase_name, phase_config in workflow['phases'].items():
                phase_result = await self._execute_phase(phase_name, phase_config, request)
                workflow_results[phase_name] = phase_result
        else:
            # Parallel execution for medium/high automation
            phase_tasks = []
            for phase_name, phase_config in workflow['phases'].items():
                task = asyncio.create_task(
                    self._execute_phase(phase_name, phase_config, request)
                )
                phase_tasks.append((phase_name, task))

            # Wait for all phases to complete
            for phase_name, task in phase_tasks:
                try:
                    phase_result = await task
                    workflow_results[phase_name] = phase_result
                except Exception as e:
                    logger.error(f"Phase {phase_name} failed: {e}")
                    workflow_results[phase_name] = {'error': str(e)}

        return workflow_results

    async def _execute_phase(self, phase_name: str, phase_config: dict[str, Any],
                           request: InvestigationRequest) -> dict[str, Any]:
        """Execute a single workflow phase"""
        phase_results = {
            'phase_name': phase_name,
            'start_time': datetime.now(UTC).isoformat(),
            'tools_executed': [],
            'results': {},
            'errors': []
        }

        try:
            # Execute tools in the phase
            for tool_name, tool_config in phase_config.get('tools', {}).items():
                try:
                    tool_result = await self._execute_tool(tool_name, tool_config, request)
                    phase_results['tools_executed'].append(tool_name)
                    phase_results['results'][tool_name] = tool_result
                except Exception as e:
                    error_msg = f"Tool {tool_name} failed: {e}"
                    phase_results['errors'].append(error_msg)
                    logger.warning(error_msg)

            phase_results['end_time'] = datetime.now(UTC).isoformat()

        except Exception as e:
            phase_results['errors'].append(f"Phase {phase_name} failed: {e}")
            logger.error(f"Phase {phase_name} failed: {e}")

        return phase_results

    async def _execute_tool(self, tool_name: str, tool_config: dict[str, Any],
                          request: InvestigationRequest) -> dict[str, Any]:
        """Execute a single tool"""
        # This would instantiate and execute the actual tool class
        # For now, return mock results
        return {
            'tool_name': tool_name,
            'target': request.target,
            'automation_level': request.automation_level.value,
            'execution_time': 0.0,
            'status': 'completed',
            'results': f"Mock results for {tool_name}"
        }

    def _create_osint_workflow(self) -> dict[str, Any]:
        """Create OSINT investigation workflow"""
        return {
            'name': 'OSINT Investigation',
            'description': 'Comprehensive open source intelligence gathering',
            'phases': {
                'reconnaissance': {
                    'description': 'Initial reconnaissance and target identification',
                    'tools': {
                        'nmap': {'scan_type': 'stealth'},
                        'theharvester': {'sources': 'all'},
                        'amass': {'subdomain_enumeration': True}
                    }
                },
                'social_media': {
                    'description': 'Social media intelligence gathering',
                    'tools': {
                        'whatsmyname': {'platforms': 'all'},
                        'maigret': {'sites': 'top_100'},
                        'holehe': {'email_check': True}
                    }
                },
                'threat_intelligence': {
                    'description': 'Threat intelligence correlation',
                    'tools': {
                        'misp': {'query_type': 'comprehensive'},
                        'virustotal': {'scan_type': 'full'},
                        'otx': {'pulse_search': True}
                    }
                }
            }
        }

    def _create_pentest_workflow(self) -> dict[str, Any]:
        """Create penetration testing workflow"""
        return {
            'name': 'Penetration Testing',
            'description': 'Comprehensive penetration testing engagement',
            'phases': {
                'reconnaissance': {
                    'description': 'Passive and active reconnaissance',
                    'tools': {
                        'nmap': {'scan_type': 'comprehensive'},
                        'masscan': {'ports': 'all'},
                        'spiderfoot': {'modules': 'all'}
                    }
                },
                'vulnerability_assessment': {
                    'description': 'Vulnerability identification and assessment',
                    'tools': {
                        'burpsuite': {'scan_type': 'active'},
                        'zap': {'scan_policy': 'high'},
                        'sqlmap': {'level': 'high'}
                    }
                },
                'exploitation': {
                    'description': 'Controlled exploitation of vulnerabilities',
                    'tools': {
                        'metasploit': {'exploit_selection': 'intelligent'},
                        'hydra': {'wordlists': 'comprehensive'}
                    }
                },
                'post_exploitation': {
                    'description': 'Post-exploitation activities and persistence',
                    'tools': {
                        'metasploit': {'post_modules': 'all'},
                        'volatility': {'memory_analysis': True}
                    }
                }
            }
        }

    def _create_forensics_workflow(self) -> dict[str, Any]:
        """Create digital forensics workflow"""
        return {
            'name': 'Digital Forensics',
            'description': 'Comprehensive digital forensics investigation',
            'phases': {
                'acquisition': {
                    'description': 'Evidence acquisition and preservation',
                    'tools': {
                        'dd': {'block_size': 'optimal'},
                        'dc3dd': {'verification': True}
                    }
                },
                'analysis': {
                    'description': 'Evidence analysis and examination',
                    'tools': {
                        'volatility': {'plugins': 'all'},
                        'tsk': {'analysis_type': 'comprehensive'},
                        'autopsy': {'modules': 'all'}
                    }
                },
                'recovery': {
                    'description': 'Data recovery and carving',
                    'tools': {
                        'foremost': {'file_types': 'all'},
                        'photorec': {'recovery_mode': 'comprehensive'},
                        'bulk_extractor': {'extractors': 'all'}
                    }
                },
                'timeline': {
                    'description': 'Timeline analysis and correlation',
                    'tools': {
                        'log2timeline': {'sources': 'all'},
                        'plaso': {'analysis': 'comprehensive'}
                    }
                }
            }
        }

    def _create_malware_workflow(self) -> dict[str, Any]:
        """Create malware analysis workflow"""
        return {
            'name': 'Malware Analysis',
            'description': 'Comprehensive malware analysis and classification',
            'phases': {
                'static_analysis': {
                    'description': 'Static analysis of malware samples',
                    'tools': {
                        'pefile': {'analysis_type': 'comprehensive'},
                        'yara': {'rules': 'all'},
                        'strings': {'encoding': 'all'}
                    }
                },
                'dynamic_analysis': {
                    'description': 'Dynamic analysis in controlled environment',
                    'tools': {
                        'cuckoo': {'analysis_time': 'extended'},
                        'volatility': {'memory_analysis': True}
                    }
                },
                'classification': {
                    'description': 'Malware family classification and attribution',
                    'tools': {
                        'capa': {'capabilities': 'all'},
                        'peid': {'signatures': 'comprehensive'}
                    }
                }
            }
        }

    def _create_threat_intel_workflow(self) -> dict[str, Any]:
        """Create threat intelligence workflow"""
        return {
            'name': 'Threat Intelligence',
            'description': 'Comprehensive threat intelligence gathering and analysis',
            'phases': {
                'collection': {
                    'description': 'Threat intelligence collection',
                    'tools': {
                        'misp': {'feeds': 'all'},
                        'otx': {'pulses': 'recent'},
                        'virustotal': {'scan_type': 'comprehensive'}
                    }
                },
                'correlation': {
                    'description': 'Intelligence correlation and analysis',
                    'tools': {
                        'misp': {'correlation': True},
                        'otx': {'indicators': 'related'}
                    }
                },
                'reporting': {
                    'description': 'Intelligence reporting and dissemination',
                    'tools': {
                        'report_generator': {'format': 'comprehensive'},
                        'stix_taxii': {'sharing': True}
                    }
                }
            }
        }

    def _create_incident_response_workflow(self) -> dict[str, Any]:
        """Create incident response workflow"""
        return {
            'name': 'Incident Response',
            'description': 'Comprehensive incident response and handling',
            'phases': {
                'detection': {
                    'description': 'Incident detection and triage',
                    'tools': {
                        'siem': {'alerts': 'all'},
                        'edr': {'endpoint_analysis': True}
                    }
                },
                'containment': {
                    'description': 'Incident containment and isolation',
                    'tools': {
                        'firewall': {'rules': 'emergency'},
                        'ids': {'signatures': 'updated'}
                    }
                },
                'eradication': {
                    'description': 'Threat eradication and cleanup',
                    'tools': {
                        'antivirus': {'scan_type': 'full'},
                        'malware_removal': {'tools': 'all'}
                    }
                },
                'recovery': {
                    'description': 'System recovery and restoration',
                    'tools': {
                        'backup_restore': {'verification': True},
                        'system_validation': {'checks': 'all'}
                    }
                }
            }
        }

    def _create_compliance_workflow(self) -> dict[str, Any]:
        """Create compliance audit workflow"""
        return {
            'name': 'Compliance Audit',
            'description': 'Comprehensive compliance and regulatory audit',
            'phases': {
                'assessment': {
                    'description': 'Compliance assessment and gap analysis',
                    'tools': {
                        'nmap': {'scan_type': 'compliance'},
                        'nessus': {'policies': 'compliance'}
                    }
                },
                'documentation': {
                    'description': 'Policy and procedure documentation review',
                    'tools': {
                        'document_analyzer': {'standards': 'all'},
                        'policy_checker': {'frameworks': 'all'}
                    }
                },
                'testing': {
                    'description': 'Compliance testing and validation',
                    'tools': {
                        'penetration_testing': {'scope': 'compliance'},
                        'vulnerability_assessment': {'frameworks': 'all'}
                    }
                }
            }
        }

    def _create_red_team_workflow(self) -> dict[str, Any]:
        """Create red team workflow"""
        return {
            'name': 'Red Team',
            'description': 'Comprehensive red team engagement',
            'phases': {
                'planning': {
                    'description': 'Engagement planning and scope definition',
                    'tools': {
                        'project_management': {'planning': True},
                        'scope_definition': {'boundaries': 'clear'}
                    }
                },
                'execution': {
                    'description': 'Red team execution and attack simulation',
                    'tools': {
                        'metasploit': {'exploits': 'advanced'},
                        'custom_tools': {'development': True}
                    }
                },
                'reporting': {
                    'description': 'Comprehensive reporting and debriefing',
                    'tools': {
                        'report_generator': {'format': 'executive'},
                        'presentation_tools': {'templates': 'professional'}
                    }
                }
            }
        }

    def _create_blue_team_workflow(self) -> dict[str, Any]:
        """Create blue team workflow"""
        return {
            'name': 'Blue Team',
            'description': 'Comprehensive blue team defense and monitoring',
            'phases': {
                'monitoring': {
                    'description': 'Continuous monitoring and detection',
                    'tools': {
                        'siem': {'monitoring': '24x7'},
                        'edr': {'endpoint_monitoring': True}
                    }
                },
                'response': {
                    'description': 'Incident response and handling',
                    'tools': {
                        'playbooks': {'automation': True},
                        'forensics': {'tools': 'all'}
                    }
                },
                'improvement': {
                    'description': 'Process improvement and lessons learned',
                    'tools': {
                        'metrics_analysis': {'kpis': 'all'},
                        'process_improvement': {'methodology': 'agile'}
                    }
                }
            }
        }

    def _create_purple_team_workflow(self) -> dict[str, Any]:
        """Create purple team workflow"""
        return {
            'name': 'Purple Team',
            'description': 'Collaborative red and blue team engagement',
            'phases': {
                'collaboration': {
                    'description': 'Red and blue team collaboration',
                    'tools': {
                        'communication': {'channels': 'all'},
                        'knowledge_sharing': {'platforms': 'secure'}
                    }
                },
                'testing': {
                    'description': 'Collaborative testing and validation',
                    'tools': {
                        'red_team_tools': {'scope': 'collaborative'},
                        'blue_team_tools': {'integration': True}
                    }
                },
                'improvement': {
                    'description': 'Joint process improvement',
                    'tools': {
                        'lessons_learned': {'documentation': True},
                        'process_refinement': {'methodology': 'collaborative'}
                    }
                }
            }
        }


class IntelligenceCorrelator:
    """Intelligent correlation engine for threat intelligence and findings"""

    async def correlate_all_data(self, workflow_results: dict[str, Any]) -> dict[str, Any]:
        """Correlate all data from workflow execution"""
        correlated_data = {
            'threat_indicators': [],
            'attack_patterns': [],
            'timeline_events': [],
            'risk_indicators': [],
            'correlation_score': 0.0
        }

        # Extract and correlate threat indicators
        for phase_name, phase_result in workflow_results.items():
            if 'results' in phase_result:
                for tool_name, tool_result in phase_result['results'].items():
                    indicators = self._extract_threat_indicators(tool_result)
                    correlated_data['threat_indicators'].extend(indicators)

        # Calculate correlation score
        correlated_data['correlation_score'] = self._calculate_correlation_score(correlated_data)

        return correlated_data

    def _extract_threat_indicators(self, tool_result: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract threat indicators from tool results"""
        indicators = []

        # This would implement sophisticated indicator extraction
        # For now, return basic structure
        if 'results' in tool_result:
            indicators.append({
                'source': tool_result.get('tool_name', 'unknown'),
                'indicator_type': 'unknown',
                'value': str(tool_result.get('results', '')),
                'confidence': 0.5
            })

        return indicators

    def _calculate_correlation_score(self, correlated_data: dict[str, Any]) -> float:
        """Calculate overall correlation score"""
        # Simple scoring algorithm
        base_score = len(correlated_data.get('threat_indicators', [])) * 0.1
        return min(base_score, 1.0)


class RiskAssessor:
    """Comprehensive risk assessment engine"""

    async def assess_comprehensive_risk(self, target: str, correlated_data: dict[str, Any],
                                      automation_level: AutomationLevel) -> dict[str, Any]:
        """Assess comprehensive risk based on all findings"""
        risk_assessment = {
            'overall_risk_score': 0.0,
            'risk_level': 'low',
            'risk_factors': [],
            'mitigation_controls': [],
            'compliance_impact': 'low'
        }

        # Calculate risk score based on threat indicators
        threat_indicators = correlated_data.get('threat_indicators', [])
        risk_score = len(threat_indicators) * 0.1

        # Adjust for automation level
        if automation_level == AutomationLevel.APT_SIMULATION:
            risk_score *= 1.5

        risk_assessment['overall_risk_score'] = min(risk_score, 1.0)

        # Determine risk level
        if risk_assessment['overall_risk_score'] >= 0.7:
            risk_assessment['risk_level'] = 'high'
        elif risk_assessment['overall_risk_score'] >= 0.4:
            risk_assessment['risk_level'] = 'medium'

        return risk_assessment

    async def generate_recommendations(self, risk_assessment: dict[str, Any],
                                    correlated_data: dict[str, Any]) -> list[str]:
        """Generate actionable recommendations based on risk assessment"""
        recommendations = []

        risk_level = risk_assessment.get('risk_level', 'low')

        if risk_level == 'high':
            recommendations.extend([
                'Implement immediate containment measures',
                'Activate incident response procedures',
                'Notify senior management and stakeholders',
                'Engage external security consultants if needed'
            ])
        elif risk_level == 'medium':
            recommendations.extend([
                'Implement enhanced monitoring',
                'Review and update security policies',
                'Conduct additional security assessments',
                'Provide security awareness training'
            ])
        else:
            recommendations.extend([
                'Continue routine monitoring',
                'Document findings for future reference',
                'Consider periodic reassessment'
            ])

        return recommendations


class ReportGenerator:
    """Comprehensive report generation engine"""

    async def generate_comprehensive_report(self, investigation_id: str, request: InvestigationRequest,
                                         workflow_results: dict[str, Any], correlated_data: dict[str, Any],
                                         risk_assessment: dict[str, Any],
                                         recommendations: list[str]) -> str:
        """Generate comprehensive investigation report"""

        report = {
            'investigation_id': investigation_id,
            'executive_summary': {
                'target': request.target,
                'investigation_type': request.investigation_type.value,
                'automation_level': request.automation_level.value,
                'overall_risk_score': risk_assessment.get('overall_risk_score', 0.0),
                'risk_level': risk_assessment.get('risk_level', 'low')
            },
            'methodology': {
                'workflow_used': self._get_workflow_name(request.investigation_type),
                'tools_executed': self._extract_tools_executed(workflow_results),
                'execution_parameters': {
                    'automation_level': request.automation_level.value,
                    'timeline_hours': request.timeline_hours,
                    'priority': request.priority
                }
            },
            'findings': {
                'workflow_results': workflow_results,
                'correlated_data': correlated_data,
                'threat_indicators': correlated_data.get('threat_indicators', [])
            },
            'risk_assessment': risk_assessment,
            'recommendations': recommendations,
            'appendix': {
                'raw_data': workflow_results,
                'correlation_details': correlated_data,
                'timestamps': {
                    'investigation_start': request.start_time.isoformat() if hasattr(request, 'start_time') else None,
                    'report_generated': datetime.now(UTC).isoformat()
                }
            }
        }

        # Save report to file
        report_path = f"/opt/kali-automation/reports/{investigation_id}_comprehensive_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        return report_path

    def _get_workflow_name(self, investigation_type: InvestigationType) -> str:
        """Get workflow name for investigation type"""
        workflow_names = {
            InvestigationType.OSINT: "OSINT Investigation Workflow",
            InvestigationType.PENETRATION_TESTING: "Penetration Testing Workflow",
            InvestigationType.FORENSICS: "Digital Forensics Workflow",
            InvestigationType.MALWARE_ANALYSIS: "Malware Analysis Workflow",
            InvestigationType.THREAT_INTELLIGENCE: "Threat Intelligence Workflow",
            InvestigationType.INCIDENT_RESPONSE: "Incident Response Workflow",
            InvestigationType.COMPLIANCE_AUDIT: "Compliance Audit Workflow",
            InvestigationType.RED_TEAM: "Red Team Workflow",
            InvestigationType.BLUE_TEAM: "Blue Team Workflow",
            InvestigationType.PURPLE_TEAM: "Purple Team Workflow"
        }
        return workflow_names.get(investigation_type, "Unknown Workflow")

    def _extract_tools_executed(self, workflow_results: dict[str, Any]) -> list[str]:
        """Extract list of tools executed during investigation"""
        tools = []
        for phase_name, phase_result in workflow_results.items():
            if 'tools_executed' in phase_result:
                tools.extend(phase_result['tools_executed'])
        return list(set(tools))  # Remove duplicates
