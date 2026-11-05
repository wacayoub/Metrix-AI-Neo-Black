"""Bounded, LAN-only HTTPS association. No video proxy or receiver control API."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import ssl
import threading

from .core import ConnectError, private_ipv4


class PairingServer:
    def __init__(self, controller, host):
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(str(controller.directory / 'pairing.crt'), str(controller.directory / 'pairing.key'))
        slots = threading.BoundedSemaphore(4)

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def reply(self, status, data):
                body = json.dumps(data).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self):
                if not private_ipv4(self.client_address[0]):
                    self.reply(403, {'error': 'LAN uniquement'})
                    return
                try:
                    length = int(self.headers.get('Content-Length', '0'))
                    if self.path != '/pair' or not 1 <= length <= 4096:
                        self.reply(400, {'error': 'Requete invalide'})
                        return
                    data = json.loads(self.rfile.read(length))
                    if not isinstance(data, dict):
                        raise ValueError()
                    result = controller.pair(data.get('code'), data.get('public_key'), data.get('name'))
                    self.reply(200, result)
                except ConnectError:
                    self.reply(401, {'error': 'Association refusee ; verifier le code sur le Vu+'})
                except (ValueError, TypeError, UnicodeDecodeError):
                    self.reply(400, {'error': 'Requete invalide'})
                except Exception:
                    self.reply(503, {'error': 'Association indisponible'})

        class Server(ThreadingHTTPServer):
            daemon_threads = True
            block_on_close = False

            def get_request(self):
                sock, addr = self.socket.accept()
                sock.settimeout(5)
                try:
                    return context.wrap_socket(sock, server_side=True), addr
                except Exception:
                    sock.close()
                    raise

            def process_request(self, request, address):
                if not slots.acquire(blocking=False):
                    self.shutdown_request(request)
                    return
                try:
                    super().process_request(request, address)
                except Exception:
                    slots.release()
                    raise

            def process_request_thread(self, request, address):
                try:
                    super().process_request_thread(request, address)
                finally:
                    slots.release()

            def handle_error(self, request, address):
                pass  # Never emit request bodies, codes or private keys to Enigma2 logs.

        self.server = Server((host, controller.PAIR_PORT), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
