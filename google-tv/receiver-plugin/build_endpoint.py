"""Cross-compile the pinned userspace endpoint for Vu+ Zero 4K (ARMv7)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--go', default='go')
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = root / 'dist'
    output.mkdir(exist_ok=True)
    env = dict(os.environ, GOOS='linux', GOARCH='arm', GOARM='7', CGO_ENABLED='0', GOTOOLCHAIN='local')
    target = output / 'neoconnect-endpoint-armv7'
    subprocess.run([args.go, '-C', str(root / 'endpoint'), 'build', '-trimpath', '-buildvcs=false',
                    '-ldflags=-s -w -buildid=', '-o', str(target), '.'], env=env, check=True)
    # Go modules carry their own source hashes in go.sum; retain licenses and a source list.
    result = subprocess.run([args.go, '-C', str(root / 'endpoint'), 'list', '-m', '-json', 'all'],
                            env=env, capture_output=True, text=True, encoding='utf-8', check=True)
    decoder, remaining = json.JSONDecoder(), result.stdout.lstrip()
    modules = []
    notices = output / 'licenses'
    notices.mkdir(exist_ok=True)
    while remaining:
        module, end = decoder.raw_decode(remaining)
        remaining = remaining[end:].lstrip()
        if module.get('Main'):
            continue
        modules.append({'module': module['Path'], 'version': module.get('Version'), 'sum': module.get('Sum')})
        if not module.get('Dir'):
            continue  # e.g. the Windows-only wintun module is not linked into Linux ARM.
        directory = Path(module['Dir'])
        for name in ('LICENSE', 'COPYING', 'NOTICE', 'AUTHORS'):
            source = directory / name
            if source.is_file():
                safe = module['Path'].replace('/', '_').replace('.', '_') + '-' + name + '.txt'
                shutil.copyfile(source, notices / safe)
    (notices / 'SOURCES.json').write_text(json.dumps(modules, indent=2), encoding='utf-8')
    goroot = subprocess.run([args.go, 'env', 'GOROOT'], capture_output=True, text=True, check=True).stdout.strip()
    shutil.copyfile(Path(goroot) / 'LICENSE', notices / 'Go-LICENSE.txt')
    print(json.dumps({'target': target.name, 'bytes': target.stat().st_size,
                      'sha256': hashlib.file_digest(target.open('rb'), 'sha256').hexdigest(), 'cgo': False}))


if __name__ == '__main__':
    main()
