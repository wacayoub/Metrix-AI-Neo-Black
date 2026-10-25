"""Prepare an additive Git binary patch against the audited user repository.

Uses Git objects and a separate index only. Does not checkout, apply a patch to
the working tree, commit, push, modify update feeds, or execute legacy scripts.
"""
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "18ec2cfd3d9e97fc41fb889d81bc695961a5e6eb"


def git(*args, env=None, input=None):
    result = subprocess.run(["git", *args], cwd=ROOT, env=env, input=input, capture_output=True)
    if result.returncode:
        raise RuntimeError(result.stderr.decode("utf-8", errors="replace"))
    return result.stdout


def main():
    # Read the working files; all new Git objects and both review indices live in
    # build/. The real .git index/object store remain read-only in managed sessions.
    git("cat-file", "-e", BASE + "^{commit}")
    existing = git("ls-tree", "--name-only", BASE).decode().splitlines()
    if "dual-skins" in existing:
        raise ValueError("dual-skins already exists in the audited base")
    index = (ROOT / "build/legacy-review.index").resolve()
    if not index.is_relative_to((ROOT / "build").resolve()):
        raise ValueError("Index outside the local build directory")
    index.parent.mkdir(exist_ok=True)
    objects = ROOT / "build/legacy-objects"
    objects.mkdir(exist_ok=True)
    original_objects = git("rev-parse", "--git-path", "objects").decode().strip()
    original_objects = str((ROOT / original_objects).resolve())
    env = dict(os.environ, GIT_INDEX_FILE=str(index), GIT_OBJECT_DIRECTORY=str(objects.resolve()), GIT_ALTERNATE_OBJECT_DIRECTORIES=original_objects)
    project_env = dict(env, GIT_INDEX_FILE=str((ROOT / "build/project-review.index").resolve()))
    git("read-tree", "--empty", env=project_env)
    paths = set(git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")) - {""}
    selected = []
    for name in sorted(paths):
        path = ROOT / name
        if not path.exists():
            continue
        if path.is_symlink() or not path.resolve().is_relative_to(ROOT.resolve()) or not path.is_file():
            raise ValueError("Unsafe project file: " + name)
        selected.append(name.encode("utf-8") + b"\0")
    # Batch indexing avoids launching one Git process for every PNG. All index
    # and object writes still use the isolated build/ locations above.
    git("add", "-f", "--pathspec-from-file=-", "--pathspec-file-nul", env=project_env, input=b"".join(selected))
    tree = git("write-tree", env=project_env).decode().strip()
    git("read-tree", BASE, env=env)
    git("read-tree", "--prefix=dual-skins/", tree, env=env)
    ci = (ROOT / "packaging/github-integration-ci.yml").read_bytes()
    blob = git("hash-object", "-w", "--stdin", env=env, input=ci).decode().strip()
    git("update-index", "--add", "--cacheinfo", "100644," + blob + ",.github/workflows/metrix-neo-dual-skins.yml", env=env)
    changed = git("diff", "--cached", "--name-status", BASE, env=env).decode().splitlines()
    assert changed and all(row.startswith("A\t") for row in changed), "Existing file changed"
    assert all(row.split("\t", 1)[1].startswith("dual-skins/") or row.endswith(".github/workflows/metrix-neo-dual-skins.yml") for row in changed)
    patch = git("diff", "--cached", "--binary", "--full-index", BASE, env=env)
    destination = ROOT / "dist/metrix-neo-dual-skins.patch"
    destination.write_bytes(patch)
    # Check reverse against the prepared index; it represents exactly the result
    # of applying the additive patch to BASE, without changing actual files.
    git("apply", "--cached", "--check", "--reverse", str(destination), env=env)
    git("read-tree", BASE, env=env)
    git("apply", "--cached", "--check", str(destination), env=env)
    report = {"repository": "https://github.com/wacayoub/Metrix-AI-Neo-Black", "base_commit": BASE, "result": "PASS", "only_additions": True, "existing_files_modified": 0, "files_added": len(changed), "forward_apply_check": "PASS", "reverse_apply_check": "PASS", "sha256": hashlib.sha256(patch).hexdigest(), "patch": destination.name, "published": False, "receiver_status": "NOT_INSTALLED"}
    (ROOT / "dist/GITHUB_PREPARATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
