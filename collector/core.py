from __future__ import annotations
import json
import os
import platform
import re
import shlex
import socket
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

TIMEOUT = 8
MAX_OUTPUT = 20000

@dataclass(frozen=True)
class Cmd:
    name: str
    argv: tuple[str, ...]
    timeout: int = TIMEOUT


def run_cmd(cmd: Cmd) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        p = subprocess.run(
            list(cmd.argv),
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=cmd.timeout,
            shell=False,
            check=False,
        )
        return {
            'name': cmd.name,
            'argv': list(cmd.argv),
            'returncode': p.returncode,
            'stdout': p.stdout[-MAX_OUTPUT:],
            'stderr': p.stderr[-MAX_OUTPUT:],
            'duration_ms': round((time.perf_counter() - started) * 1000, 1),
        }
    except FileNotFoundError:
        return {'name': cmd.name, 'argv': list(cmd.argv), 'returncode': -127, 'stdout': '', 'stderr': 'command not found', 'duration_ms': round((time.perf_counter() - started) * 1000, 1)}
    except subprocess.TimeoutExpired as exc:
        return {'name': cmd.name, 'argv': list(cmd.argv), 'returncode': -124, 'stdout': (exc.stdout or '')[-MAX_OUTPUT:] if isinstance(exc.stdout, str) else '', 'stderr': 'timeout', 'duration_ms': round((time.perf_counter() - started) * 1000, 1)}


def which(name: str) -> str | None:
    import shutil
    return shutil.which(name)


def platform_family() -> str:
    s = platform.system().lower()
    if s == 'windows': return 'Windows'
    if s == 'darwin': return 'macOS'
    if s == 'linux':
        if 'android' in platform.platform().lower() or os.environ.get('ANDROID_ROOT'):
            return 'Android'
        return 'Linux'
    return s.title()


def commands_for_os() -> list[Cmd]:
    osname = platform_family()
    if osname == 'Windows':
        return [
            Cmd('hostname', ('hostname',)),
            Cmd('ipconfig_all', ('ipconfig', '/all')),
            Cmd('route_print', ('route', 'print')),
            Cmd('arp', ('arp', '-a')),
            Cmd('netstat', ('netstat', '-ano')),
            Cmd('wifi_interfaces', ('netsh', 'wlan', 'show', 'interfaces')),
            Cmd('wifi_profiles', ('netsh', 'wlan', 'show', 'profiles')),
            Cmd('dns_cache', ('ipconfig', '/displaydns')),
            Cmd('net_statistics_workstation', ('net', 'statistics', 'workstation')),
        ]
    if osname == 'macOS':
        airport = '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport'
        cmds = [
            Cmd('hostname', ('hostname',)),
            Cmd('ifconfig', ('ifconfig',)),
            Cmd('route', ('route', '-n', 'get', 'default')),
            Cmd('netstat_routes', ('netstat', '-rn')),
            Cmd('arp', ('arp', '-an')),
            Cmd('netstat', ('netstat', '-anv')),
            Cmd('lsof_tcp_listen', ('lsof', '-nP', '-iTCP', '-sTCP:LISTEN')),
            Cmd('scutil_dns', ('scutil', '--dns')),
            Cmd('networksetup_ports', ('networksetup', '-listallhardwareports')),
            Cmd('networksetup_wifi', ('networksetup', '-getinfo', 'Wi-Fi')),
            Cmd('wifi_info', (airport, '-I')),
        ]
        return cmds
    return [
        Cmd('hostname', ('hostname',)),
        Cmd('ip_addr', ('ip', 'addr')),
        Cmd('ip_link', ('ip', '-details', 'link')),
        Cmd('ip_route', ('ip', 'route')),
        Cmd('ip_neigh', ('ip', 'neigh')),
        Cmd('ss_all', ('ss', '-tulpen')),
        Cmd('ss_tcp', ('ss', '-tanp')),
        Cmd('resolvectl', ('resolvectl', 'status')),
        Cmd('nmcli_status', ('nmcli', 'device', 'status')),
        Cmd('nmcli_connections', ('nmcli', 'connection', 'show')),
        Cmd('nmcli_wifi', ('nmcli', 'device', 'wifi', 'list')),
        Cmd('ufw', ('ufw', 'status', 'verbose')),
    ]


def collect_local() -> dict[str, Any]:
    results = [run_cmd(c) for c in commands_for_os()]
    return {
        'schema': 'nethack.report.v1',
        'collected_at': datetime.now(timezone.utc).isoformat(),
        'platform': platform_family(),
        'hostname': socket.gethostname(),
        'python': platform.python_version(),
        'system': platform.platform(),
        'commands': results,
    }


def validate_target(target: str) -> str:
    t = target.strip()
    if not t or len(t) > 255 or any(ch in t for ch in '\r\n'):
        raise ValueError('Invalid target')
    if re.fullmatch(r'[A-Za-z0-9.:%_\-\[\]]+', t) is None:
        # Permit normal DNS names and IP literals; reject shell metacharacters.
        raise ValueError('Target contains unsupported characters')
    return t


def target_probe(target: str, port: int | None = None) -> dict[str, Any]:
    target = validate_target(target)
    out: dict[str, Any] = {'target': target, 'timestamp': datetime.now(timezone.utc).isoformat()}
    try:
        infos = socket.getaddrinfo(target, None, type=socket.SOCK_STREAM)
        addrs = sorted({x[4][0] for x in infos})
        out['resolved_ips'] = addrs
    except OSError as e:
        out['resolved_ips'] = []
        out['dns_error'] = str(e)
        addrs = []

    try:
        reverse = socket.gethostbyaddr(target)[0]
        out['reverse_dns'] = reverse
    except OSError:
        if addrs:
            try:
                out['reverse_dns'] = socket.gethostbyaddr(addrs[0])[0]
            except OSError:
                out['reverse_dns'] = None
        else:
            out['reverse_dns'] = None

    if port is not None:
        if not 1 <= int(port) <= 65535:
            raise ValueError('Port must be 1..65535')
        started = time.perf_counter()
        try:
            with socket.create_connection((target, int(port)), timeout=3):
                out['tcp'] = {'port': int(port), 'reachable': True, 'duration_ms': round((time.perf_counter()-started)*1000, 2)}
        except OSError as e:
            out['tcp'] = {'port': int(port), 'reachable': False, 'error': str(e), 'duration_ms': round((time.perf_counter()-started)*1000, 2)}
    return out


def ping_probe(target: str, count: int = 4) -> dict[str, Any]:
    target = validate_target(target)
    count = max(1, min(10, int(count)))
    if platform_family() == 'Windows':
        cmd = Cmd('target_ping', ('ping', '-n', str(count), target), timeout=20)
    else:
        cmd = Cmd('target_ping', ('ping', '-c', str(count), target), timeout=20)
    return run_cmd(cmd)


def trace_probe(target: str) -> dict[str, Any]:
    target = validate_target(target)
    osname = platform_family()
    if osname == 'Windows':
        return run_cmd(Cmd('target_tracert', ('tracert', '-d', '-h', '16', target), timeout=35))
    traceroute = which('traceroute') or which('tracepath')
    if traceroute:
        if traceroute.endswith('tracepath'):
            return run_cmd(Cmd('target_tracepath', (traceroute, '-m', '16', target), timeout=35))
        return run_cmd(Cmd('target_traceroute', (traceroute, '-n', '-m', '16', target), timeout=35))
    return {'name': 'target_traceroute', 'argv': [], 'returncode': -127, 'stdout': '', 'stderr': 'traceroute/tracepath not installed', 'duration_ms': 0}


def full_report(target: str | None = None, port: int | None = None) -> dict[str, Any]:
    report = collect_local()
    if target:
        report['target'] = target_probe(target, port)
        report['ping'] = ping_probe(target)
        report['trace'] = trace_probe(target)
    return report
