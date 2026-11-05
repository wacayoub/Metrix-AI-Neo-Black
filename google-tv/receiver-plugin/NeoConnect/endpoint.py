"""Control the owned userspace endpoint through private pipes, never a shell."""
import json
from pathlib import Path
import select
import subprocess

from .core import ConnectError


class Endpoint:
    def __init__(self):
        self.binary = str(Path(__file__).with_name('neoconnect-endpoint'))
        self.process = None

    def available(self):
        return Path(self.binary).is_file()

    def running(self):
        return self.process is not None and self.process.poll() is None

    def send(self, value):
        if not self.running():
            raise ConnectError('Moteur Neo Connect arrete.')
        try:
            self.process.stdin.write(json.dumps(value) + '\n')
            self.process.stdin.flush()
            ready, _, _ = select.select([self.process.stdout], [], [], 10)
            if not ready or json.loads(self.process.stdout.readline(1024)).get('ok') is not True:
                raise ValueError()
        except (OSError, ValueError):
            self.stop()
            raise ConnectError('Configuration du moteur Neo Connect refusee.') from None

    def start(self, private_key, host, port, peers):
        if self.running():
            raise ConnectError('Moteur deja actif.')
        self.process = subprocess.Popen([self.binary, 'serve'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding='utf-8', bufsize=1, close_fds=True)
        self.send({'op': 'configure', 'private_key': private_key, 'receiver_host': host, 'receiver_port': port, 'peers': peers})

    def update(self, peers):
        self.send({'op': 'peers', 'peers': peers})

    def stop(self):
        process, self.process = self.process, None
        if process is None:
            return
        if process.stdin:
            try:
                process.stdin.close()
            except OSError:
                pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=3)
        if process.stdout:
            process.stdout.close()
