"""Download the pinned official Android SDK and extract ARMv7 (Sony BRAVIA).

Usage: python tools/prepare-gstreamer.py ABSOLUTE_SDK_DESTINATION
The archive is verified before extraction. No Android device is modified.
"""
import concurrent.futures
import hashlib
from pathlib import Path
import shutil
import sys
import tarfile
import urllib.request

VERSION = "1.28.8"
SHA256 = "f19c6f971a956675402452fce0fe772d66dbd0d28d70999618355813ea593a99"
URL = f"https://gstreamer.freedesktop.org/data/pkg/android/{VERSION}/gstreamer-1.0-android-universal-{VERSION}.tar.xz"


def prepare(destination):
    root = Path(destination).resolve()
    root.mkdir(parents=True, exist_ok=True)
    archive = root / f"gstreamer-{VERSION}.tar.xz"
    if not archive.exists():
        size = int(urllib.request.urlopen(urllib.request.Request(URL, method="HEAD"), timeout=60).headers["Content-Length"])
        block = 16 * 1024 * 1024

        def part(i):
            lo, hi = i * block, min(size, (i + 1) * block) - 1
            target = root / f"download-{i:03}.part"
            for attempt in range(3):
                try:
                    req = urllib.request.Request(URL, headers={"Range": f"bytes={lo}-{hi}"})
                    with urllib.request.urlopen(req, timeout=120) as response, target.open("wb") as out:
                        if response.status != 206 or not response.headers["Content-Range"].startswith(f"bytes {lo}-"):
                            raise RuntimeError("Server did not honor download range")
                        shutil.copyfileobj(response, out)
                    if target.stat().st_size != hi - lo + 1:
                        raise RuntimeError("Incomplete download")
                    return target
                except Exception:
                    if attempt == 2:
                        raise

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            parts = list(pool.map(part, range((size + block - 1) // block)))
        with archive.open("wb") as out:
            for part_file in parts:
                with part_file.open("rb") as source:
                    shutil.copyfileobj(source, out)
                part_file.unlink()
    with archive.open("rb") as source:
        if hashlib.file_digest(source, "sha256").hexdigest() != SHA256:
            raise RuntimeError("SDK SHA256 mismatch; remove the invalid archive and retry")
    links = []
    with tarfile.open(archive, "r|xz") as tar:
        for member in tar:
            if not member.name.startswith("armv7/"):
                continue
            target = root / member.name
            if not target.resolve().is_relative_to(root):
                raise RuntimeError("Invalid archive path")
            if member.issym() or member.islnk():
                links.append(member)
            elif member.isdir() or member.isreg():
                tar.extract(member, root, filter="data")
    # Windows can copy link targets without requiring Developer Mode/admin rights.
    for member in links:
        target = root / member.name
        source = root / member.linkname if member.islnk() else target.parent / member.linkname
        if not source.resolve().is_relative_to(root):
            raise RuntimeError("Invalid archive link")
        if source.is_file():
            shutil.copyfile(source, target)
    print(f"GStreamer {VERSION} ARMv7 verified and extracted: {root}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    prepare(sys.argv[1])
