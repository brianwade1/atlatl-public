"""Fresh-interpreter imports for research modules with colliding flat names."""

from tests.support.process_helpers import run_python
from tests.support.isolation import KnownDefect


PRELUDE = '''
import sys, json, copy, pickle
from pathlib import Path
from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch
import numpy as np
import pytest
from tests.support.imports import SERVER_DIR, TESTS_DIR, explicit_module
from tests.support.builders import make_map, make_unit, make_scenario, make_state
sys.path[:0] = [str(SERVER_DIR / 'azg'), str(SERVER_DIR / 'portabletorch'), str(SERVER_DIR)]
stack = ExitStack()
def load(name, relative):
    return stack.enter_context(explicit_module(name, SERVER_DIR / relative))
load('Game', 'azg/Game.py')
load('game', 'game.py')
load('utils', 'azg/utils.py')
def board():
    units = [make_unit(hex='hex-2-2'), make_unit(faction='red', hex='hex-3-2')]
    param = make_scenario(make_map(rows=5, cols=5), units)
    return {'param': param, 'state': make_state(units, score=25)}
'''


def probe(source, tmp_path, *, torch=False):
    setup = "import torch\ntorch.set_num_threads(1)\ntorch.manual_seed(1729)\n" if torch else ""
    return run_python(PRELUDE + setup + source, cwd=tmp_path, timeout=60)


def defect_probe(source, tmp_path, *, torch=False):
    result = probe(source, tmp_path, torch=torch)
    if 'S16_MATCHED_DEFECT' in result.stdout.splitlines():
        raise KnownDefect('Exact S16 defect signature reproduced')
