"""Build a deterministic Python + static ARM endpoint IPK; never install it."""
import gzip
import hashlib
import io
from pathlib import Path
import tarfile


def tgz(files):
    buffer = io.BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode='wb', mtime=0, filename='') as gz:
        with tarfile.open(fileobj=gz, mode='w', format=tarfile.USTAR_FORMAT) as archive:
            for name, (data, mode) in sorted(files.items()):
                info = tarfile.TarInfo(name)
                info.size = len(data)
                info.mode = mode
                info.mtime = 0
                info.uid = info.gid = 0
                info.uname = info.gname = 'root'
                archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def main():
    root = Path(__file__).resolve().parent
    control = '''Package: enigma2-plugin-extensions-neoconnect
Version: 0.1.0
Architecture: vuzero4k
Maintainer: Metrix Neo project
Section: extra
Priority: optional
Depends: enigma2, python3-core, python3-json, python3-threading, python3-netclient, python3-netserver, python3-misc, python3-asyncio, python3-crypt, openssl
Description: Explicit private pairing with Neo Android and receiver WireGuard endpoint.
 Userspace endpoint: no kernel module, host routes, firewall or router changes.
'''.encode()
    files = {'./usr/lib/enigma2/python/Plugins/Extensions/NeoConnect/' + p.name: (p.read_bytes(), 0o644)
             for p in sorted((root / 'NeoConnect').glob('*.py'))}
    assert len(files) == 5
    binary = root / 'dist/neoconnect-endpoint-armv7'
    assert binary.is_file(), 'Run build_endpoint.py first'
    payload = binary.read_bytes()
    assert payload[:4] == b'\x7fELF' and int.from_bytes(payload[18:20], 'little') == 40, 'ARM ELF required'
    files['./usr/lib/enigma2/python/Plugins/Extensions/NeoConnect/neoconnect-endpoint'] = (payload, 0o755)
    for notice in (root / 'dist/licenses').glob('*'):
        files['./usr/share/doc/neoconnect/licenses/' + notice.name] = (notice.read_bytes(), 0o644)
    members = [('debian-binary', b'2.0\n'), ('control.tar.gz', tgz({'./control': (control, 0o644)})), ('data.tar.gz', tgz(files))]
    result = bytearray(b'!<arch>\n')
    for name, data in members:
        header = ('%-16s%-12s%-6s%-6s%-8s%-10s`\n' % (name + '/', 0, 0, 0, '100644', len(data))).encode('ascii')
        assert len(header) == 60
        result += header + data + (b'\n' if len(data) % 2 else b'')
    destination = root / 'dist'
    destination.mkdir(exist_ok=True)
    path = destination / 'enigma2-plugin-extensions-neoconnect_0.1.0_vuzero4k.ipk'
    path.write_bytes(result)
    digest = hashlib.sha256(result).hexdigest()
    path.with_suffix('.ipk.sha256').write_text(digest + '  ' + path.name + '\n', encoding='ascii')
    print(path.name + ' ' + str(len(result)) + ' bytes SHA256=' + digest)


if __name__ == '__main__':
    main()
