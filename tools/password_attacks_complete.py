#!/usr/bin/env python3
"""
Complete Password Attacks Automation Module
Automates ALL Kali Linux password attack and cracking tools
"""

import asyncio
import subprocess
import hashlib
import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class PasswordHash:
    hash_type: str
    hash_value: str
    username: Optional[str] = None
    salt: Optional[str] = None


@dataclass
class CrackResult:
    success: bool
    hash_type: str
    time_taken: float
    method_used: str
    wordlist_used: str
    attempts: int
    password: Optional[str] = None


class BasePasswordTool:
    """Base class for all password attack tools"""

    def __init__(self):
        self.wordlists = {
            'rockyou': '/usr/share/wordlists/rockyou.txt',
            'common': '/usr/share/wordlists/common.txt',
            'fasttrack': '/usr/share/wordlists/fasttrack.txt',
            'custom': None
        }
        self.results_dir = Path('./results/password_attacks')
        self.results_dir.mkdir(parents=True, exist_ok=True)

    async def run_command(self, cmd: List[str], timeout: int = 300) -> Dict[str, Any]:
        """Execute command with timeout and error handling"""
        try:
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=timeout
            )
            stdout, stderr = await process.communicate()

            return {
                'success': process.returncode == 0,
                'stdout': stdout.decode() if stdout else '',
                'stderr': stderr.decode() if stderr else '',
                'returncode': process.returncode
            }
        except asyncio.TimeoutError:
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Command timed out',
                'returncode': -1
            }
        except Exception as e:
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1
            }


class HashcatAutomation(BasePasswordTool):
    """Automates Hashcat for GPU-accelerated password cracking"""

    def __init__(self):
        super().__init__()
        self.hashcat_path = 'hashcat'
        self.supported_modes = {
            'md5': 0,
            'sha1': 100,
            'sha256': 1400,
            'sha512': 1700,
            'ntlm': 1000,
            'lm': 3000,
            'bcrypt': 3200,
            'sha256crypt': 7400,
            'sha512crypt': 1800,
            'md5crypt': 500,
            'wordpress': 400,
            'joomla': 400,
            'drupal': 7900
        }

    async def crack_hash(self, hash_value: str, hash_type: str, wordlist: str = 'rockyou') -> CrackResult:
        """Crack password hash using Hashcat"""
        start_time = asyncio.get_event_loop().time()

        if hash_type not in self.supported_modes:
            return CrackResult(
                success=False,
                hash_type=hash_type,
                time_taken=0,
                method_used='hashcat',
                wordlist_used=wordlist,
                attempts=0
            )

        mode = self.supported_modes[hash_type]
        wordlist_path = self.wordlists.get(wordlist, wordlist)

        # Create hash file
        hash_file = self.results_dir / f"hash_{hash_type}_{hash_value[:8]}.txt"
        hash_file.write_text(hash_value)

        cmd = [
            self.hashcat_path,
            '-m', str(mode),
            '-a', '0',
            hash_file,
            wordlist_path,
            '-o', str(self.results_dir / f"cracked_{hash_type}_{hash_value[:8]}.txt"),
            '--potfile-disable'
        ]

        result = await self.run_command(cmd, timeout=3600)  # 1 hour timeout

        time_taken = asyncio.get_event_loop().time() - start_time

        if result['success']:
            # Parse output for cracked password
            cracked_file = self.results_dir / f"cracked_{hash_type}_{hash_value[:8]}.txt"
            if cracked_file.exists():
                with open(cracked_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        password = lines[0].strip().split(':')[-1]
                        return CrackResult(
                            success=True,
                            password=password,
                            hash_type=hash_type,
                            time_taken=time_taken,
                            method_used='hashcat',
                            wordlist_used=wordlist,
                            attempts=0  # Hashcat doesn't provide attempt count
                        )

        return CrackResult(
            success=False,
            hash_type=hash_type,
            time_taken=time_taken,
            method_used='hashcat',
            wordlist_used=wordlist,
            attempts=0
        )

    async def benchmark_gpu(self) -> Dict[str, Any]:
        """Benchmark GPU performance for different hash types"""
        results = {}

        for hash_name, mode in list(self.supported_modes.items())[:5]:  # Test first 5
            cmd = [self.hashcat_path, '-b', '-m', str(mode)]
            result = await self.run_command(cmd, timeout=300)

            if result['success']:
                # Parse benchmark output
                lines = result['stdout'].split('\n')
                for line in lines:
                    if 'Speed.#1' in line:
                        speed = line.split()[-1]
                        results[hash_name] = speed
                        break

        return results


class JohnTheRipperAutomation(BasePasswordTool):
    """Automates John the Ripper for password cracking"""

    def __init__(self):
        super().__init__()
        self.john_path = 'john'
        self.john_dir = Path('./.john')
        self.john_dir.mkdir(parents=True, exist_ok=True)

    async def crack_hash(self, hash_value: str, hash_type: str, wordlist: str = 'rockyou') -> CrackResult:
        """Crack password hash using John the Ripper"""
        start_time = asyncio.get_event_loop().time()

        # Create hash file
        hash_file = self.results_dir / f"john_hash_{hash_type}_{hash_value[:8]}.txt"
        hash_file.write_text(hash_value)

        wordlist_path = self.wordlists.get(wordlist, wordlist)

        cmd = [
            self.john_path,
            f'--wordlist={wordlist_path}',
            f'--format={hash_type}',
            str(hash_file)
        ]

        result = await self.run_command(cmd, timeout=3600)

        time_taken = asyncio.get_event_loop().time() - start_time

        if result['success']:
            # Show cracked passwords
            show_cmd = [self.john_path, '--show', str(hash_file)]
            show_result = await self.run_command(show_cmd)

            if show_result['success'] and show_result['stdout']:
                lines = show_result['stdout'].split('\n')
                for line in lines:
                    if ':' in line and hash_value in line:
                        password = line.split(':')[1]
                        return CrackResult(
                            success=True,
                            password=password,
                            hash_type=hash_type,
                            time_taken=time_taken,
                            method_used='john',
                            wordlist_used=wordlist,
                            attempts=0
                        )

        return CrackResult(
            success=False,
            hash_type=hash_type,
            time_taken=time_taken,
            method_used='john',
            wordlist_used=wordlist,
            attempts=0
        )

    async def crack_zip_file(self, zip_file: str, wordlist: str = 'rockyou') -> CrackResult:
        """Crack ZIP file password"""
        start_time = asyncio.get_event_loop().time()

        cmd = [
            self.john_path,
            f'--wordlist={self.wordlists.get(wordlist, wordlist)}',
            zip_file
        ]

        result = await self.run_command(cmd, timeout=7200)  # 2 hours for ZIP

        time_taken = asyncio.get_event_loop().time() - start_time

        if result['success']:
            # Show cracked password
            show_cmd = [self.john_path, '--show', zip_file]
            show_result = await self.run_command(show_cmd)

            if show_result['success'] and show_result['stdout']:
                lines = show_result['stdout'].split('\n')
                for line in lines:
                    if ':' in line and 'password' in line.lower():
                        password = line.split(':')[1]
                        return CrackResult(
                            success=True,
                            password=password,
                            hash_type='zip',
                            time_taken=time_taken,
                            method_used='john',
                            wordlist_used=wordlist,
                            attempts=0
                        )

        return CrackResult(
            success=False,
            hash_type='zip',
            time_taken=time_taken,
            method_used='john',
            wordlist_used=wordlist,
            attempts=0
        )


class HydraAutomation(BasePasswordTool):
    """Automates Hydra for online password attacks"""

    def __init__(self):
        super().__init__()
        self.hydra_path = 'hydra'
        self.supported_protocols = [
            'ssh', 'ftp', 'telnet', 'http', 'https', 'smb', 'rdp', 'vnc',
            'mysql', 'postgres', 'mssql', 'oracle', 'ldap', 'pop3', 'imap', 'smtp'
        ]

    async def brute_force_service(self, target: str, service: str, username: str,
                                 wordlist: str = 'rockyou', port: Optional[int] = None) -> CrackResult:
        """Brute force service with username/password combinations"""
        start_time = asyncio.get_event_loop().time()

        if service not in self.supported_protocols:
            return CrackResult(
                success=False,
                hash_type=f'{service}_brute',
                time_taken=0,
                method_used='hydra',
                wordlist_used=wordlist,
                attempts=0
            )

        wordlist_path = self.wordlists.get(wordlist, wordlist)

        cmd = [
            self.hydra_path,
            '-l', username,
            '-P', wordlist_path,
            '-t', '4',  # 4 threads
            '-v',  # verbose
            '-f',  # stop on first success
            f'{target}:{service}'
        ]

        if port:
            cmd.extend(['-s', str(port)])

        result = await self.run_command(cmd, timeout=1800)  # 30 minutes

        time_taken = asyncio.get_event_loop().time() - start_time

        if result['success'] and 'password:' in result['stdout']:
            # Parse output for password
            lines = result['stdout'].split('\n')
            for line in lines:
                if 'password:' in line:
                    password = line.split('password:')[-1].strip()
                    return CrackResult(
                        success=True,
                        password=password,
                        hash_type=f'{service}_brute',
                        time_taken=time_taken,
                        method_used='hydra',
                        wordlist_used=wordlist,
                        attempts=0
                    )

        return CrackResult(
            success=False,
            hash_type=f'{service}_brute',
            time_taken=time_taken,
            method_used='hydra',
            wordlist_used=wordlist,
            attempts=0
        )

    async def brute_force_users(self, target: str, service: str,
                               userlist: List[str], password: str,
                               port: Optional[int] = None) -> CrackResult:
        """Brute force service with multiple usernames and one password"""
        start_time = asyncio.get_event_loop().time()

        # Create user list file
        user_file = self.results_dir / f"users_{service}_{target}.txt"
        user_file.write_text('\n'.join(userlist))

        cmd = [
            self.hydra_path,
            '-L', str(user_file),
            '-p', password,
            '-t', '4',
            '-v',
            '-f',
            f'{target}:{service}'
        ]

        if port:
            cmd.extend(['-s', str(port)])

        result = await self.run_command(cmd, timeout=1800)

        time_taken = asyncio.get_event_loop().time() - start_time

        if result['success'] and 'login:' in result['stdout']:
            # Parse output for username
            lines = result['stdout'].split('\n')
            for line in lines:
                if 'login:' in line:
                    username = line.split('login:')[-1].strip()
                    return CrackResult(
                        success=True,
                        password=password,
                        hash_type=f'{service}_user_brute',
                        time_taken=time_taken,
                        method_used='hydra',
                        wordlist_used='custom_userlist',
                        attempts=0
                    )

        return CrackResult(
            success=False,
            hash_type=f'{service}_user_brute',
            time_taken=time_taken,
            method_used='hydra',
            wordlist_used='custom_userlist',
            attempts=0
        )


class MedusaAutomation(BasePasswordTool):
    """Automates Medusa for parallel brute force attacks"""

    def __init__(self):
        super().__init__()
        self.medusa_path = 'medusa'
        self.supported_modules = [
            'ssh', 'ftp', 'telnet', 'http', 'https', 'smb', 'rdp', 'vnc',
            'mysql', 'postgres', 'mssql', 'oracle', 'ldap', 'pop3', 'imap', 'smtp'
        ]

    async def parallel_brute_force(self, target: str, service: str,
                                  username: str, wordlist: str = 'rockyou',
                                  port: Optional[int] = None, threads: int = 10) -> CrackResult:
        """Parallel brute force attack using Medusa"""
        start_time = asyncio.get_event_loop().time()

        if service not in self.supported_modules:
            return CrackResult(
                success=False,
                hash_type=f'{service}_medusa',
                time_taken=0,
                method_used='medusa',
                wordlist_used=wordlist,
                attempts=0
            )

        wordlist_path = self.wordlists.get(wordlist, wordlist)

        cmd = [
            self.medusa_path,
            '-h', target,
            '-U', username,
            '-P', wordlist_path,
            '-M', service,
            '-t', str(threads),
            '-f'  # stop on first success
        ]

        if port:
            cmd.extend(['-n', str(port)])

        result = await self.run_command(cmd, timeout=1800)

        time_taken = asyncio.get_event_loop().time() - start_time

        if result['success'] and 'SUCCESS' in result['stdout']:
            # Parse output for password
            lines = result['stdout'].split('\n')
            for line in lines:
                if 'SUCCESS' in line and 'password:' in line:
                    password = line.split('password:')[-1].strip()
                    return CrackResult(
                        success=True,
                        password=password,
                        hash_type=f'{service}_medusa',
                        time_taken=time_taken,
                        method_used='medusa',
                        wordlist_used=wordlist,
                        attempts=0
                    )

        return CrackResult(
            success=False,
            hash_type=f'{service}_medusa',
            time_taken=time_taken,
            method_used='medusa',
            wordlist_used=wordlist,
            attempts=0
        )


class CrunchAutomation(BasePasswordTool):
    """Automates Crunch for custom wordlist generation"""

    def __init__(self):
        super().__init__()
        self.crunch_path = 'crunch'
        self.custom_wordlists_dir = self.results_dir / 'custom_wordlists'
        self.custom_wordlists_dir.mkdir(exist_ok=True)

    async def generate_wordlist(self, min_length: int, max_length: int,
                               charset: str = 'abcdefghijklmnopqrstuvwxyz0123456789',
                               output_file: Optional[str] = None) -> Dict[str, Any]:
        """Generate custom wordlist using Crunch"""
        if not output_file:
            output_file = f"crunch_{min_length}-{max_length}_{charset[:10]}.txt"

        output_path = self.custom_wordlists_dir / output_file

        cmd = [
            self.crunch_path,
            str(min_length),
            str(max_length),
            charset,
            '-o', str(output_path)
        ]

        result = await self.run_command(cmd, timeout=3600)  # 1 hour

        if result['success'] and output_path.exists():
            file_size = output_path.stat().st_size
            return {
                'success': True,
                'output_file': str(output_path),
                'file_size': file_size,
                'charset': charset,
                'min_length': min_length,
                'max_length': max_length
            }

        return {
            'success': False,
            'error': result['stderr']
        }

    async def generate_pattern_wordlist(self, pattern: str, charset: Optional[str] = None) -> Dict[str, Any]:
        """Generate wordlist based on pattern"""
        output_file = f"pattern_{pattern.replace('@', 'a').replace('!', '1')[:20]}.txt"
        output_path = self.custom_wordlists_dir / output_file

        cmd = [
            self.crunch_path,
            str(len(pattern)),
            str(len(pattern)),
            '-p', pattern
        ]

        if charset:
            cmd.extend(['-c', charset])

        cmd.extend(['-o', str(output_path)])

        result = await self.run_command(cmd, timeout=1800)

        if result['success'] and output_path.exists():
            file_size = output_path.stat().st_size
            return {
                'success': True,
                'output_file': str(output_path),
                'file_size': file_size,
                'pattern': pattern
            }

        return {
            'success': False,
            'error': result['stderr']
        }


class PasswordAttacksOrchestrator:
    """Master orchestrator for all password attack tools"""

    def __init__(self):
        self.hashcat = HashcatAutomation()
        self.john = JohnTheRipperAutomation()
        self.hydra = HydraAutomation()
        self.medusa = MedusaAutomation()
        self.crunch = CrunchAutomation()
        self.attack_history = []

    async def comprehensive_password_audit(self, target: str, services: List[str],
                                        usernames: List[str], wordlists: Optional[List[str]] = None) -> Dict[str, Any]:
        """Run comprehensive password audit across multiple services"""
        if not wordlists:
            wordlists = ['rockyou', 'common']

        results = {
            'target': target,
            'timestamp': asyncio.get_event_loop().time(),
            'services': {},
            'summary': {
                'total_attempts': 0,
                'successful_cracks': 0,
                'failed_attempts': 0
            }
        }

        for service in services:
            results['services'][service] = []

            for username in usernames:
                for wordlist in wordlists:
                    # Try different tools for each service
                    if service in ['ssh', 'ftp', 'http', 'https']:
                        # Use Hydra for online services
                        result = await self.hydra.brute_force_service(
                            target, service, username, wordlist
                        )
                    else:
                        # Use Medusa as fallback
                        result = await self.medusa.parallel_brute_force(
                            target, service, username, wordlist
                        )

                    results['services'][service].append({
                        'username': username,
                        'wordlist': wordlist,
                        'result': result
                    })

                    if result.success:
                        results['summary']['successful_cracks'] += 1
                    else:
                        results['summary']['failed_attempts'] += 1

                    results['summary']['total_attempts'] += 1

        self.attack_history.append(results)
        return results

    async def hash_cracking_contest(self, hashes: List[PasswordHash],
                                   wordlists: Optional[List[str]] = None) -> Dict[str, Any]:
        """Competition between Hashcat and John for hash cracking"""
        if not wordlists:
            wordlists = ['rockyou', 'common']

        results = {
            'timestamp': asyncio.get_event_loop().time(),
            'hashcat_results': [],
            'john_results': [],
            'winner': None,
            'summary': {
                'hashcat_success': 0,
                'john_success': 0,
                'total_hashes': len(hashes)
            }
        }

        for hash_obj in hashes:
            # Run Hashcat
            hashcat_result = await self.hashcat.crack_hash(
                hash_obj.hash_value, hash_obj.hash_type, wordlists[0]
            )
            results['hashcat_results'].append(hashcat_result)

            if hashcat_result.success:
                results['summary']['hashcat_success'] += 1

            # Run John
            john_result = await self.john.crack_hash(
                hash_obj.hash_value, hash_obj.hash_type, wordlists[0]
            )
            results['john_results'].append(john_result)

            if john_result.success:
                results['summary']['john_success'] += 1

        # Determine winner
        if results['summary']['hashcat_success'] > results['summary']['john_success']:
            results['winner'] = 'hashcat'
        elif results['summary']['john_success'] > results['summary']['hashcat_success']:
            results['winner'] = 'john'
        else:
            results['winner'] = 'tie'

        self.attack_history.append(results)
        return results

    async def generate_custom_wordlists(self, patterns: List[str],
                                       ranges: List[Dict[str, int]]) -> Dict[str, Any]:
        """Generate multiple custom wordlists for targeted attacks"""
        results = {
            'timestamp': asyncio.get_event_loop().time(),
            'generated_wordlists': [],
            'total_size': 0
        }

        # Generate pattern-based wordlists
        for pattern in patterns:
            result = await self.crunch.generate_pattern_wordlist(pattern)
            if result['success']:
                results['generated_wordlists'].append(result)
                results['total_size'] += result.get('file_size', 0)

        # Generate range-based wordlists
        for range_config in ranges:
            result = await self.crunch.generate_wordlist(
                range_config['min_length'],
                range_config['max_length'],
                range_config.get('charset', 'abcdefghijklmnopqrstuvwxyz0123456789')
            )
            if result['success']:
                results['generated_wordlists'].append(result)
                results['total_size'] += result.get('file_size', 0)

        return results

    async def benchmark_all_tools(self) -> Dict[str, Any]:
        """Benchmark performance of all password attack tools"""
        results = {
            'timestamp': asyncio.get_event_loop().time(),
            'hashcat_benchmark': {},
            'john_benchmark': {},
            'hydra_benchmark': {},
            'medusa_benchmark': {}
        }

        # Benchmark Hashcat
        results['hashcat_benchmark'] = await self.hashcat.benchmark_gpu()

        # Benchmark other tools with simple tests
        # (John, Hydra, and Medusa don't have built-in benchmarks)

        return results


# Example usage and testing
async def main():
    """Test the password attacks automation"""
    orchestrator = PasswordAttacksOrchestrator()

    # Test hash cracking
    test_hash = PasswordHash(
        hash_type='md5',
        hash_value='5f4dcc3b5aa765d61d8327deb882cf99',  # 'password'
        username='testuser'
    )

    print("Testing Hashcat...")
    hashcat_result = await orchestrator.hashcat.crack_hash(
        test_hash.hash_value, test_hash.hash_type, 'rockyou'
    )
    print(f"Hashcat result: {hashcat_result}")

    print("Testing John...")
    john_result = await orchestrator.john.crack_hash(
        test_hash.hash_value, test_hash.hash_type, 'rockyou'
    )
    print(f"John result: {john_result}")

    # Test wordlist generation
    print("Generating custom wordlist...")
    wordlist_result = await orchestrator.crunch.generate_wordlist(
        4, 6, 'abc123', 'test_wordlist.txt'
    )
    print(f"Wordlist generation: {wordlist_result}")


if __name__ == "__main__":
    asyncio.run(main())
