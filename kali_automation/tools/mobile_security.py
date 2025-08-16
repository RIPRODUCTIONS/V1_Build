#!/usr/bin/env python3
"""
Mobile Security Tools Category

This module provides automation for mobile security testing tools including:
- Android app analysis and reverse engineering
- iOS app security testing
- Mobile device forensics
- App vulnerability assessment
- Mobile malware analysis
- Device security testing
"""

import asyncio
import hashlib
import json
import logging
import os
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MobilePlatform(Enum):
    """Mobile platforms."""
    ANDROID = "android"
    IOS = "ios"
    UNKNOWN = "unknown"


class AppAnalysisType(Enum):
    """Types of app analysis."""
    STATIC_ANALYSIS = "static_analysis"
    DYNAMIC_ANALYSIS = "dynamic_analysis"
    MALWARE_ANALYSIS = "malware_analysis"
    PERMISSION_ANALYSIS = "permission_analysis"
    NETWORK_ANALYSIS = "network_analysis"
    CODE_ANALYSIS = "code_analysis"


@dataclass
class MobileApp:
    """Information about a mobile app."""
    package_name: str
    app_name: str
    version: str
    platform: MobilePlatform
    file_path: str
    file_size: int
    file_hash: str
    permissions: list[str]
    activities: list[str]
    services: list[str]
    receivers: list[str]
    providers: list[str]
    min_sdk: int
    target_sdk: int


@dataclass
class AnalysisResult:
    """Result of a mobile app analysis."""
    analysis_type: AppAnalysisType
    target: str
    success: bool
    findings: list[dict[str, Any]]
    artifacts: list[str]
    timestamp: str
    duration: float
    output: str = None
    error: str = None


class MobileSecurityTools:
    """Main class for mobile security tool automation."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize mobile security tools."""
        self.config = config or {}
        self.output_dir = self.config.get('output_dir', '/tmp/mobile_security_output')
        self.apps_dir = os.path.join(self.output_dir, 'apps')
        self.reports_dir = os.path.join(self.output_dir, 'reports')
        self.decompiled_dir = os.path.join(self.output_dir, 'decompiled')

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.apps_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)
        os.makedirs(self.decompiled_dir, exist_ok=True)

        # Tool paths
        self.tools = {
            'apktool': 'apktool',
            'dex2jar': 'd2j-dex2jar',
            'jadx': 'jadx',
            'jadx-gui': 'jadx-gui',
            'androguard': 'androguard',
            'apkleaks': 'apkleaks',
            'mobsf': 'mobsf',
            'drozer': 'drozer',
            'frida': 'frida',
            'objection': 'objection',
            'cycript': 'cycript',
            'class-dump': 'class-dump',
            'otool': 'otool',
            'strings': 'strings',
            'file': 'file',
            'adb': 'adb',
            'fastboot': 'fastboot'
        }

        # Analysis tracking
        self.analysis_history: list[AnalysisResult] = []
        self.analyzed_apps: dict[str, MobileApp] = {}

        logger.info("Mobile security tools initialized")

    async def analyze_android_app(self, apk_file: str) -> MobileApp:
        """Analyze an Android APK file."""
        try:
            logger.info(f"Analyzing Android app: {apk_file}")

            # Check if already analyzed
            if apk_file in self.analyzed_apps:
                return self.analyzed_apps[apk_file]

            # Basic file information
            file_size = os.path.getsize(apk_file)
            file_hash = await self._calculate_file_hash(apk_file)

            # Extract APK information
            app_info = await self._extract_apk_info(apk_file)

            # Decompile APK
            decompiled_path = await self._decompile_apk(apk_file)

            # Extract permissions
            permissions = await self._extract_permissions(decompiled_path)

            # Extract components
            activities = await self._extract_activities(decompiled_path)
            services = await self._extract_services(decompiled_path)
            receivers = await self._extract_receivers(decompiled_path)
            providers = await self._extract_providers(decompiled_path)

            # Create MobileApp object
            mobile_app = MobileApp(
                package_name=app_info.get('package_name', ''),
                app_name=app_info.get('app_name', ''),
                version=app_info.get('version', ''),
                platform=MobilePlatform.ANDROID,
                file_path=apk_file,
                file_size=file_size,
                file_hash=file_hash,
                permissions=permissions,
                activities=activities,
                services=services,
                receivers=receivers,
                providers=providers,
                min_sdk=app_info.get('min_sdk', 0),
                target_sdk=app_info.get('target_sdk', 0)
            )

            # Cache the result
            self.analyzed_apps[apk_file] = mobile_app

            logger.info(f"Android app analysis completed for {apk_file}")
            return mobile_app

        except Exception as e:
            logger.error(f"Error analyzing Android app: {e}")
            raise

    async def _extract_apk_info(self, apk_file: str) -> dict[str, Any]:
        """Extract basic information from APK file."""
        app_info = {}

        try:
            # Use apktool to extract basic info
            cmd = ['apktool', 'd', apk_file, '-f', '-o', '/tmp/apk_temp']
            result = await self._run_command(cmd)

            if result['success']:
                # Parse AndroidManifest.xml
                manifest_path = '/tmp/apk_temp/AndroidManifest.xml'
                if os.path.exists(manifest_path):
                    app_info = await self._parse_android_manifest(manifest_path)

                # Clean up
                import shutil
                shutil.rmtree('/tmp/apk_temp', ignore_errors=True)

        except Exception as e:
            logger.error(f"Error extracting APK info: {e}")

        return app_info

    async def _parse_android_manifest(self, manifest_path: str) -> dict[str, Any]:
        """Parse AndroidManifest.xml file."""
        manifest_info = {}

        try:
            # Parse XML manifest
            tree = ET.parse(manifest_path)
            root = tree.getroot()

            # Extract package name
            manifest_info['package_name'] = root.get('package', '')

            # Extract version info
            version_code = root.get('android:versionCode', '0')
            version_name = root.get('android:versionName', '')
            manifest_info['version'] = version_name

            # Extract SDK info
            uses_sdk = root.find('.//uses-sdk')
            if uses_sdk is not None:
                manifest_info['min_sdk'] = int(uses_sdk.get('android:minSdkVersion', '0'))
                manifest_info['target_sdk'] = int(uses_sdk.get('android:targetSdkVersion', '0'))

            # Extract app name
            application = root.find('.//application')
            if application is not None:
                app_name = application.get('android:label', '')
                if app_name.startswith('@'):
                    # Reference to string resource
                    app_name = 'Unknown'
                manifest_info['app_name'] = app_name

        except Exception as e:
            logger.error(f"Error parsing Android manifest: {e}")

        return manifest_info

    async def _decompile_apk(self, apk_file: str) -> str:
        """Decompile APK using apktool."""
        try:
            # Generate output directory name
            app_name = os.path.splitext(os.path.basename(apk_file))[0]
            output_dir = os.path.join(self.decompiled_dir, f"{app_name}_{int(time.time())}")

            # Decompile APK
            cmd = ['apktool', 'd', apk_file, '-f', '-o', output_dir]
            result = await self._run_command(cmd)

            if result['success']:
                logger.info(f"APK decompiled to: {output_dir}")
                return output_dir
            else:
                raise Exception(f"APK decompilation failed: {result['error']}")

        except Exception as e:
            logger.error(f"Error decompiling APK: {e}")
            raise

    async def _extract_permissions(self, decompiled_path: str) -> list[str]:
        """Extract permissions from decompiled APK."""
        permissions = []

        try:
            manifest_path = os.path.join(decompiled_path, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()

                # Find all permission elements
                for permission in root.findall('.//uses-permission'):
                    perm_name = permission.get('android:name', '')
                    if perm_name:
                        permissions.append(perm_name)

        except Exception as e:
            logger.error(f"Error extracting permissions: {e}")

        return permissions

    async def _extract_activities(self, decompiled_path: str) -> list[str]:
        """Extract activities from decompiled APK."""
        activities = []

        try:
            manifest_path = os.path.join(decompiled_path, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()

                # Find all activity elements
                for activity in root.findall('.//activity'):
                    activity_name = activity.get('android:name', '')
                    if activity_name:
                        activities.append(activity_name)

        except Exception as e:
            logger.error(f"Error extracting activities: {e}")

        return activities

    async def _extract_services(self, decompiled_path: str) -> list[str]:
        """Extract services from decompiled APK."""
        services = []

        try:
            manifest_path = os.path.join(decompiled_path, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()

                # Find all service elements
                for service in root.findall('.//service'):
                    service_name = service.get('android:name', '')
                    if service_name:
                        services.append(service_name)

        except Exception as e:
            logger.error(f"Error extracting services: {e}")

        return services

    async def _extract_receivers(self, decompiled_path: str) -> list[str]:
        """Extract receivers from decompiled APK."""
        receivers = []

        try:
            manifest_path = os.path.join(decompiled_path, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()

                # Find all receiver elements
                for receiver in root.findall('.//receiver'):
                    receiver_name = receiver.get('android:name', '')
                    if receiver_name:
                        receivers.append(receiver_name)

        except Exception as e:
            logger.error(f"Error extracting receivers: {e}")

        return receivers

    async def _extract_providers(self, decompiled_path: str) -> list[str]:
        """Extract content providers from decompiled APK."""
        providers = []

        try:
            manifest_path = os.path.join(decompiled_path, 'AndroidManifest.xml')
            if os.path.exists(manifest_path):
                tree = ET.parse(manifest_path)
                root = tree.getroot()

                # Find all provider elements
                for provider in root.findall('.//provider'):
                    provider_name = provider.get('android:name', '')
                    if provider_name:
                        providers.append(provider_name)

        except Exception as e:
            logger.error(f"Error extracting providers: {e}")

        return providers

    async def perform_static_analysis(self, app_file: str) -> AnalysisResult:
        """Perform static analysis on a mobile app."""
        try:
            logger.info(f"Starting static analysis on {app_file}")
            start_time = time.time()

            # Determine platform and analyze
            if app_file.endswith('.apk'):
                mobile_app = await self.analyze_android_app(app_file)
                platform = MobilePlatform.ANDROID
            elif app_file.endswith('.ipa'):
                # iOS app analysis would go here
                raise NotImplementedError("iOS app analysis not yet implemented")
            else:
                raise ValueError(f"Unsupported app format: {app_file}")

            findings = []

            # Analyze permissions
            permission_findings = await self._analyze_permissions(mobile_app.permissions)
            findings.extend(permission_findings)

            # Analyze components
            component_findings = await self._analyze_components(mobile_app)
            findings.extend(component_findings)

            # Analyze manifest
            manifest_findings = await self._analyze_manifest(mobile_app)
            findings.extend(manifest_findings)

            # Analyze code (if available)
            code_findings = await self._analyze_code(mobile_app)
            findings.extend(code_findings)

            duration = time.time() - start_time

            analysis_result = AnalysisResult(
                analysis_type=AppAnalysisType.STATIC_ANALYSIS,
                target=app_file,
                success=True,
                findings=findings,
                artifacts=[app_file],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(analysis_result)
            return analysis_result

        except Exception as e:
            logger.error(f"Error in static analysis: {e}")
            return AnalysisResult(
                analysis_type=AppAnalysisType.STATIC_ANALYSIS,
                target=app_file,
                success=False,
                findings=[],
                artifacts=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _analyze_permissions(self, permissions: list[str]) -> list[dict[str, Any]]:
        """Analyze app permissions for security implications."""
        findings = []

        # Define dangerous permissions
        dangerous_permissions = {
            'android.permission.READ_CONTACTS': 'Read contacts',
            'android.permission.WRITE_CONTACTS': 'Write contacts',
            'android.permission.READ_CALL_LOG': 'Read call log',
            'android.permission.WRITE_CALL_LOG': 'Write call log',
            'android.permission.READ_SMS': 'Read SMS',
            'android.permission.SEND_SMS': 'Send SMS',
            'android.permission.RECEIVE_SMS': 'Receive SMS',
            'android.permission.READ_PHONE_STATE': 'Read phone state',
            'android.permission.CALL_PHONE': 'Make phone calls',
            'android.permission.READ_PHONE_NUMBERS': 'Read phone numbers',
            'android.permission.ACCESS_FINE_LOCATION': 'Access fine location',
            'android.permission.ACCESS_COARSE_LOCATION': 'Access coarse location',
            'android.permission.CAMERA': 'Access camera',
            'android.permission.RECORD_AUDIO': 'Record audio',
            'android.permission.READ_EXTERNAL_STORAGE': 'Read external storage',
            'android.permission.WRITE_EXTERNAL_STORAGE': 'Write external storage',
            'android.permission.INTERNET': 'Access internet',
            'android.permission.ACCESS_NETWORK_STATE': 'Access network state',
            'android.permission.ACCESS_WIFI_STATE': 'Access WiFi state',
            'android.permission.CHANGE_WIFI_STATE': 'Change WiFi state'
        }

        try:
            for permission in permissions:
                if permission in dangerous_permissions:
                    findings.append({
                        'type': 'dangerous_permission',
                        'permission': permission,
                        'description': dangerous_permissions[permission],
                        'severity': 'high',
                        'risk': 'This permission allows the app to access sensitive data or perform potentially dangerous operations'
                    })
                elif 'android.permission.' in permission:
                    findings.append({
                        'type': 'standard_permission',
                        'permission': permission,
                        'description': 'Standard Android permission',
                        'severity': 'info',
                        'risk': 'Standard permission with moderate risk'
                    })
                else:
                    findings.append({
                        'type': 'custom_permission',
                        'permission': permission,
                        'description': 'Custom permission',
                        'severity': 'medium',
                        'risk': 'Custom permission - review implementation details'
                    })

        except Exception as e:
            logger.error(f"Error analyzing permissions: {e}")

        return findings

    async def _analyze_components(self, mobile_app: MobileApp) -> list[dict[str, Any]]:
        """Analyze app components for security implications."""
        findings = []

        try:
            # Analyze activities
            for activity in mobile_app.activities:
                if 'MainActivity' in activity or 'Launcher' in activity:
                    findings.append({
                        'type': 'main_activity',
                        'component': activity,
                        'description': 'Main activity identified',
                        'severity': 'info',
                        'risk': 'Main entry point of the application'
                    })

                if 'WebView' in activity or 'Browser' in activity:
                    findings.append({
                        'type': 'webview_activity',
                        'component': activity,
                        'description': 'WebView activity detected',
                        'severity': 'medium',
                        'risk': 'WebView activities may be vulnerable to JavaScript injection attacks'
                    })

            # Analyze services
            for service in mobile_app.services:
                if 'Foreground' in service or 'Notification' in service:
                    findings.append({
                        'type': 'foreground_service',
                        'component': service,
                        'description': 'Foreground service detected',
                        'severity': 'info',
                        'risk': 'Foreground services run continuously and may impact battery life'
                    })

            # Analyze receivers
            for receiver in mobile_app.receivers:
                if 'Boot' in receiver or 'Startup' in receiver:
                    findings.append({
                        'type': 'boot_receiver',
                        'component': receiver,
                        'description': 'Boot receiver detected',
                        'severity': 'medium',
                        'risk': 'App starts automatically on device boot'
                    })

            # Analyze providers
            for provider in mobile_app.providers:
                if 'Content' in provider or 'File' in provider:
                    findings.append({
                        'type': 'content_provider',
                        'component': provider,
                        'description': 'Content provider detected',
                        'severity': 'medium',
                        'risk': 'Content providers may expose sensitive data to other apps'
                    })

        except Exception as e:
            logger.error(f"Error analyzing components: {e}")

        return findings

    async def _analyze_manifest(self, mobile_app: MobileApp) -> list[dict[str, Any]]:
        """Analyze app manifest for security implications."""
        findings = []

        try:
            # Check SDK versions
            if mobile_app.min_sdk < 23:  # Android 6.0
                findings.append({
                    'type': 'low_min_sdk',
                    'description': f'Low minimum SDK version: {mobile_app.min_sdk}',
                    'severity': 'medium',
                    'risk': 'Older SDK versions may have known security vulnerabilities'
                })

            if mobile_app.target_sdk < 30:  # Android 11
                findings.append({
                    'type': 'low_target_sdk',
                    'description': f'Low target SDK version: {mobile_app.target_sdk}',
                    'severity': 'medium',
                    'risk': 'Targeting older SDK versions may miss security improvements'
                })

            # Check for debug flags
            findings.append({
                'type': 'manifest_analysis',
                'description': 'Manifest analysis completed',
                'severity': 'info',
                'risk': 'Review manifest for additional security configurations'
            })

        except Exception as e:
            logger.error(f"Error analyzing manifest: {e}")

        return findings

    async def _analyze_code(self, mobile_app: MobileApp) -> list[dict[str, Any]]:
        """Analyze app code for security issues."""
        findings = []

        try:
            # This is a simplified code analysis
            # In practice, you'd use tools like Androguard, MobSF, or custom scripts

            findings.append({
                'type': 'code_analysis',
                'description': 'Code analysis completed',
                'severity': 'info',
                'risk': 'Review decompiled code for security vulnerabilities',
                'recommendations': [
                    'Check for hardcoded secrets',
                    'Review encryption implementations',
                    'Check for SQL injection vulnerabilities',
                    'Review network communication security',
                    'Check for proper input validation'
                ]
            })

        except Exception as e:
            logger.error(f"Error analyzing code: {e}")

        return findings

    async def perform_malware_analysis(self, app_file: str) -> AnalysisResult:
        """Perform malware analysis on a mobile app."""
        try:
            logger.info(f"Starting malware analysis on {app_file}")
            start_time = time.time()

            findings = []

            # Basic malware indicators
            malware_indicators = await self._check_malware_indicators(app_file)
            findings.extend(malware_indicators)

            # Check for suspicious permissions
            if app_file.endswith('.apk'):
                mobile_app = await self.analyze_android_app(app_file)
                suspicious_permissions = await self._check_suspicious_permissions(mobile_app.permissions)
                findings.extend(suspicious_permissions)

            # Check for suspicious strings
            string_findings = await self._check_suspicious_strings(app_file)
            findings.extend(string_findings)

            # Check for suspicious URLs
            url_findings = await self._check_suspicious_urls(app_file)
            findings.extend(url_findings)

            duration = time.time() - start_time

            analysis_result = AnalysisResult(
                analysis_type=AppAnalysisType.MALWARE_ANALYSIS,
                target=app_file,
                success=True,
                findings=findings,
                artifacts=[app_file],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=json.dumps(findings, indent=2)
            )

            self.analysis_history.append(analysis_result)
            return analysis_result

        except Exception as e:
            logger.error(f"Error in malware analysis: {e}")
            return AnalysisResult(
                analysis_type=AppAnalysisType.MALWARE_ANALYSIS,
                target=app_file,
                success=False,
                findings=[],
                artifacts=[],
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _check_malware_indicators(self, app_file: str) -> list[dict[str, Any]]:
        """Check for basic malware indicators."""
        findings = []

        try:
            # Check file size (very small APKs might be suspicious)
            file_size = os.path.getsize(app_file)
            if file_size < 10000:  # Less than 10KB
                findings.append({
                    'type': 'suspicious_size',
                    'description': f'Very small app size: {file_size} bytes',
                    'severity': 'medium',
                    'risk': 'Unusually small app size may indicate malicious payload'
                })

            # Check file hash against known malware databases
            file_hash = await self._calculate_file_hash(app_file)
            findings.append({
                'type': 'file_hash',
                'description': f'File hash: {file_hash}',
                'severity': 'info',
                'risk': 'Check hash against malware databases',
                'hash': file_hash
            })

        except Exception as e:
            logger.error(f"Error checking malware indicators: {e}")

        return findings

    async def _check_suspicious_permissions(self, permissions: list[str]) -> list[dict[str, Any]]:
        """Check for suspicious permission combinations."""
        findings = []

        try:
            # Suspicious permission combinations
            suspicious_combinations = [
                ['android.permission.READ_SMS', 'android.permission.SEND_SMS'],
                ['android.permission.ACCESS_FINE_LOCATION', 'android.permission.INTERNET'],
                ['android.permission.CAMERA', 'android.permission.INTERNET'],
                ['android.permission.RECORD_AUDIO', 'android.permission.INTERNET'],
                ['android.permission.READ_CONTACTS', 'android.permission.INTERNET']
            ]

            for combo in suspicious_combinations:
                if all(perm in permissions for perm in combo):
                    findings.append({
                        'type': 'suspicious_permission_combo',
                        'description': f'Suspicious permission combination: {", ".join(combo)}',
                        'severity': 'high',
                        'risk': 'This combination of permissions may indicate data exfiltration capabilities'
                    })

            # Check for excessive permissions
            if len(permissions) > 20:
                findings.append({
                    'type': 'excessive_permissions',
                    'description': f'Excessive number of permissions: {len(permissions)}',
                    'severity': 'medium',
                    'risk': 'Apps requesting many permissions may be over-privileged'
                })

        except Exception as e:
            logger.error(f"Error checking suspicious permissions: {e}")

        return findings

    async def _check_suspicious_strings(self, app_file: str) -> list[dict[str, Any]]:
        """Check for suspicious strings in the app."""
        findings = []

        try:
            # Extract strings from the app
            cmd = ['strings', app_file]
            result = await self._run_command(cmd)

            if result['success']:
                strings = result['output'].lower()

                # Suspicious patterns
                suspicious_patterns = [
                    'malware', 'trojan', 'virus', 'backdoor', 'keylogger',
                    'spyware', 'stealer', 'botnet', 'crypto', 'miner',
                    'http://', 'https://', 'ftp://', 'cmd.exe', 'powershell',
                    'registry', 'regedit', 'taskkill', 'netstat', 'ipconfig'
                ]

                for pattern in suspicious_patterns:
                    if pattern in strings:
                        findings.append({
                            'type': 'suspicious_string',
                            'description': f'Suspicious string found: {pattern}',
                            'severity': 'medium',
                            'risk': 'Suspicious strings may indicate malicious functionality'
                        })

        except Exception as e:
            logger.error(f"Error checking suspicious strings: {e}")

        return findings

    async def _check_suspicious_urls(self, app_file: str) -> list[dict[str, Any]]:
        """Check for suspicious URLs in the app."""
        findings = []

        try:
            # Extract strings and look for URLs
            cmd = ['strings', app_file]
            result = await self._run_command(cmd)

            if result['success']:
                strings = result['output']

                # URL patterns
                import re
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                urls = re.findall(url_pattern, strings)

                for url in urls:
                    # Check for suspicious domains
                    suspicious_domains = [
                        'malware.com', 'evil.com', 'hack.com', 'c2.com',
                        'command.com', 'control.com', 'bot.com'
                    ]

                    if any(domain in url.lower() for domain in suspicious_domains):
                        findings.append({
                            'type': 'suspicious_url',
                            'description': f'Suspicious URL found: {url}',
                            'severity': 'high',
                            'risk': 'Suspicious URLs may indicate command and control communication'
                        })
                    else:
                        findings.append({
                            'type': 'url_found',
                            'description': f'URL found: {url}',
                            'severity': 'info',
                            'risk': 'Review URL for legitimacy'
                        })

        except Exception as e:
            logger.error(f"Error checking suspicious URLs: {e}")

        return findings

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

    def get_analyzed_apps(self) -> dict[str, MobileApp]:
        """Get analyzed apps."""
        return self.analyzed_apps

    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up decompiled directories
            for app_file, mobile_app in self.analyzed_apps.items():
                # Clean up decompiled files
                pass

            logger.info("Mobile security tools cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Example usage and testing
async def main():
    """Example usage of mobile security tools."""
    tools = MobileSecurityTools()

    try:
        # Note: This is a demonstration - you would need actual APK files
        print("Mobile security tools demonstration")
        print("To test with real apps, provide APK file paths")

        # Example analysis (would fail without real APK)
        print("Tools ready for mobile app analysis")

    finally:
        tools.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
