import base64
import hashlib
import http.client
import json
from pathlib import Path
import shutil
import ssl
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from NeoConnect.core import Controller, atomic_private
from NeoConnect.pairing import PairingServer
from test_core import FakeCommands, FakeEndpoint, key

OPENSSL = shutil.which('openssl')
if OPENSSL is None and Path('C:/Program Files/Git/usr/bin/openssl.exe').exists():
    OPENSSL = 'C:/Program Files/Git/usr/bin/openssl.exe'


@unittest.skipUnless(OPENSSL, 'TLS fixture requires OpenSSL; available on Linux CI')
class HttpsPairingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        r = subprocess.run([OPENSSL, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-days', '1',
            '-subj', '/CN=NeoConnect', '-keyout', str(cls.root / 'pairing.key'), '-out', str(cls.root / 'pairing.crt')],
            capture_output=True, timeout=30)
        if r.returncode:
            raise RuntimeError('TLS fixture generation failed')
        atomic_private(cls.root / 'server.key', key(1))

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        endpoint = FakeEndpoint()
        endpoint.started = True
        self.c = Controller(self.root, FakeCommands(), endpoint=endpoint)
        self.c.PAIR_PORT = 0
        self.c.active = True
        self.c.configure('192.168.11.2', 82, 'home.example:51820')
        self.server = PairingServer(self.c, '127.0.0.1')
        self.server.start()
        self.addCleanup(self.server.close)
        self.port = self.server.server.server_address[1]
        self.context = ssl.create_default_context(cafile=str(self.root / 'pairing.crt'))
        self.context.check_hostname = False  # Fixture uses loopback rather than the receiver's LAN IP.

    def request(self, payload, allowed=True, path='/pair'):
        with patch('NeoConnect.pairing.private_ipv4', return_value=allowed):
            connection = http.client.HTTPSConnection('127.0.0.1', self.port, context=self.context, timeout=5)
            try:
                connection.request('POST', path, body=json.dumps(payload), headers={'Content-Type': 'application/json'})
                response = connection.getresponse()
                return response.status, json.loads(response.read())
            finally:
                connection.close()

    def test_real_tls_certificate_matches_displayed_fingerprint(self):
        import socket
        with socket.create_connection(('127.0.0.1', self.port), timeout=5) as raw:
            with self.context.wrap_socket(raw, server_hostname='NeoConnect') as secure:
                self.assertEqual(hashlib.sha256(secure.getpeercert(binary_form=True)).hexdigest().upper(), self.c.fingerprint())

    def test_real_https_pair_does_not_return_private_key_and_replay_fails(self):
        payload = {'code': self.c.new_code(), 'public_key': key(4), 'name': 'TLS test TV'}
        status, response = self.request(payload)
        self.assertEqual(status, 200)
        self.assertEqual(response['receiver_port'], 82)
        self.assertNotIn(key(1), json.dumps(response))
        self.assertEqual(self.request(payload)[0], 401)

    def test_source_outside_private_network_is_denied(self):
        self.assertEqual(self.request({'code': self.c.new_code()}, allowed=False)[0], 403)

    def test_non_pair_routes_and_oversized_requests_denied(self):
        self.assertEqual(self.request({}, path='/api/zap')[0], 400)
        self.assertEqual(self.request({'data': 'x' * 5000})[0], 400)


if __name__ == '__main__':
    unittest.main()
