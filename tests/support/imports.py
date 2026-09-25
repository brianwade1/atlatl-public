"""Resolve flat engine imports without relying on the working directory."""

from contextlib import contextmanager
import importlib
import importlib.util
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
TESTS_DIR = REPO_ROOT / "tests"
SERVER_DIR = REPO_ROOT / "server"


def assert_origin(module, expected):
    assert Path(module.__file__).resolve() == Path(expected).resolve(), (
        f"Wrong module origin: {module.__name__}: {module.__file__}; expected {expected}"
    )
    return module


@contextmanager
def server_imports():
    """Expose flat imports and restore paths/module collisions.

    For azg and portabletorch, use run_python in a fresh subprocess and load
    Game/game/utils/cnn with explicit_module under their required names.
    """
    original_path = sys.path[:]
    original_modules = sys.modules.copy()
    sys.path[:0] = [str(SERVER_DIR), str(REPO_ROOT)]
    try:
        yield
    finally:
        sys.path[:] = original_path
        for name, module in list(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            local = filename and Path(filename).resolve().is_relative_to(SERVER_DIR)
            if name in original_modules:
                if module is not original_modules[name]:
                    sys.modules[name] = original_modules[name]
            elif local:
                del sys.modules[name]
        for name, module in original_modules.items():
            if name not in sys.modules:
                sys.modules[name] = module


def import_server(name):
    """Reject cached modules from another directory with the same name."""
    return assert_origin(importlib.import_module(name), SERVER_DIR / f"{name}.py")


@contextmanager
def explicit_module(name, filename):
    """Load an exact file under its required name; restore that entry on exit."""
    missing = object()
    previous = sys.modules.get(name, missing)
    filename = Path(filename).resolve()
    spec = importlib.util.spec_from_file_location(name, filename)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {name} from {filename}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        yield assert_origin(module, filename)
    finally:
        if previous is missing:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
