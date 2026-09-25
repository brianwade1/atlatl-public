"""Fresh portable JSON builders; no engine calls and no implicit random draws.

Maps default to 3 rows x 4 columns, clear terrain, no setup, paths or fog.
Overrides use (column, row) keys. Units default to blue infantry A, strength
100 at hex-0-0, movable/effective/undetected. Scenarios default to a blue/red
pair, four phases, zero city points and -2 blue loss penalty. States default
to ordinary blue phase zero, score zero, no city owners. These are explicit
test inputs, not substitutes for Game.initial_state().
"""

from copy import deepcopy
import json

from tests.support.imports import TESTS_DIR


def make_map(rows=3, cols=4, terrain_overrides=None, setup_overrides=None):
    terrain_overrides = terrain_overrides or {}
    setup_overrides = setup_overrides or {}
    result = {"hexes": [], "edges": [], "paths": []}
    edges = {}
    for row in range(rows):
        for col in range(cols):
            x, y = 2 + 3 * col, 2 + 2 * row + col % 2
            points = [(x-1, y-1), (x+1, y-1), (x+2, y),
                      (x+1, y+1), (x-1, y+1), (x-2, y)]
            ids = []
            for a, b in zip(points, points[1:] + points[:1]):
                key = tuple(sorted((a, b)))
                if key not in edges:
                    xa, ya = a
                    xb, yb = b
                    edges[key] = {"id": f"edge-{xa}-{ya}-{xb}-{yb}",
                                  "xa_grid": xa, "ya_grid": ya,
                                  "xb_grid": xb, "yb_grid": yb, "type": "normal"}
                ids.append(edges[key]["id"])
            result["hexes"].append({"x_offset": col, "y_offset": row,
                "x_grid": x, "y_grid": y,
                "terrain": terrain_overrides.get((col, row), "clear"),
                "setup": setup_overrides.get((col, row)), "edges": ids})
    result["edges"] = list(edges.values())
    return result


def make_unit(name="A", faction="blue", unit_type="infantry", strength=100,
              hex="hex-0-0", can_move=True, ineffective=False, detected=False):
    return {"longName": name, "faction": faction, "type": unit_type,
            "currentStrength": strength, "hex": hex, "canMove": can_move,
            "ineffective": ineffective, "detected": detected}


def make_scenario(map_data=None, units=None, *, max_phases=4, city_score=0,
                  loss_penalty=-2):
    return deepcopy({"map": make_map() if map_data is None else map_data,
        "units": [make_unit(), make_unit(faction="red", hex="hex-3-2", can_move=False)]
                 if units is None else units,
        "score": {"maxPhases": max_phases, "cityScore": city_score,
                  "lossPenalty": loss_penalty}})


def make_state(units=None, *, on_move="blue", phase=0, score=0,
               city_owner=None, setup=False, terminal=False):
    return deepcopy({"units": [] if units is None else units,
        "status": {"onMove": on_move, "phaseCount": phase, "score": score,
                   "cityOwner": {} if city_owner is None else city_owner,
                   "setupMode": setup, "isTerminal": terminal}})


def load_fixture(relative_path):
    """Read anew on every call; callers may mutate all returned JSON values."""
    return json.loads((TESTS_DIR / "fixtures" / relative_path).read_text(encoding="utf-8"))
