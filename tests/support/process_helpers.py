"""Bounded subprocesses for modules with global state/import side effects."""

import os
from pathlib import Path
import subprocess
import sys

from tests.support.imports import REPO_ROOT, TESTS_DIR


def run_python(source, *, cwd, timeout=30):
    cwd = Path(cwd).resolve()
    if not cwd.is_relative_to(TESTS_DIR / ".tmp"):
        raise ValueError("Subprocess working directories must be under tests/.tmp")
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    for name in ("TMP", "TEMP", "TMPDIR"):
        env[name] = str(cwd)
    return subprocess.run(
        [sys.executable, "-B", "-c", source], cwd=cwd, env=env,
        text=True, capture_output=True, timeout=timeout, check=True,
    )
