import base64
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from NeoConnect.core import Controller, ConnectError, atomic_private, checked_endpoint, private_ipv4, valid_key


def key(n):
    return base64.b64encode(bytes([n]) * 32).decode()


class FakeCommands:
    def __init__(self):
        self.calls = []

    def __call__(self, args, text=None):
        self.calls.append((args, text))
        return SimpleNamespace(returncode=0, stdout=key(2) if args[-1] == 'public-key' else '')


class FakeEndpoint:
    binary = 'neoconnect-endpoint'

    def __init__(self):
        self.started = False
        self.peers = []
        self.fail_start = False

    def available(self):
        return True

    def running(self):
        return self.started

    def start(self, private_key, host, port, peers):
        self.started = True
        if self.fail_start:
            raise ConnectError('Fixture unavailable')
        self.peers = list(peers)

    def update(self, peers):
        self.peers = list(peers)

    def stop(self):
        self.started = False


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.commands = FakeCommands()
        self.endpoint = FakeEndpoint()
        self.now = 10
        self.c = Controller(self.temp.name, self.commands, clock=lambda: self.now, endpoint=self.endpoint)
        atomic_private(Path(self.temp.name) / 'server.key', key(1))
        self.c.prepare_identity = lambda: None

    def start(self):
        self.c.up('192.168.11.2', 82, 'home.example:51820', serve=False)

    def pair(self, n=3):
        return self.c.pair(self.c.new_code(), key(n), 'TV salon')

    def test_private_ipv4_is_literal_rfc1918_only(self):
        for address in ('192.168.11.2', '10.4.3.2', '172.31.255.1'):
            self.assertTrue(private_ipv4(address))
        for address in ('127.0.0.1', '100.64.1.2', '8.8.8.8', '192.168.11.2.example', '::1', '169.254.1.2'):
            self.assertFalse(private_ipv4(address))

    def test_endpoint_rejects_url_credentials_and_command_injection(self):
        for endpoint in ('home.example:51820', '1.2.3.4:1234', '[2001:db8::1]:51820'):
            self.assertEqual(endpoint, checked_endpoint(endpoint))
        for endpoint in ('https://home:443', 'user:password@home:1234', 'home:0', 'home:65536', 'home:1234/x', 'home:1234\ncommand', 'home', '[invalid]:1234'):
            with self.assertRaises(ConnectError):
                checked_endpoint(endpoint)

    def test_invalid_keys_and_tunnel_subnet_collision_rejected(self):
        self.assertFalse(valid_key(base64.b64encode(bytes(32)).decode()))
        self.assertFalse(valid_key('x' * 44))
        with self.assertRaises(ConnectError):
            self.c.configure('10.78.0.5', 82, 'home.example:51820')

    def test_lifecycle_never_changes_host_network_or_installs_packages(self):
        self.start()
        self.pair()
        self.c.down()
        self.assertFalse(any(a[0] in ('ip', 'iptables', 'modprobe', 'sysctl', 'sh', 'bash', 'opkg') for a, _ in self.commands.calls))
        self.assertFalse(self.endpoint.started)

    def test_failed_endpoint_start_is_stopped_and_not_reported_active(self):
        self.endpoint.fail_start = True
        with self.assertRaises(ConnectError):
            self.start()
        self.assertFalse(self.endpoint.started)
        self.assertFalse(self.c.active)

    def test_dead_process_never_reports_an_active_tunnel(self):
        self.start()
        self.endpoint.started = False
        self.assertFalse(self.c.active)
        with self.assertRaises(ConnectError):
            self.c.new_code()

    def test_successful_pair_consumes_code_and_never_exports_private_key(self):
        self.start()
        code = self.c.new_code()
        response = self.c.pair(code, key(3), 'TV salon')
        self.assertEqual(response['address'], '10.78.0.2/32')
        self.assertNotIn(key(1), json.dumps(response))
        self.assertNotIn('private', json.dumps(response))
        self.assertIsNone(self.c.code)
        with self.assertRaises(ConnectError):
            self.c.pair(code, key(4), 'Other TV')

    def test_expired_and_three_wrong_codes_are_invalidated(self):
        self.start()
        code = self.c.new_code()
        self.now += 121
        with self.assertRaises(ConnectError):
            self.c.pair(code, key(3), 'TV')
        code = self.c.new_code()
        wrong = '000000' if code != '000000' else '111111'
        for _ in range(3):
            with self.assertRaises(ConnectError):
                self.c.pair(wrong, key(3), 'TV')
        self.assertIsNone(self.c.code)

    def test_peer_limit_revoke_and_restart_preserve_allocations(self):
        self.start()
        for n in range(3, 11):
            self.pair(n)
        with self.assertRaises(ConnectError):
            self.pair(11)
        self.c.revoke(key(4))
        self.assertNotIn(key(4), json.dumps(self.endpoint.peers))
        self.assertEqual(self.pair(11)['address'], '10.78.0.3/32')
        restored = Controller(self.temp.name, self.commands, endpoint=FakeEndpoint())
        self.assertEqual(len(restored.peers), 8)
        self.assertFalse(restored.active)

    def test_storage_failure_rolls_back_runtime_peer_without_consuming_code(self):
        self.start()
        code = self.c.new_code()
        with patch('NeoConnect.core.atomic_private', side_effect=OSError):
            with self.assertRaises(ConnectError):
                self.c.pair(code, key(3), 'TV')
        self.assertEqual(self.endpoint.peers, [])
        self.assertEqual(self.c.code, code)

    def test_concurrent_requests_cannot_reuse_one_code(self):
        self.start()
        code = self.c.new_code()
        def attempt(n):
            try:
                self.c.pair(code, key(n), 'TV')
                return True
            except ConnectError:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sum(pool.map(attempt, (3, 4))), 1)
        self.assertEqual(len(self.c.peers), 1)

    @unittest.skipIf(os.name == 'nt', 'POSIX mode bits checked by Linux CI')
    def test_private_files_have_no_group_or_world_access(self):
        self.start()
        self.pair()
        self.assertEqual(stat.S_IMODE((Path(self.temp.name) / 'peers.json').stat().st_mode), 0o600)


if __name__ == '__main__':
    unittest.main()
