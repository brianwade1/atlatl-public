"""Bounded subprocesses for modules with global state/import side effects."""

import os
from pathlib import Path
import subprocess
import sys

from tests.support.imports import REPO_ROOT, TESTS_DIR


def run_python(source, *, cwd, timeout=30, env_overrides=None):
    cwd = Path(cwd).resolve()
    if not cwd.is_relative_to(TESTS_DIR / ".tmp"):
        raise ValueError("Subprocess working directories must be under tests/.tmp")
    env = os.environ.copy()
    # Opt in to model paths only through explicit per-test overrides.
    for name in list(env):
        if any(part in name.upper() for part in ("MODEL", "CHECKPOINT", "NEURAL")):
            del env[name]
    env.update(env_overrides or {})
    env["ATLATL_NEURAL"] = "0"
    env["PYTHONHASHSEED"] = "1729"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONPATH"] = str(REPO_ROOT)
    for name in ("TMP", "TEMP", "TMPDIR"):
        env[name] = str(cwd)
    try:
        return subprocess.run(
            [sys.executable, "-B", "-c", source], cwd=cwd, env=env,
            text=True, capture_output=True, timeout=timeout, check=True,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise AssertionError(
            f"Child Python failed: {exc}\nstdout:\n{exc.stdout}\nstderr:\n{exc.stderr}"
        ) from exc
