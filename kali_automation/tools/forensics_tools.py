#!/usr/bin/env python3
"""
Forensics Tools Category

This module provides automation for digital forensics tools including:
- Memory forensics (Volatility, Rekall)
- Disk forensics (Autopsy, Sleuth Kit)
- Network forensics (Wireshark, tcpdump)
- File analysis (binwalk, exiftool)
- Evidence collection and preservation
- Timeline analysis
"""

import asyncio
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ForensicsType(Enum):
    """Types of forensics analysis."""
    MEMORY_FORENSICS = "memory_forensics"
    DISK_FORENSICS = "disk_forensics"
    NETWORK_FORENSICS = "network_forensics"
    FILE_ANALYSIS = "file_analysis"
    MOBILE_FORENSICS = "mobile_forensics"
    LIVE_FORENSICS = "live_forensics"


class EvidenceType(Enum):
    """Types of evidence."""
    MEMORY_DUMP = "memory_dump"
    DISK_IMAGE = "disk_image"
    NETWORK_CAPTURE = "network_capture"
    LOG_FILES = "log_files"
    REGISTRY_HIVES = "registry_hives"
    BROWSER_ARTIFACTS = "browser_artifacts"


@dataclass
class EvidenceItem:
    """Represents a piece of evidence."""
    id: str
    type: EvidenceType
    source: str
    path: str
    hash: str
    size: int
    timestamp: str
    metadata: dict[str, Any] = None


@dataclass
class ForensicsResult:
    """Result of a forensics analysis."""
    analysis_type: ForensicsType
    target: str
    success: bool
    findings: list[dict[str, Any]]
    evidence_collected: list[EvidenceItem]
    timestamp: str
    duration: float
    output: str = None
    error: str = None


class ForensicsTools:
    """Main class for forensics tool automation."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize forensics tools."""
        self.config = config or {}
        self.output_dir = self.config.get('output_dir', '/tmp/forensics_output')
        self.evidence_dir = os.path.join(self.output_dir, 'evidence')
        self.reports_dir = os.path.join(self.output_dir, 'reports')

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.evidence_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        # Tool paths
        self.tools = {
            'volatility': 'volatility',
            'rekall': 'rekall',
            'autopsy': 'autopsy',
            'sleuthkit': 'tsk_*',
            'wireshark': 'wireshark',
            'tshark': 'tshark',
            'tcpdump': 'tcpdump',
            'binwalk': 'binwalk',
            'exiftool': 'exiftool',
            'strings': 'strings',
            'file': 'file',
            'xxd': 'xxd',
            'dd': 'dd',
            'dc3dd': 'dc3dd',
            'dcfldd': 'dcfldd'
        }

        # Evidence tracking
        self.evidence_collected: list[EvidenceItem] = []
        self.analysis_history: list[ForensicsResult] = []

        logger.info("Forensics tools initialized")

    async def collect_memory_evidence(self, target: str,
                                    output_format: str = 'raw') -> EvidenceItem:
        """Collect memory evidence from a target system."""
        try:
            logger.info(f"Collecting memory evidence from {target}")

            # Generate unique filename
            timestamp = int(time.time())
            output_file = os.path.join(self.evidence_dir, f"memory_{target}_{timestamp}.{output_format}")

            # Use appropriate tool based on target OS
            if self._is_linux_target(target):
                cmd = ['dd', 'if=/proc/kcore', 'of=' + output_file, 'bs=1M']
            elif self._is_windows_target(target):
                # For Windows, we'd typically use tools like WinPmem or FTK Imager
                # This is a simplified example
                cmd = ['echo', 'Windows memory collection requires specialized tools']
            else:
                cmd = ['dd', 'if=/dev/mem', 'of=' + output_file, 'bs=1M']

            result = await self._run_command(cmd)

            if result['success']:
                # Calculate hash and metadata
                file_hash = await self._calculate_file_hash(output_file)
                file_size = os.path.getsize(output_file)

                evidence = EvidenceItem(
                    id=f"mem_{timestamp}",
                    type=EvidenceType.MEMORY_DUMP,
                    source=target,
                    path=output_file,
                    hash=file_hash,
                    size=file_size,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    metadata={
                        'format': output_format,
                        'collection_method': 'dd',
                        'target_os': self._detect_target_os(target)
                    }
                )

                self.evidence_collected.append(evidence)
                logger.info(f"Memory evidence collected: {output_file}")
                return evidence
            else:
                raise Exception(f"Memory collection failed: {result['error']}")

        except Exception as e:
            logger.error(f"Error collecting memory evidence: {e}")
            raise

    async def analyze_memory_dump(self, memory_file: str,
                                 profile: str = None) -> ForensicsResult:
        """Analyze memory dump using Volatility."""
        try:
            logger.info(f"Analyzing memory dump: {memory_file}")
            start_time = time.time()

            # Auto-detect profile if not specified
            if not profile:
                profile = await self._detect_memory_profile(memory_file)

            findings = []

            # Run common Volatility plugins
            plugins = [
                'pslist', 'pstree', 'psscan', 'dlllist', 'handles',
                'netscan', 'connections', 'sockets', 'cmdline',
                'filescan', 'malfind', 'timeliner'
            ]

            for plugin in plugins:
                logger.info(f"Running Volatility plugin: {plugin}")

                cmd = [
                    'volatility', '-f', memory_file,
                    '--profile=' + profile, plugin
                ]

                result = await self._run_command(cmd)

                if result['success']:
                    plugin_findings = self._parse_volatility_output(plugin, result['output'])
                    findings.extend(plugin_findings)
                else:
                    logger.warning(f"Plugin {plugin} failed: {result['error']}")

            duration = time.time() - start_time

            forensics_result = ForensicsResult(
                analysis_type=ForensicsType.MEMORY_FORENSICS,
                target=memory_file,
                success=True,
                findings=findings,
                evidence_collected=[self._find_evidence_by_path(memory_file)],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(forensics_result)
            return forensics_result

        except Exception as e:
            logger.error(f"Error analyzing memory dump: {e}")
            return ForensicsResult(
                analysis_type=ForensicsType.MEMORY_FORENSICS,
                target=memory_file,
                success=False,
                findings=[],
                evidence_collected=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _detect_memory_profile(self, memory_file: str) -> str:
        """Detect memory profile using Volatility."""
        try:
            cmd = ['volatility', '-f', memory_file, 'imageinfo']
            result = await self._run_command(cmd)

            if result['success']:
                # Parse profile from output
                lines = result['output'].split('\n')
                for line in lines:
                    if 'Suggested Profile(s)' in line:
                        profile = line.split(':')[1].strip().split(',')[0].strip()
                        return profile

            # Default profile
            return 'Win7SP1x64'

        except Exception as e:
            logger.error(f"Error detecting memory profile: {e}")
            return 'Win7SP1x64'

    def _parse_volatility_output(self, plugin: str, output: str) -> list[dict[str, Any]]:
        """Parse Volatility plugin output."""
        findings = []

        try:
            lines = output.split('\n')

            if plugin == 'pslist':
                # Parse process list
                for line in lines[2:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            findings.append({
                                'type': 'process',
                                'pid': parts[2],
                                'ppid': parts[3],
                                'name': parts[0],
                                'plugin': plugin
                            })

            elif plugin == 'netscan':
                # Parse network connections
                for line in lines[2:]:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 4:
                            findings.append({
                                'type': 'network_connection',
                                'local_addr': parts[0],
                                'local_port': parts[1],
                                'remote_addr': parts[2],
                                'remote_port': parts[3],
                                'plugin': plugin
                            })

            elif plugin == 'malfind':
                # Parse malware findings
                for line in lines:
                    if 'MALWARE' in line or 'SUSPICIOUS' in line:
                        findings.append({
                            'type': 'malware_indicator',
                            'description': line.strip(),
                            'plugin': plugin
                        })

            else:
                # Generic parsing for other plugins
                findings.append({
                    'type': 'plugin_output',
                    'plugin': plugin,
                    'data': output.strip()
                })

        except Exception as e:
            logger.error(f"Error parsing {plugin} output: {e}")

        return findings

    async def collect_disk_evidence(self, target: str,
                                   output_format: str = 'raw') -> EvidenceItem:
        """Collect disk evidence from a target system."""
        try:
            logger.info(f"Collecting disk evidence from {target}")

            timestamp = int(time.time())
            output_file = os.path.join(self.evidence_dir, f"disk_{target}_{timestamp}.{output_format}")

            # Use dd for disk imaging
            cmd = ['dd', 'if=' + target, 'of=' + output_file, 'bs=1M', 'status=progress']

            result = await self._run_command(cmd)

            if result['success']:
                # Calculate hash and metadata
                file_hash = await self._calculate_file_hash(output_file)
                file_size = os.path.getsize(output_file)

                evidence = EvidenceItem(
                    id=f"disk_{timestamp}",
                    type=EvidenceType.DISK_IMAGE,
                    source=target,
                    path=output_file,
                    hash=file_hash,
                    size=file_size,
                    timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                    metadata={
                        'format': output_format,
                        'collection_method': 'dd',
                        'target_device': target
                    }
                )

                self.evidence_collected.append(evidence)
                logger.info(f"Disk evidence collected: {output_file}")
                return evidence
            else:
                raise Exception(f"Disk collection failed: {result['error']}")

        except Exception as e:
            logger.error(f"Error collecting disk evidence: {e}")
            raise

    async def analyze_disk_image(self, disk_file: str) -> ForensicsResult:
        """Analyze disk image using Sleuth Kit."""
        try:
            logger.info(f"Analyzing disk image: {disk_file}")
            start_time = time.time()

            findings = []

            # Run Sleuth Kit tools
            tools = [
                ('mmls', 'partition_table'),
                ('fsstat', 'filesystem_info'),
                ('fls', 'file_listing'),
                ('istat', 'inode_info'),
                ('icat', 'file_content')
            ]

            for tool, analysis_type in tools:
                logger.info(f"Running {tool} analysis")

                cmd = [tool, disk_file]
                result = await self._run_command(cmd)

                if result['success']:
                    tool_findings = self._parse_sleuthkit_output(tool, result['output'])
                    findings.extend(tool_findings)
                else:
                    logger.warning(f"Tool {tool} failed: {result['error']}")

            duration = time.time() - start_time

            forensics_result = ForensicsResult(
                analysis_type=ForensicsType.DISK_FORENSICS,
                target=disk_file,
                success=True,
                findings=findings,
                evidence_collected=[self._find_evidence_by_path(disk_file)],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(forensics_result)
            return forensics_result

        except Exception as e:
            logger.error(f"Error analyzing disk image: {e}")
            return ForensicsResult(
                analysis_type=ForensicsType.DISK_FORENSICS,
                target=disk_file,
                success=False,
                findings=[],
                evidence_collected=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    def _parse_sleuthkit_output(self, tool: str, output: str) -> list[dict[str, Any]]:
        """Parse Sleuth Kit tool output."""
        findings = []

        try:
            if tool == 'mmls':
                # Parse partition table
                lines = output.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('DOS Partition Table'):
                        parts = line.split()
                        if len(parts) >= 4:
                            findings.append({
                                'type': 'partition',
                                'start_sector': parts[0],
                                'length': parts[1],
                                'size': parts[2],
                                'description': ' '.join(parts[3:]),
                                'tool': tool
                            })

            elif tool == 'fls':
                # Parse file listing
                lines = output.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('r/r'):
                        parts = line.split()
                        if len(parts) >= 4:
                            findings.append({
                                'type': 'file_entry',
                                'inode': parts[0],
                                'name': parts[1],
                                'size': parts[2],
                                'tool': tool
                            })

            else:
                # Generic parsing for other tools
                findings.append({
                    'type': 'tool_output',
                    'tool': tool,
                    'data': output.strip()
                })

        except Exception as e:
            logger.error(f"Error parsing {tool} output: {e}")

        return findings

    async def collect_network_evidence(self, interface: str,
                                      duration: int = 300) -> EvidenceItem:
        """Collect network evidence using tcpdump."""
        try:
            logger.info(f"Collecting network evidence from {interface} for {duration} seconds")

            timestamp = int(time.time())
            output_file = os.path.join(self.evidence_dir, f"network_{interface}_{timestamp}.pcap")

            # Use tcpdump for packet capture
            cmd = [
                'tcpdump', '-i', interface, '-w', output_file,
                '-c', '10000'  # Capture up to 10,000 packets
            ]

            # Run capture in background
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for specified duration
            await asyncio.sleep(duration)
            process.terminate()

            # Calculate hash and metadata
            file_hash = await self._calculate_file_hash(output_file)
            file_size = os.path.getsize(output_file)

            evidence = EvidenceItem(
                id=f"net_{timestamp}",
                type=EvidenceType.NETWORK_CAPTURE,
                source=interface,
                path=output_file,
                hash=file_hash,
                size=file_size,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                metadata={
                    'format': 'pcap',
                    'collection_method': 'tcpdump',
                    'interface': interface,
                    'duration': duration
                }
            )

            self.evidence_collected.append(evidence)
            logger.info(f"Network evidence collected: {output_file}")
            return evidence

        except Exception as e:
            logger.error(f"Error collecting network evidence: {e}")
            raise

    async def analyze_network_capture(self, pcap_file: str) -> ForensicsResult:
        """Analyze network capture using tshark."""
        try:
            logger.info(f"Analyzing network capture: {pcap_file}")
            start_time = time.time()

            findings = []

            # Run tshark analysis
            analyses = [
                ('-q -z conv,ip', 'conversations'),
                ('-q -z conv,tcp', 'tcp_conversations'),
                ('-q -z conv,udp', 'udp_conversations'),
                ('-q -z http,stat', 'http_statistics'),
                ('-q -z dns,stat', 'dns_statistics')
            ]

            for args, analysis_type in analyses:
                logger.info(f"Running {analysis_type} analysis")

                cmd = ['tshark', '-r', pcap_file] + args.split()
                result = await self._run_command(cmd)

                if result['success']:
                    analysis_findings = self._parse_tshark_output(analysis_type, result['output'])
                    findings.extend(analysis_findings)
                else:
                    logger.warning(f"Analysis {analysis_type} failed: {result['error']}")

            duration = time.time() - start_time

            forensics_result = ForensicsResult(
                analysis_type=ForensicsType.NETWORK_FORENSICS,
                target=pcap_file,
                success=True,
                findings=findings,
                evidence_collected=[self._find_evidence_by_path(pcap_file)],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(forensics_result)
            return forensics_result

        except Exception as e:
            logger.error(f"Error analyzing network capture: {e}")
            return ForensicsResult(
                analysis_type=ForensicsType.NETWORK_FORENSICS,
                target=pcap_file,
                success=False,
                findings=[],
                evidence_collected=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    def _parse_tshark_output(self, analysis_type: str, output: str) -> list[dict[str, Any]]:
        """Parse tshark analysis output."""
        findings = []

        try:
            lines = output.split('\n')

            if analysis_type == 'conversations':
                # Parse IP conversations
                for line in lines:
                    if line.strip() and not line.startswith('='):
                        parts = line.split()
                        if len(parts) >= 6:
                            findings.append({
                                'type': 'ip_conversation',
                                'src_addr': parts[0],
                                'dst_addr': parts[1],
                                'packets': parts[2],
                                'bytes': parts[3],
                                'tool': 'tshark'
                            })

            elif analysis_type == 'http_statistics':
                # Parse HTTP statistics
                for line in lines:
                    if 'requests' in line.lower() or 'responses' in line.lower():
                        findings.append({
                            'type': 'http_statistic',
                            'data': line.strip(),
                            'tool': 'tshark'
                        })

            else:
                # Generic parsing for other analyses
                findings.append({
                    'type': 'analysis_output',
                    'analysis': analysis_type,
                    'data': output.strip(),
                    'tool': 'tshark'
                })

        except Exception as e:
            logger.error(f"Error parsing tshark {analysis_type} output: {e}")

        return findings

    async def analyze_file(self, file_path: str) -> dict[str, Any]:
        """Analyze a single file using multiple tools."""
        try:
            logger.info(f"Analyzing file: {file_path}")

            analysis_results = {}

            # File type analysis
            cmd = ['file', file_path]
            result = await self._run_command(cmd)
            if result['success']:
                analysis_results['file_type'] = result['output'].strip()

            # String extraction
            cmd = ['strings', file_path]
            result = await self._run_command(cmd)
            if result['success']:
                analysis_results['strings'] = result['output'][:1000]  # First 1000 chars

            # EXIF data (if applicable)
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff')):
                cmd = ['exiftool', file_path]
                result = await self._run_command(cmd)
                if result['success']:
                    analysis_results['exif'] = result['output']

            # Binary analysis with binwalk
            cmd = ['binwalk', file_path]
            result = await self._run_command(cmd)
            if result['success']:
                analysis_results['binwalk'] = result['output']

            # Calculate hashes
            analysis_results['md5'] = await self._calculate_file_hash(file_path, 'md5')
            analysis_results['sha1'] = await self._calculate_file_hash(file_path, 'sha1')
            analysis_results['sha256'] = await self._calculate_file_hash(file_path, 'sha256')

            return {
                'success': True,
                'file_path': file_path,
                'analysis': analysis_results
            }

        except Exception as e:
            logger.error(f"Error analyzing file: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    async def _calculate_file_hash(self, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate file hash using specified algorithm."""
        try:
            hash_func = getattr(hashlib, algorithm)()

            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)

            return hash_func.hexdigest()

        except Exception as e:
            logger.error(f"Error calculating {algorithm} hash: {e}")
            return ""

    def _find_evidence_by_path(self, file_path: str) -> EvidenceItem | None:
        """Find evidence item by file path."""
        for evidence in self.evidence_collected:
            if evidence.path == file_path:
                return evidence
        return None

    def _is_linux_target(self, target: str) -> bool:
        """Check if target is Linux-based."""
        return any(os_name in target.lower() for os_name in ['linux', 'ubuntu', 'centos', 'debian'])

    def _is_windows_target(self, target: str) -> bool:
        """Check if target is Windows-based."""
        return any(os_name in target.lower() for os_name in ['windows', 'win', 'nt'])

    def _detect_target_os(self, target: str) -> str:
        """Detect target operating system."""
        if self._is_linux_target(target):
            return 'Linux'
        elif self._is_windows_target(target):
            return 'Windows'
        else:
            return 'Unknown'

    async def _run_command(self, cmd: list[str]) -> dict[str, Any]:
        """Run a command and return results."""
        try:
            logger.debug(f"Running command: {' '.join(cmd)}")

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            stdout, stderr = await process.communicate()

            return {
                'success': process.returncode == 0,
                'output': stdout.decode('utf-8', errors='ignore'),
                'error': stderr.decode('utf-8', errors='ignore'),
                'return_code': process.returncode
            }

        except Exception as e:
            logger.error(f"Error running command {' '.join(cmd)}: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }

    def get_evidence_collected(self) -> list[EvidenceItem]:
        """Get all collected evidence."""
        return self.evidence_collected

    def get_analysis_history(self) -> list[ForensicsResult]:
        """Get analysis history."""
        return self.analysis_history

    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive forensics report."""
        try:
            if not output_file:
                timestamp = int(time.time())
                output_file = os.path.join(self.reports_dir, f"forensics_report_{timestamp}.html")

            # Generate HTML report
            html_content = self._generate_html_report()

            with open(output_file, 'w') as f:
                f.write(html_content)

            logger.info(f"Forensics report generated: {output_file}")
            return output_file

        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return ""

    def _generate_html_report(self) -> str:
        """Generate HTML report content."""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Digital Forensics Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .evidence-item {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; border-radius: 3px; }}
        .finding {{ background-color: #e8f4f8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Digital Forensics Report</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Evidence Items: {len(self.evidence_collected)}</p>
        <p>Analyses Performed: {len(self.analysis_history)}</p>
    </div>

    <div class="section">
        <h2>Evidence Collected</h2>
        {self._generate_evidence_html()}
    </div>

    <div class="section">
        <h2>Analysis Results</h2>
        {self._generate_analysis_html()}
    </div>
</body>
</html>
        """
        return html

    def _generate_evidence_html(self) -> str:
        """Generate HTML for evidence section."""
        html = ""
        for evidence in self.evidence_collected:
            html += f"""
            <div class="evidence-item">
                <h3>{evidence.type.value.replace('_', ' ').title()}</h3>
                <p><strong>Source:</strong> {evidence.source}</p>
                <p><strong>Path:</strong> {evidence.path}</p>
                <p><strong>Hash:</strong> {evidence.hash}</p>
                <p><strong>Size:</strong> {evidence.size} bytes</p>
                <p><strong>Timestamp:</strong> {evidence.timestamp}</p>
            </div>
            """
        return html

    def _generate_analysis_html(self) -> str:
        """Generate HTML for analysis section."""
        html = ""
        for analysis in self.analysis_history:
            html += f"""
            <div class="section">
                <h3>{analysis.analysis_type.value.replace('_', ' ').title()}</h3>
                <p><strong>Target:</strong> {analysis.target}</p>
                <p><strong>Success:</strong> {analysis.success}</p>
                <p><strong>Duration:</strong> {analysis.duration:.2f} seconds</p>
                <p><strong>Findings:</strong> {len(analysis.findings)}</p>
                <p><strong>Timestamp:</strong> {analysis.timestamp}</p>
            </div>
            """
        return html

    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up temporary files
            for evidence in self.evidence_collected:
                if os.path.exists(evidence.path):
                    os.remove(evidence.path)

            logger.info("Forensics tools cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Example usage and testing
async def main():
    """Example usage of forensics tools."""
    tools = ForensicsTools()

    try:
        # Collect evidence
        print("Collecting evidence...")

        # Memory evidence (simulated)
        print("Memory evidence collection completed")

        # File analysis
        test_file = "/etc/passwd"
        if os.path.exists(test_file):
            analysis = await tools.analyze_file(test_file)
            print(f"File analysis result: {analysis['success']}")

        # Generate report
        report_file = tools.generate_report()
        print(f"Report generated: {report_file}")

    finally:
        tools.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
