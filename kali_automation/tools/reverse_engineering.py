#!/usr/bin/env python3
"""
Reverse Engineering Tools Category

This module provides automation for reverse engineering tools including:
- Binary analysis (Ghidra, IDA Pro, Radare2)
- Malware analysis and sandboxing
- Disassembly and decompilation
- Dynamic analysis and debugging
- Code obfuscation analysis
- YARA rule generation and scanning
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

import pefile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalysisType(Enum):
    """Types of reverse engineering analysis."""
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    MALWARE_ANALYSIS = "malware_analysis"
    CODE_ANALYSIS = "code_analysis"
    NETWORK_ANALYSIS = "network_analysis"
    BEHAVIOR_ANALYSIS = "behavior_analysis"


class BinaryType(Enum):
    """Types of binary files."""
    EXECUTABLE = "executable"
    LIBRARY = "library"
    DRIVER = "driver"
    MALWARE = "malware"
    UNKNOWN = "unknown"


@dataclass
class BinaryInfo:
    """Information about a binary file."""
    file_path: str
    file_type: BinaryType
    architecture: str
    platform: str
    entry_point: int
    sections: list[dict[str, Any]]
    imports: list[str]
    exports: list[str]
    strings: list[str]
    file_hash: str
    size: int


@dataclass
class AnalysisResult:
    """Result of a reverse engineering analysis."""
    analysis_type: AnalysisType
    target: str
    success: bool
    findings: list[dict[str, Any]]
    artifacts: list[str]
    timestamp: str
    duration: float
    output: str = None
    error: str = None


class ReverseEngineeringTools:
    """Main class for reverse engineering tool automation."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize reverse engineering tools."""
        self.config = config or {}
        self.output_dir = self.config.get('output_dir', '/tmp/reverse_engineering_output')
        self.artifacts_dir = os.path.join(self.output_dir, 'artifacts')
        self.reports_dir = os.path.join(self.output_dir, 'reports')

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.artifacts_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        # Tool paths
        self.tools = {
            'radare2': 'r2',
            'ghidra': 'ghidra',
            'ida': 'ida64',
            'objdump': 'objdump',
            'readelf': 'readelf',
            'nm': 'nm',
            'strings': 'strings',
            'hexdump': 'hexdump',
            'xxd': 'xxd',
            'file': 'file',
            'ldd': 'ldd',
            'strace': 'strace',
            'ltrace': 'ltrace',
            'gdb': 'gdb',
            'valgrind': 'valgrind'
        }

        # Analysis tracking
        self.analysis_history: list[AnalysisResult] = []
        self.binary_cache: dict[str, BinaryInfo] = {}

        logger.info("Reverse engineering tools initialized")

    async def analyze_binary(self, file_path: str) -> BinaryInfo:
        """Perform comprehensive binary analysis."""
        try:
            logger.info(f"Analyzing binary: {file_path}")

            # Check if already analyzed
            if file_path in self.binary_cache:
                return self.binary_cache[file_path]

            # Basic file information
            file_hash = await self._calculate_file_hash(file_path)
            file_size = os.path.getsize(file_path)

            # Determine binary type
            binary_type = await self._determine_binary_type(file_path)

            # Architecture detection
            architecture = await self._detect_architecture(file_path)

            # Platform detection
            platform = await self._detect_platform(file_path)

            # Entry point analysis
            entry_point = await self._get_entry_point(file_path)

            # Section analysis
            sections = await self._analyze_sections(file_path)

            # Import/Export analysis
            imports = await self._analyze_imports(file_path)
            exports = await self._analyze_exports(file_path)

            # String extraction
            strings = await self._extract_strings(file_path)

            binary_info = BinaryInfo(
                file_path=file_path,
                file_type=binary_type,
                architecture=architecture,
                platform=platform,
                entry_point=entry_point,
                sections=sections,
                imports=imports,
                exports=exports,
                strings=strings,
                file_hash=file_hash,
                size=file_size
            )

            # Cache the result
            self.binary_cache[file_path] = binary_info

            logger.info(f"Binary analysis completed for {file_path}")
            return binary_info

        except Exception as e:
            logger.error(f"Error analyzing binary: {e}")
            raise

    async def _determine_binary_type(self, file_path: str) -> BinaryType:
        """Determine the type of binary file."""
        try:
            cmd = ['file', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                output = result['output'].lower()

                if 'executable' in output:
                    return BinaryType.EXECUTABLE
                elif 'shared object' in output or 'library' in output:
                    return BinaryType.LIBRARY
                elif 'driver' in output or 'kernel' in output:
                    return BinaryType.DRIVER
                elif 'malware' in output or 'trojan' in output or 'virus' in output:
                    return BinaryType.MALWARE
                else:
                    return BinaryType.UNKNOWN

            return BinaryType.UNKNOWN

        except Exception as e:
            logger.error(f"Error determining binary type: {e}")
            return BinaryType.UNKNOWN

    async def _detect_architecture(self, file_path: str) -> str:
        """Detect the architecture of a binary."""
        try:
            cmd = ['file', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                output = result['output'].lower()

                if 'x86-64' in output or 'amd64' in output:
                    return 'x86_64'
                elif 'x86' in output or 'i386' in output:
                    return 'x86'
                elif 'arm' in output:
                    return 'ARM'
                elif 'mips' in output:
                    return 'MIPS'
                elif 'powerpc' in output:
                    return 'PowerPC'
                else:
                    return 'Unknown'

            return 'Unknown'

        except Exception as e:
            logger.error(f"Error detecting architecture: {e}")
            return 'Unknown'

    async def _detect_platform(self, file_path: str) -> str:
        """Detect the platform of a binary."""
        try:
            cmd = ['file', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                output = result['output'].lower()

                if 'linux' in output:
                    return 'Linux'
                elif 'windows' in output:
                    return 'Windows'
                elif 'macos' in output or 'darwin' in output:
                    return 'macOS'
                elif 'freebsd' in output:
                    return 'FreeBSD'
                else:
                    return 'Unknown'

            return 'Unknown'

        except Exception as e:
            logger.error(f"Error detecting platform: {e}")
            return 'Unknown'

    async def _get_entry_point(self, file_path: str) -> int:
        """Get the entry point of a binary."""
        try:
            # Try using objdump for ELF files
            cmd = ['objdump', '-f', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                lines = result['output'].split('\n')
                for line in lines:
                    if 'start address' in line.lower():
                        try:
                            addr = line.split()[-1]
                            return int(addr, 16)
                        except ValueError:
                            pass

            # Try using readelf for ELF files
            cmd = ['readelf', '-h', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                lines = result['output'].split('\n')
                for line in lines:
                    if 'entry point address' in line.lower():
                        try:
                            addr = line.split()[-1]
                            return int(addr, 16)
                        except ValueError:
                            pass

            return 0

        except Exception as e:
            logger.error(f"Error getting entry point: {e}")
            return 0

    async def _analyze_sections(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze binary sections."""
        try:
            sections = []

            # Use objdump for section analysis
            cmd = ['objdump', '-h', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                lines = result['output'].split('\n')
                for line in lines[2:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 6:
                            section = {
                                'name': parts[0],
                                'size': parts[1],
                                'vma': parts[2],
                                'lma': parts[3],
                                'file_off': parts[4],
                                'align': parts[5]
                            }
                            sections.append(section)

            return sections

        except Exception as e:
            logger.error(f"Error analyzing sections: {e}")
            return []

    async def _analyze_imports(self, file_path: str) -> list[str]:
        """Analyze binary imports."""
        try:
            imports = []

            # Use objdump for import analysis
            cmd = ['objdump', '-T', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                lines = result['output'].split('\n')
                for line in lines:
                    if 'DF' in line and '*UND*' in line:
                        parts = line.split()
                        if len(parts) >= 6:
                            import_name = parts[-1]
                            imports.append(import_name)

            return imports

        except Exception as e:
            logger.error(f"Error analyzing imports: {e}")
            return []

    async def _analyze_exports(self, file_path: str) -> list[str]:
        """Analyze binary exports."""
        try:
            exports = []

            # Use objdump for export analysis
            cmd = ['objdump', '-T', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                lines = result['output'].split('\n')
                for line in lines:
                    if 'DF' in line and '*UND*' not in line:
                        parts = line.split()
                        if len(parts) >= 6:
                            export_name = parts[-1]
                            exports.append(export_name)

            return exports

        except Exception as e:
            logger.error(f"Error analyzing exports: {e}")
            return []

    async def _extract_strings(self, file_path: str) -> list[str]:
        """Extract strings from binary."""
        try:
            cmd = ['strings', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                strings = result['output'].split('\n')
                # Filter out very short strings and common noise
                filtered_strings = [s for s in strings if len(s) > 3 and not s.isdigit()]
                return filtered_strings[:1000]  # Limit to first 1000 strings

            return []

        except Exception as e:
            logger.error(f"Error extracting strings: {e}")
            return []

    async def perform_static_analysis(self, file_path: str) -> AnalysisResult:
        """Perform static analysis on a binary."""
        try:
            logger.info(f"Starting static analysis on {file_path}")
            start_time = time.time()

            # Get binary information
            binary_info = await self.analyze_binary(file_path)

            findings = []

            # Analyze PE file if it's a Windows executable
            if binary_info.platform == 'Windows' and file_path.endswith(('.exe', '.dll')):
                pe_findings = await self._analyze_pe_file(file_path)
                findings.extend(pe_findings)

            # Analyze ELF file if it's a Linux executable
            elif binary_info.platform == 'Linux':
                elf_findings = await self._analyze_elf_file(file_path)
                findings.extend(elf_findings)

            # Analyze strings for suspicious patterns
            string_findings = await self._analyze_strings(binary_info.strings)
            findings.extend(string_findings)

            # Analyze imports for suspicious functions
            import_findings = await self._analyze_imports_suspicious(binary_info.imports)
            findings.extend(import_findings)

            duration = time.time() - start_time

            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.STATIC_ANALYSIS,
                target=file_path,
                success=True,
                findings=findings,
                artifacts=[file_path],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(analysis_result)
            return analysis_result

        except Exception as e:
            logger.error(f"Error in static analysis: {e}")
            return AnalysisResult(
                analysis_type=AnalysisType.STATIC_ANALYSIS,
                target=file_path,
                success=False,
                findings=[],
                artifacts=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _analyze_pe_file(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze PE (Portable Executable) file."""
        findings = []

        try:
            pe = pefile.PE(file_path)

            # Check for suspicious characteristics
            if pe.OPTIONAL_HEADER.DllCharacteristics & 0x0040:  # IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE
                findings.append({
                    'type': 'aslr_enabled',
                    'description': 'ASLR (Address Space Layout Randomization) is enabled',
                    'severity': 'info'
                })

            # Check for suspicious sections
            for section in pe.sections:
                if section.Name.decode().strip('\x00') in ['.text', '.data', '.rdata']:
                    if section.SizeOfRawData > 0 and section.PointerToRawData == 0:
                        findings.append({
                            'type': 'suspicious_section',
                            'description': f'Suspicious section {section.Name.decode()}',
                            'severity': 'warning'
                        })

            # Check for suspicious imports
            suspicious_apis = [
                'CreateRemoteThread', 'VirtualAllocEx', 'WriteProcessMemory',
                'SetWindowsHookEx', 'RegisterHotKey', 'SetTimer'
            ]

            for entry in pe.DIRECTORY_ENTRY_IMPORT:
                for imp in entry.imports:
                    if imp.name and imp.name.decode() in suspicious_apis:
                        findings.append({
                            'type': 'suspicious_import',
                            'description': f'Suspicious API: {imp.name.decode()}',
                            'severity': 'warning'
                        })

            pe.close()

        except Exception as e:
            logger.error(f"Error analyzing PE file: {e}")

        return findings

    async def _analyze_elf_file(self, file_path: str) -> list[dict[str, Any]]:
        """Analyze ELF file."""
        findings = []

        try:
            # Use readelf for ELF analysis
            cmd = ['readelf', '-a', file_path]
            result = await self._run_command(cmd)

            if result['success']:
                output = result['output']

                # Check for stripped binary
                if 'not stripped' not in output:
                    findings.append({
                        'type': 'stripped_binary',
                        'description': 'Binary is stripped (symbols removed)',
                        'severity': 'info'
                    })

                # Check for suspicious sections
                if '.text' in output and '.data' in output:
                    findings.append({
                        'type': 'standard_sections',
                        'description': 'Standard ELF sections present',
                        'severity': 'info'
                    })

        except Exception as e:
            logger.error(f"Error analyzing ELF file: {e}")

        return findings

    async def _analyze_strings(self, strings: list[str]) -> list[dict[str, Any]]:
        """Analyze strings for suspicious patterns."""
        findings = []

        suspicious_patterns = [
            'http://', 'https://', 'ftp://', 'cmd.exe', 'powershell',
            'registry', 'regedit', 'taskkill', 'netstat', 'ipconfig',
            'malware', 'trojan', 'virus', 'backdoor', 'keylogger'
        ]

        for string in strings:
            for pattern in suspicious_patterns:
                if pattern.lower() in string.lower():
                    findings.append({
                        'type': 'suspicious_string',
                        'description': f'Suspicious string found: {string}',
                        'pattern': pattern,
                        'severity': 'warning'
                    })

        return findings

    async def _analyze_imports_suspicious(self, imports: list[str]) -> list[dict[str, Any]]:
        """Analyze imports for suspicious functions."""
        findings = []

        suspicious_imports = [
            'CreateRemoteThread', 'VirtualAllocEx', 'WriteProcessMemory',
            'SetWindowsHookEx', 'RegisterHotKey', 'SetTimer',
            'CreateFile', 'WriteFile', 'ReadFile', 'DeleteFile',
            'RegCreateKey', 'RegSetValue', 'RegDeleteKey'
        ]

        for imp in imports:
            if imp in suspicious_imports:
                findings.append({
                    'type': 'suspicious_import',
                    'description': f'Suspicious import: {imp}',
                    'severity': 'warning'
                })

        return findings

    async def perform_dynamic_analysis(self, file_path: str,
                                     timeout: int = 300) -> AnalysisResult:
        """Perform dynamic analysis on a binary."""
        try:
            logger.info(f"Starting dynamic analysis on {file_path}")
            start_time = time.time()

            findings = []
            artifacts = []

            # Create sandbox environment
            sandbox_dir = os.path.join(self.artifacts_dir, f"sandbox_{int(time.time())}")
            os.makedirs(sandbox_dir, exist_ok=True)

            # Copy binary to sandbox
            sandbox_binary = os.path.join(sandbox_dir, os.path.basename(file_path))
            shutil.copy2(file_path, sandbox_binary)

            # Make executable
            os.chmod(sandbox_binary, 0o755)

            # Run with strace for system call monitoring
            strace_log = os.path.join(sandbox_dir, 'strace.log')
            cmd = ['strace', '-o', strace_log, '-f', sandbox_binary]

            # Run in background with timeout
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            try:
                await asyncio.wait_for(process.communicate(), timeout=timeout)
            except TimeoutError:
                process.terminate()
                findings.append({
                    'type': 'timeout',
                    'description': f'Binary execution timed out after {timeout} seconds',
                    'severity': 'warning'
                })

            # Analyze strace output
            if os.path.exists(strace_log):
                strace_findings = await self._analyze_strace_log(strace_log)
                findings.extend(strace_findings)
                artifacts.append(strace_log)

            # Check for created files
            created_files = await self._find_created_files(sandbox_dir)
            findings.extend(created_files)

            duration = time.time() - start_time

            analysis_result = AnalysisResult(
                analysis_type=AnalysisType.DYNAMIC_ANALYSIS,
                target=file_path,
                success=True,
                findings=findings,
                artifacts=artifacts,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(analysis_result)
            return analysis_result

        except Exception as e:
            logger.error(f"Error in dynamic analysis: {e}")
            return AnalysisResult(
                analysis_type=AnalysisType.DYNAMIC_ANALYSIS,
                target=file_path,
                success=False,
                findings=[],
                artifacts=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _analyze_strace_log(self, strace_log: str) -> list[dict[str, Any]]:
        """Analyze strace log for suspicious activity."""
        findings = []

        try:
            with open(strace_log) as f:
                lines = f.readlines()

            suspicious_syscalls = [
                'execve', 'fork', 'clone', 'ptrace', 'mmap',
                'mprotect', 'open', 'write', 'socket', 'connect'
            ]

            syscall_counts = {}

            for line in lines:
                for syscall in suspicious_syscalls:
                    if syscall in line:
                        syscall_counts[syscall] = syscall_counts.get(syscall, 0) + 1

                        # Check for specific suspicious patterns
                        if 'execve' in line and ('/tmp/' in line or '/dev/' in line):
                            findings.append({
                                'type': 'suspicious_execution',
                                'description': f'Suspicious execution: {line.strip()}',
                                'severity': 'warning'
                            })

                        if 'socket' in line and 'connect' in line:
                            findings.append({
                                'type': 'network_activity',
                                'description': f'Network activity detected: {line.strip()}',
                                'severity': 'info'
                            })

            # Add syscall count findings
            for syscall, count in syscall_counts.items():
                if count > 10:  # Threshold for suspicious activity
                    findings.append({
                        'type': 'frequent_syscall',
                        'description': f'Frequent {syscall} calls: {count} times',
                        'severity': 'info'
                    })

        except Exception as e:
            logger.error(f"Error analyzing strace log: {e}")

        return findings

    async def _find_created_files(self, sandbox_dir: str) -> list[dict[str, Any]]:
        """Find files created during dynamic analysis."""
        findings = []

        try:
            for root, dirs, files in os.walk(sandbox_dir):
                for file in files:
                    if file != os.path.basename(sandbox_dir):
                        file_path = os.path.join(root, file)
                        file_size = os.path.getsize(file_path)

                        findings.append({
                            'type': 'created_file',
                            'description': f'File created: {file}',
                            'path': file_path,
                            'size': file_size,
                            'severity': 'info'
                        })

        except Exception as e:
            logger.error(f"Error finding created files: {e}")

        return findings

    async def generate_yara_rules(self, file_path: str) -> str:
        """Generate YARA rules based on binary analysis."""
        try:
            logger.info(f"Generating YARA rules for {file_path}")

            binary_info = await self.analyze_binary(file_path)

            # Generate rule content
            rule_name = f"rule_{os.path.basename(file_path).replace('.', '_')}"

            yara_rule = f"""
rule {rule_name}
{{
    meta:
        description = "Auto-generated rule for {os.path.basename(file_path)}"
        author = "Kali Automation"
        date = "{time.strftime('%Y-%m-%d')}"
        hash = "{binary_info.file_hash}"
        platform = "{binary_info.platform}"
        architecture = "{binary_info.architecture}"

    strings:
"""

            # Add string conditions
            for i, string in enumerate(binary_info.strings[:20]):  # Limit to first 20 strings
                if len(string) > 3 and string.isprintable():
                    yara_rule += f'        $s{i} = "{string}"\n'

            yara_rule += """
    condition:
        """

            # Add condition
            if binary_info.strings:
                yara_rule += "any of them"
            else:
                yara_rule += "uint16(0) == 0x5A4D"  # MZ header for PE files

            yara_rule += "\n}\n"

            # Save rule
            rule_file = os.path.join(self.artifacts_dir, f"{rule_name}.yar")
            with open(rule_file, 'w') as f:
                f.write(yara_rule)

            logger.info(f"YARA rule generated: {rule_file}")
            return rule_file

        except Exception as e:
            logger.error(f"Error generating YARA rules: {e}")
            return ""

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

    def get_analysis_history(self) -> list[AnalysisResult]:
        """Get analysis history."""
        return self.analysis_history

    def get_binary_cache(self) -> dict[str, BinaryInfo]:
        """Get cached binary information."""
        return self.binary_cache

    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive reverse engineering report."""
        try:
            if not output_file:
                timestamp = int(time.time())
                output_file = os.path.join(self.reports_dir, f"reverse_engineering_report_{timestamp}.html")

            # Generate HTML report
            html_content = self._generate_html_report()

            with open(output_file, 'w') as f:
                f.write(html_content)

            logger.info(f"Reverse engineering report generated: {output_file}")
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
    <title>Reverse Engineering Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .finding {{ background-color: #e8f4f8; padding: 10px; margin: 5px 0; border-radius: 3px; }}
        .warning {{ background-color: #fff3cd; border-left: 4px solid #ffc107; }}
        .info {{ background-color: #d1ecf1; border-left: 4px solid #17a2b8; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Reverse Engineering Report</h1>
        <p>Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Binaries Analyzed: {len(self.binary_cache)}</p>
        <p>Analyses Performed: {len(self.analysis_history)}</p>
    </div>

    <div class="section">
        <h2>Binary Analysis Results</h2>
        {self._generate_binary_analysis_html()}
    </div>

    <div class="section">
        <h2>Analysis History</h2>
        {self._generate_analysis_history_html()}
    </div>
</body>
</html>
        """
        return html

    def _generate_binary_analysis_html(self) -> str:
        """Generate HTML for binary analysis section."""
        html = ""
        for file_path, binary_info in self.binary_cache.items():
            html += f"""
            <div class="section">
                <h3>{os.path.basename(file_path)}</h3>
                <p><strong>Type:</strong> {binary_info.file_type.value}</p>
                <p><strong>Platform:</strong> {binary_info.platform}</p>
                <p><strong>Architecture:</strong> {binary_info.architecture}</p>
                <p><strong>Entry Point:</strong> 0x{binary_info.entry_point:X}</p>
                <p><strong>Size:</strong> {binary_info.size} bytes</p>
                <p><strong>Hash:</strong> {binary_info.file_hash}</p>
                <p><strong>Imports:</strong> {len(binary_info.imports)}</p>
                <p><strong>Exports:</strong> {len(binary_info.exports)}</p>
                <p><strong>Strings:</strong> {len(binary_info.strings)}</p>
            </div>
            """
        return html

    def _generate_analysis_history_html(self) -> str:
        """Generate HTML for analysis history section."""
        html = ""
        for analysis in self.analysis_history:
            severity_class = 'info'
            if any('warning' in finding.get('severity', '') for finding in analysis.findings):
                severity_class = 'warning'

            html += f"""
            <div class="section {severity_class}">
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
            for analysis in self.analysis_history:
                for artifact in analysis.artifacts:
                    if os.path.exists(artifact) and artifact.startswith('/tmp'):
                        try:
                            os.remove(artifact)
                        except Exception:
                            pass

            logger.info("Reverse engineering tools cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Example usage and testing
async def main():
    """Example usage of reverse engineering tools."""
    tools = ReverseEngineeringTools()

    try:
        # Analyze a binary
        test_file = "/bin/ls"  # Use a common Linux binary
        if os.path.exists(test_file):
            print(f"Analyzing binary: {test_file}")

            # Static analysis
            static_result = await tools.perform_static_analysis(test_file)
            print(f"Static analysis completed: {len(static_result.findings)} findings")

            # Dynamic analysis (be careful with system binaries)
            print("Skipping dynamic analysis for system binary")

            # Generate YARA rules
            yara_file = await tools.generate_yara_rules(test_file)
            print(f"YARA rules generated: {yara_file}")

        # Generate report
        report_file = tools.generate_report()
        print(f"Report generated: {report_file}")

    finally:
        tools.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
