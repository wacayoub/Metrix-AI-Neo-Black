"""Fetch only the public, pinned audit sources. No receiver communication.

An existing checkout must already match the lock; it is never reset or updated.
Use --check for an entirely offline preflight.
"""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    "MetrixHD": ("MetrixHD", "https://github.com/openatv/MetrixHD"),
    "Enigma2 OpenATV": ("enigma2", "https://github.com/openatv/enigma2"),
}


def git(path, *args):
    result = subprocess.run(["git", "-C", str(path), *args], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify existing checkouts without network access")
    args = parser.parse_args()
    lock = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))
    for source in lock["sources"]:
        if source["name"] not in SOURCES:
            continue
        directory, url = SOURCES[source["name"]]
        if source["url"] != url:
            raise ValueError("Unexpected audit-source URL")
        commit = source["commit"]
        if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
            raise ValueError("Invalid pinned commit")
        path = ROOT / ".upstream" / directory
        if path.is_symlink() or not path.resolve().is_relative_to((ROOT / ".upstream").resolve()):
            raise ValueError("Unsafe upstream path")
        if not path.exists():
            if args.check:
                raise RuntimeError("Missing pinned source: " + directory)
            path.mkdir(parents=True)
            git(path, "init", "--quiet")
            git(path, "remote", "add", "origin", url)
            git(path, "fetch", "--depth=1", "origin", commit)
            git(path, "checkout", "--quiet", "--detach", commit)
        if not (path / ".git").exists() or git(path, "rev-parse", "--show-toplevel").replace("\\", "/").casefold() != path.resolve().as_posix().casefold():
            raise RuntimeError("Not the expected upstream checkout: " + directory)
        if git(path, "rev-parse", "HEAD") != commit:
            raise RuntimeError("Existing source differs from lock; refusing to change " + directory)
        if git(path, "status", "--porcelain", "--untracked-files=no"):
            raise RuntimeError("Modified audit source: " + directory)
        print(directory + ": pinned commit verified " + commit)


if __name__ == "__main__":
    main()
