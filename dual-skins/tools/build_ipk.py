"""Deterministic IPK/ar writer and source bundle; no deployment capability."""
import gzip
import hashlib
import io
import json
import tarfile
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text().strip()
COMMON = "enigma2-plugin-skincomponents-metrixneo-runtime"
PACKAGES = {
    "enigma2-plugin-skins-metrixneo": ("Metrix NEO FHD for OpenATV (hardware unverified)", "enigma2, %s (= %s)" % (COMMON, VERSION), "MetrixNEO"),
    "enigma2-plugin-skins-metrixneo-advanced": ("Metrix NEO Advanced FHD for OpenATV (hardware unverified)", "enigma2, %s (= %s)" % (COMMON, VERSION), "MetrixNEOAdvanced"),
    COMMON: ("Metrix NEO shared rendering components (no Smart dependency)", "enigma2, python3-core, python3-json", "runtime"),
    "enigma2-plugin-extensions-metrixneohelper": ("Optional EPG artwork, opt-in weather and automatic team badges", "enigma2, %s (= %s), python3-netclient, python3-twisted-core" % (COMMON, VERSION), "helper"),
}


def payload(profile):
    if profile.startswith("MetrixNEO"):
        base = ROOT / "skins" / profile
        target = "usr/share/enigma2/" + profile
    elif profile == "runtime":
        base = ROOT / "runtime"
        target = "usr/lib/enigma2/python"
    else:
        base = ROOT / "plugin" / "MetrixNEOHelper"
        target = "usr/lib/enigma2/python/Plugins/Extensions/MetrixNEOHelper"
    result = {}
    for path in sorted(base.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            result[target + "/" + path.relative_to(base).as_posix()] = path.read_bytes()
    return result


def archive(files):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w", format=tarfile.USTAR_FORMAT) as tar:
        directories = set()
        for name in files:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError("Unsafe package path")
            directories.update(str(parent) for parent in p.parents if str(parent) != ".")
        for directory in sorted(directories):
            info = tarfile.TarInfo("./" + directory + "/")
            info.type, info.mode = tarfile.DIRTYPE, 0o755
            info.uid = info.gid = info.mtime = 0
            tar.addfile(info)
        for name, content in sorted(files.items()):
            info = tarfile.TarInfo("./" + name)
            info.size, info.mode = len(content), 0o644
            info.uid = info.gid = info.mtime = 0
            tar.addfile(info, io.BytesIO(content))
    return gzip.compress(stream.getvalue(), compresslevel=9, mtime=0)


def ar(members):
    result = bytearray(b"!<arch>\n")
    for name, content in members:
        header = (name + "/").ljust(16) + "0".ljust(12) + "0".ljust(6) + "0".ljust(6) + "100644".ljust(8) + str(len(content)).ljust(10) + "`\n"
        result.extend(header.encode("ascii"))
        result.extend(content)
        if len(content) % 2:
            result.extend(b"\n")
    return bytes(result)


def build():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    manifest = {"version": VERSION, "status": "NOT_INSTALLED", "hardware_validation": "NOT_PERFORMED", "reference_zip": "NOT_RECEIVED", "visual_references": "SIX_USER_IMAGES_RECEIVED_AND_TRACED", "packages": []}
    manifest["user_visual_approval"] = json.loads((ROOT / "reports/visual-validation.json").read_text(encoding="utf-8"))["overall_status"]
    for package, (description, dependencies, profile) in PACKAGES.items():
        files = payload(profile)
        docs = "usr/share/doc/" + package + "/"
        for path in sorted((ROOT / "LICENSES").glob("*")):
            if path.is_file():
                files[docs + path.name] = path.read_bytes()
        files[docs + "CHANGELOG.md"] = (ROOT / "CHANGELOG.md").read_bytes()
        files[docs + "SOURCE.json"] = (ROOT / "sources.lock.json").read_bytes()
        license_name = "MetrixHD-OpenATV-only & OFL-1.1" if profile.startswith("MetrixNEO") else "MIT"
        control = "\n".join(("Package: " + package, "Version: " + VERSION, "Architecture: all", "Maintainer: Metrix NEO contributors", "Section: skins" if profile.startswith("MetrixNEO") else "Section: enigma2", "Priority: optional", "Depends: " + dependencies, "License: " + license_name, "Description: " + description, "Installed-Size: %d" % ((sum(map(len, files.values())) + 1023) // 1024), ""))
        hashes = "".join(hashlib.md5(data).hexdigest() + "  " + name + "\n" for name, data in sorted(files.items()))
        contents = ar([("debian-binary", b"2.0\n"), ("control.tar.gz", archive({"control": control.encode(), "md5sums": hashes.encode()})), ("data.tar.gz", archive(files))])
        filename = package + "_" + VERSION + "_all.ipk"
        (output / filename).write_bytes(contents)
        manifest["packages"].append({"file": filename, "sha256": hashlib.sha256(contents).hexdigest(), "bytes": len(contents), "files": len(files), "depends": dependencies})
    source_name = "metrix-neo-" + VERSION + "-source.zip"
    with zipfile.ZipFile(output / source_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as bundle:
        for path in sorted(ROOT.rglob("*")):
            relative = path.relative_to(ROOT)
            if not path.is_file() or any(part in (".git", ".upstream", ".codex-remote-attachments", ".codex-attachments", "__pycache__", "build", "dist", ".venv") for part in relative.parts):
                continue
            if path.suffix in (".pyc", ".log", ".ipk") or path.name.startswith(".env"):
                continue
            info = zipfile.ZipInfo("metrix-neo/" + relative.as_posix(), (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, path.read_bytes())
    manifest["source"] = {"file": source_name, "sha256": hashlib.sha256((output / source_name).read_bytes()).hexdigest()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    sums = "".join(item["sha256"] + "  " + item["file"] + "\n" for item in manifest["packages"] + [manifest["source"]])
    (output / "SHA256SUMS").write_text(sums, encoding="ascii")
    print("4 IPK préparés + sources ZIP. NOT_INSTALLED. Aucun script postinst/prerm.")


if __name__ == "__main__":
    build()
