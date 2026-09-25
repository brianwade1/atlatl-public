"""Run separately in the project environment; ordinary tests never download."""

import os
from pathlib import Path
import subprocess
import sys


def main():
    tests_dir = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PLAYWRIGHT_BROWSERS_PATH"] = str(tests_dir / ".cache/ms-playwright")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    temp_dir = tests_dir / ".tmp/browser-install"
    temp_dir.mkdir(parents=True, exist_ok=True)
    for name in ("TMP", "TEMP", "TMPDIR"):
        env[name] = str(temp_dir)
    subprocess.run([sys.executable, "-B", "-m", "playwright", "install", "chromium"],
                   env=env, cwd=temp_dir, check=True, timeout=300)


if __name__ == "__main__":
    main()
