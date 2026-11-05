"""Neo Connect receiver controller. No OpenWebif credentials or generic shell API.

The endpoint starts only after explicit activation in the receiver UI. This
module can be tested outside Enigma2 using an injected command runner.
"""
import base64
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import ssl
import subprocess
import threading
import time
from urllib.parse import urlsplit


class ConnectError(Exception):
    """Fixed user-facing message; never wrap raw subprocess output or secrets."""


def private_ipv4(value):
    try:
        address = ipaddress.IPv4Address(value)
    except ValueError:
        return False
    return any(address in ipaddress.IPv4Network(n) for n in
               ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'))


def valid_key(value):
    try:
        raw = base64.b64decode(value, validate=True)
        return len(raw) == 32 and any(raw) and base64.b64encode(raw).decode() == value
    except (ValueError, TypeError):
        return False


def checked_endpoint(value):
    if not isinstance(value, str) or len(value) > 260 or re.search(r'[\s/\\?#@]', value):
        raise ConnectError('Adresse Internet invalide : hote:port ou [IPv6]:port.')
    try:
        parts = urlsplit('//' + value)
        host, port = parts.hostname, parts.port
        if not host or port is None or not 1 <= port <= 65535:
            raise ValueError()
        if ':' in host:
            ipaddress.IPv6Address(host)
        elif not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9.-]{0,251}[a-zA-Z0-9])?', host):
            raise ValueError()
    except ValueError:
        raise ConnectError('Adresse Internet invalide : hote:port ou [IPv6]:port.') from None
    return value


def atomic_private(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(path.parent, 0o700)
    temporary = path.with_name(path.name + '.new')
    fd = os.open(str(temporary), os.O_CREAT | os.O_TRUNC | os.O_WRONLY, 0o600)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as out:
            out.write(data)
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class Controller:
    LISTEN_PORT = 51820
    PAIR_PORT = 9843
    MAX_PEERS = 8

    def __init__(self, directory='/etc/enigma2/neoconnect', runner=None, clock=time.monotonic, endpoint=None):
        self.directory = Path(directory)
        self.run = runner or self._run
        self.clock = clock
        self.lock = threading.RLock()
        self._active = False
        self.server = None
        from .endpoint import Endpoint
        self.endpoint = endpoint if endpoint is not None else Endpoint()
        self.settings = {}
        self.code = None
        self.code_until = 0
        self.attempts = 0
        self.peers = []
        state = self.directory / 'peers.json'
        if state.exists():
            try:
                self.peers = json.loads(state.read_text(encoding='utf-8'))
                if not isinstance(self.peers, list) or len(self.peers) > self.MAX_PEERS:
                    raise ValueError()
                addresses = set()
                keys = set()
                for peer in self.peers:
                    if not isinstance(peer.get('name'), str) or not re.fullmatch(r'[\w .-]{1,40}', peer['name']):
                        raise ValueError()
                    if not valid_key(peer['public_key']) or peer['public_key'] in keys:
                        raise ValueError()
                    if peer['address'] not in ['10.78.0.%d/32' % i for i in range(2, 10)] or peer['address'] in addresses:
                        raise ValueError()
                    addresses.add(peer['address'])
                    keys.add(peer['public_key'])
            except (ValueError, KeyError, TypeError):
                raise ConnectError('Liste des appareils invalide ; activation refusee.') from None

    @property
    def active(self):
        return self._active and self.endpoint.running()

    @active.setter
    def active(self, value):
        self._active = value

    @staticmethod
    def _run(args, text=None):
        try:
            return subprocess.run(args, input=text, text=True, capture_output=True,
                                  timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired):
            raise ConnectError('Commande reseau indisponible ou expiree.') from None

    def command(self, args, text=None):
        result = self.run(args, text)
        if result.returncode:
            raise ConnectError('Operation reseau refusee. Verifier le moteur integre et OpenSSL.')
        return result.stdout.strip()

    def requirements(self):
        missing = [] if self.endpoint.available() else ['moteur Neo Connect ARMv7']
        if not shutil.which('openssl'):
            missing.append('openssl')
        return missing

    def prepare_identity(self):
        with self.lock:
            self.directory.mkdir(parents=True, exist_ok=True, mode=0o700)
            os.chmod(self.directory, 0o700)
            keyfile = self.directory / 'server.key'
            if not keyfile.exists():
                value = self.command([self.endpoint.binary, 'keygen'])
                if not valid_key(value):
                    raise ConnectError('Generation de cle WireGuard invalide.')
                atomic_private(keyfile, value + '\n')
            self.public_key()
            cert, key = self.directory / 'pairing.crt', self.directory / 'pairing.key'
            if cert.exists() != key.exists():
                raise ConnectError('Identite TLS incomplete ; activation refusee.')
            if not cert.exists():
                self.command(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes',
                              '-days', '3650', '-subj', '/CN=NeoConnect', '-keyout', str(key), '-out', str(cert)])
            os.chmod(cert, 0o600)
            os.chmod(key, 0o600)

    def public_key(self):
        private = (self.directory / 'server.key').read_text(encoding='ascii').strip()
        if not valid_key(private):
            raise ConnectError('Cle privee locale invalide.')
        public = self.command([self.endpoint.binary, 'public-key'], private + '\n')
        if not valid_key(public):
            raise ConnectError('Cle publique locale invalide.')
        return public

    def fingerprint(self):
        pem = (self.directory / 'pairing.crt').read_text(encoding='ascii')
        return hashlib.sha256(ssl.PEM_cert_to_DER_cert(pem)).hexdigest().upper()

    def configure(self, host, receiver_port, endpoint):
        if not private_ipv4(host) or ipaddress.IPv4Address(host) in ipaddress.IPv4Network('10.78.0.0/24'):
            raise ConnectError('Choisir une adresse LAN IPv4 privee hors 10.78.0.0/24.')
        if not isinstance(receiver_port, int) or not 1 <= receiver_port <= 65535:
            raise ConnectError('Port OpenWebif invalide.')
        self.settings = {'receiver_host': host, 'receiver_port': receiver_port,
                         'endpoint': checked_endpoint(endpoint)}

    def _apply(self, peers=None):
        self.endpoint.update(self.peers if peers is None else peers)

    def up(self, host, receiver_port, endpoint, serve=True):
        with self.lock:
            if self.active:
                raise ConnectError('Arreter Neo Connect avant de modifier sa configuration.')
            self.configure(host, receiver_port, endpoint)
            self.prepare_identity()
            if self.server:
                self.server.close()
                self.server = None
            try:
                private = (self.directory / 'server.key').read_text(encoding='ascii').strip()
                self.endpoint.start(private, host, receiver_port, self.peers)
                self.active = True
                if serve:
                    from .pairing import PairingServer
                    self.server = PairingServer(self, host)
                    self.server.start()
            except Exception:
                self.active = False
                if self.server:
                    self.server.close()
                    self.server = None
                self.endpoint.stop()
                raise ConnectError('Activation impossible. Moteur Neo Connect, adresse LAN et ports a verifier.') from None

    def down(self):
        with self.lock:
            self.code = None
            if self.server:
                server, self.server = self.server, None
                server.close()
            self.endpoint.stop()
            self.active = False

    def new_code(self):
        with self.lock:
            if not self.active:
                raise ConnectError('Activer le tunnel avant de creer un code.')
            self.code = '%06d' % secrets.randbelow(1000000)
            self.code_until = self.clock() + 120
            self.attempts = 0
            return self.code

    def pair(self, code, public_key, name):
        with self.lock:
            if not self.active or self.code is None or self.clock() >= self.code_until:
                self.code = None
                raise ConnectError('Code absent ou expire. Creer un nouveau code sur le Vu+.')
            if not isinstance(code, str) or not hmac.compare_digest(code, self.code):
                self.attempts += 1
                if self.attempts >= 3:
                    self.code = None
                raise ConnectError('Code refuse.')
            if not valid_key(public_key) or public_key == self.public_key():
                raise ConnectError('Cle publique de l appareil invalide.')
            if not isinstance(name, str) or not re.fullmatch(r'[\w .-]{1,40}', name):
                raise ConnectError('Nom de l appareil invalide.')
            peer = next((p for p in self.peers if p['public_key'] == public_key), None)
            updated = [dict(p) for p in self.peers]
            if peer is None:
                if len(updated) >= self.MAX_PEERS:
                    raise ConnectError('Huit appareils maximum ; revoquer un ancien appareil.')
                used = {p['address'] for p in updated}
                address = next('10.78.0.%d/32' % i for i in range(2, 10) if '10.78.0.%d/32' % i not in used)
                peer = {'public_key': public_key, 'name': name, 'address': address}
                updated.append(peer)
            else:
                for p in updated:
                    if p['public_key'] == public_key:
                        p['name'] = name
            self._apply(updated)
            try:
                atomic_private(self.directory / 'peers.json', json.dumps(updated))
            except OSError:
                self._apply(self.peers)
                raise ConnectError('Enregistrement impossible ; association annulee.') from None
            self.peers = updated
            self.code = None
            return {'protocol': 1, **self.settings, 'server_public_key': self.public_key(),
                    'address': peer['address'], 'mtu': 1380}

    def revoke(self, public_key):
        with self.lock:
            old = self.peers
            updated = [p for p in old if p['public_key'] != public_key]
            if self.active:
                self._apply(updated)
            try:
                atomic_private(self.directory / 'peers.json', json.dumps(updated))
            except OSError:
                if self.active:
                    self._apply(old)
                raise ConnectError('Revocation non enregistree.') from None
            self.peers = updated
