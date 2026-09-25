"""Content manifests include ignored/untracked files and respect user changes."""

import hashlib


PROTECTED_DIRS = ("server", "browser", "scenarios")


def content_manifest(root, directories=PROTECTED_DIRS):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for directory in directories
        for path in sorted((root / directory).rglob("*"))
        if path.is_file()
    }


def manifest_changes(before, after):
    return {
        "added": sorted(after.keys() - before.keys()),
        "removed": sorted(before.keys() - after.keys()),
        "changed": sorted(key for key in before.keys() & after.keys()
                          if before[key] != after[key]),
    }


class KnownDefect(AssertionError):
    """Raise only after matching a documented defect's exact wrong signature."""
