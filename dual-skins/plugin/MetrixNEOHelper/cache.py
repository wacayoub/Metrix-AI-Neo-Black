"""Bounded, dedicated cache; only files owned by this cache may be evicted."""
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path


class Cache:
    def __init__(self, root, max_bytes=32 * 1024 * 1024, clock=time.time):
        self.root = Path(root)
        self.max_bytes = max_bytes
        self.clock = clock

    def _path(self, key):
        return self.root / ("neo-" + hashlib.sha256(key.encode("utf-8")).hexdigest() + ".json")

    def get(self, key, stale=False):
        try:
            path = self._path(key)
            if path.is_symlink():
                return None
            data = json.loads(path.read_text(encoding="utf-8"))
            if stale or data["expires"] > self.clock():
                return data["value"]
        except (OSError, ValueError, KeyError, TypeError):
            pass
        return None

    def put(self, key, value, ttl):
        if ttl <= 0 or self.max_bytes <= 0:
            raise ValueError("Invalid cache bound")
        data = json.dumps({"expires": self.clock() + ttl, "value": value}, ensure_ascii=False).encode("utf-8")
        if len(data) > self.max_bytes:
            raise ValueError("Item exceeds the cache budget")
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ValueError("Cache root must not be a symlink")
        fd, name = tempfile.mkstemp(prefix=".neo-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
            os.replace(name, self._path(key))
        finally:
            if os.path.exists(name):
                os.unlink(name)
        self.evict()

    def image_path(self, key):
        path = self.root / ("neo-" + hashlib.sha256(key.encode("utf-8")).hexdigest() + ".png")
        return path if not path.is_symlink() and path.is_file() else None

    def put_image(self, key, content):
        if not content or len(content) > min(512*1024, self.max_bytes):
            raise ValueError("Image exceeds cache budget")
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink():
            raise ValueError("Cache root must not be a symlink")
        destination = self.root / ("neo-" + hashlib.sha256(key.encode("utf-8")).hexdigest() + ".png")
        fd, name = tempfile.mkstemp(prefix=".neo-", dir=self.root)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(content)
            os.replace(name, destination)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        self.evict()
        return destination if destination.is_file() else None

    def evict(self):
        files = [p for p in self.root.glob("neo-*.*") if p.suffix in (".json", ".png") and not p.is_symlink() and len(p.stem) == 68]
        files.sort(key=lambda p: (p.stat().st_mtime_ns, p.name))
        size = sum(p.stat().st_size for p in files)
        for path in files:
            if size <= self.max_bytes:
                break
            size -= path.stat().st_size
            path.unlink()
