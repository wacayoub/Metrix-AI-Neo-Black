"""Inspect generated ar/tar structure, ownership, checksums and disjoint paths."""
import hashlib
import io
import json
import tarfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def members(data):
    if not data.startswith(b"!<arch>\n"):
        raise ValueError("Invalid ar magic")
    result, offset = {}, 8
    while offset < len(data):
        header = data[offset:offset + 60]
        if len(header) != 60 or header[58:60] != b"`\n":
            raise ValueError("Invalid ar header")
        name, size = header[:16].decode().strip().rstrip("/"), int(header[48:58])
        if name in result:
            raise ValueError("Duplicate ar member")
        result[name] = data[offset + 60:offset + 60 + size]
        if len(result[name]) != size:
            raise ValueError("Truncated member")
        offset += 60 + size + size % 2
    return result


def inspect(path):
    contents = members(path.read_bytes())
    assert set(contents) == {"debian-binary", "control.tar.gz", "data.tar.gz"}
    assert contents["debian-binary"] == b"2.0\n"
    with tarfile.open(fileobj=io.BytesIO(contents["control.tar.gz"]), mode="r:gz") as tar:
        assert set(tar.getnames()) == {"./control", "./md5sums"}, "Maintainer scripts forbidden"
        control = tar.extractfile("./control").read().decode()
        sums = tar.extractfile("./md5sums").read().decode()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(contents["data.tar.gz"]), mode="r:gz") as tar:
        for item in tar:
            name = item.name.removeprefix("./")
            parts = PurePosixPath(name).parts
            assert not PurePosixPath(name).is_absolute() and ".." not in parts
            assert item.uid == item.gid == 0
            assert not item.issym() and not item.islnk()
            if item.isfile():
                assert name not in files
                assert name.startswith(("usr/share/enigma2/MetrixNEO/", "usr/share/enigma2/MetrixNEOAdvanced/", "usr/lib/enigma2/python/Components/MetrixNEO/", "usr/lib/enigma2/python/Components/Converter/MetrixNEO", "usr/lib/enigma2/python/Components/Renderer/MetrixNEO", "usr/lib/enigma2/python/Plugins/Extensions/MetrixNEOHelper/", "usr/share/doc/")), name
                assert item.mode == 0o644
                files[name] = tar.extractfile(item).read()
    expected = {}
    for row in sums.splitlines():
        checksum, name = row.split("  ", 1)
        expected[name] = checksum
    assert set(files) == set(expected)
    assert all(hashlib.md5(data).hexdigest() == expected[name] for name, data in files.items())
    assert "Architecture: all\n" in control and "Depends: enigma2" in control
    return files


def main():
    owned = {}
    packages = sorted((ROOT / "dist").glob("*.ipk"))
    assert len(packages) == 4
    for path in packages:
        files = inspect(path)
        assert not set(files).intersection(owned), "File ownership conflict"
        owned.update({name: path.name for name in files})
    report = {"result": "PASS", "packages": len(packages), "owned_files": len(owned), "scripts": 0, "receiver_writes": 0, "opkg_install": "NOT_PERFORMED"}
    (ROOT / "build/ipk-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
