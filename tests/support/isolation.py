"""Content manifests include ignored/untracked files and respect user changes."""

import hashlib
from contextlib import contextmanager
import random


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


@contextmanager
def isolated_rng(seed=1729, *, torch_module=None):
    """Restore Python/NumPy and optional CPU Torch state even on failure.

    Torch is supplied explicitly by ML consumers, never imported by core tests.
    GPU tests need their own device-specific fork_rng context.
    """
    import numpy as np

    python_state, numpy_state = random.getstate(), np.random.get_state()
    if torch_module is not None:
        torch_state = torch_module.get_rng_state().clone()
        deterministic = torch_module.are_deterministic_algorithms_enabled()
        warn_only = torch_module.is_deterministic_algorithms_warn_only_enabled()
        threads = torch_module.get_num_threads()
    try:
        random.seed(seed)
        np.random.seed(seed)
        if torch_module is not None:
            torch_module.random.default_generator.manual_seed(seed)
            torch_module.use_deterministic_algorithms(True)
            torch_module.set_num_threads(1)
        yield
    finally:
        random.setstate(python_state)
        np.random.set_state(numpy_state)
        if torch_module is not None:
            torch_module.set_rng_state(torch_state)
            torch_module.use_deterministic_algorithms(deterministic, warn_only=warn_only)
            torch_module.set_num_threads(threads)


@contextmanager
def preserve_globals(*attributes):
    """Preserve (object, attribute) bindings and nested dict/list/set identities.

    Snapshots retain aliases across rule tables/registries.
    Opaque server/model objects are retained by reference, never deep-copied.
    Missing bindings (e.g. server.gym_ai before initialization) are removed again.
    Pass AI instance counters explicitly; do not import optional modules here.
    """
    missing = object()
    bindings = [(obj, name, getattr(obj, name, missing)) for obj, name in attributes]
    containers = {}

    def visit(value):
        if isinstance(value, (dict, list, set)):
            if id(value) in containers:
                return
            containers[id(value)] = (value, None)
            for child in (value.values() if isinstance(value, dict) else value):
                visit(child)
        elif isinstance(value, tuple):
            for child in value:
                visit(child)

    for _, _, value in bindings:
        visit(value)
    # Shallow contents retain references to the original nested objects.
    containers = {key: (value, value.copy()) for key, (value, _) in containers.items()}
    try:
        yield
    finally:
        for value, saved in containers.values():
            if isinstance(value, list):
                value[:] = saved
            else:
                value.clear()
                value.update(saved)
        for obj, name, value in bindings:
            if value is missing:
                if hasattr(obj, name):
                    delattr(obj, name)
            else:
                setattr(obj, name, value)


def finite_random(values):
    """Fail on unexpected extra draws, rather than silently selecting a branch."""
    draws = iter(values)

    def draw():
        try:
            return next(draws)
        except StopIteration as exc:
            raise AssertionError("Deterministic random sequence exhausted") from exc

    return draw
