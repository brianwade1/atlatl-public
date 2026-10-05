"""S05 readable search keys and documented non-cryptographic limitations."""

from copy import deepcopy

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.fixture
def key_input(game_factory, make_map, make_unit):
    game = game_factory(map_data=make_map(rows=1, cols=2), units=[make_unit()])
    return import_server("game").statePlusParamHashKey, game.initial_state(), game.parameters()


def test_literal_key_layout_and_input_isolation(key_input):
    key, state, params = key_input
    before = deepcopy((state, params))
    assert key(state, params) == "phase 0 score 0\nc100ibo\t\t\n\t\tc\n"
    assert (state, params) == before


@pytest.mark.parametrize("kind,expected", [
    ("mechinf", "phase 0 score 0\nc100mbo\t\t\n\t\tc\n"),
    ("artillery", "phase 0 score 0\nc100abo\t\t\n\t\tc\n"),
])
def test_remaining_unit_type_encodings(key_input, kind, expected):
    key, state, params = key_input
    state["units"][0]["type"] = kind
    before = deepcopy((state, params))
    assert key(state, params) == expected
    assert (state, params) == before


@pytest.mark.parametrize("field,expected", [
    ("terrain", "phase 0 score 0\nr100ibo\t\t\n\t\tc\n"),
    ("position", "phase 0 score 0\nc\t\t\n\t\tc100ibo\n"),
    ("type", "phase 0 score 0\nc100tbo\t\t\n\t\tc\n"),
    ("strength", "phase 0 score 0\nc75ibo\t\t\n\t\tc\n"),
    ("availability", "phase 0 score 0\nc100ib\t\t\n\t\tc\n"),
    ("faction", "phase 0 score 0\nc100iro\t\t\n\t\tc\n"),
    ("phase", "phase 1 score 0\nc100ibo\t\t\n\t\tc\n"),
    ("score", "phase 0 score -3\nc100ibo\t\t\n\t\tc\n"),
    ("blue-setup", "phase blue setup score 0\nc100ibo\t\t\n\t\tc\n"),
    ("red-setup", "phase red setup score 0\nc100ibo\t\t\n\t\tc\n"),
])
def test_represented_fields_change_key(key_input, field, expected):
    key, state, params = key_input
    baseline = key(state, params)
    if field == "terrain":
        params["map"]["hexes"][0]["terrain"] = "rough"
    elif field in {"position", "type", "strength", "availability", "faction"}:
        attribute, value = {"position": ("hex", "hex-1-0"), "type": ("type", "armor"),
            "strength": ("currentStrength", 75), "availability": ("canMove", False),
            "faction": ("faction", "red")}[field]
        state["units"][0][attribute] = value
    elif field in {"phase", "score"}:
        state["status"]["phaseCount" if field == "phase" else "score"] = 1 if field == "phase" else -3
    else:
        state["status"].update(setupMode=True, onMove=field.split("-")[0])
    assert key(state, params) == expected
    assert expected != baseline


@pytest.mark.parametrize("terrain,code", [("clear", "c"), ("urban", "u"), ("rough", "r"),
                                         ("marsh", "m"), ("water", "w")])
def test_supported_terrain_codes(key_input, terrain, code):
    key, state, params = key_input
    params["map"]["hexes"][1]["terrain"] = terrain
    state["status"]["cityOwner"] = {"hex-1-0": "neutral"}
    assert key(state, params) == f"phase 0 score 0\nc100ibo\t\t\n\t\t{code}\n"


@pytest.mark.parametrize("owner,code", [("neutral", "u"), ("blue", "ub"), ("red", "ur")])
def test_city_owner_key(key_input, owner, code):
    key, state, params = key_input
    params["map"]["hexes"][1]["terrain"] = "urban"
    state["status"]["cityOwner"] = {"hex-1-0": owner}
    assert key(state, params) == f"phase 0 score 0\nc100ibo\t\t\n\t\t{code}\n"


@pytest.mark.parametrize("field", ["fractional-strength", "name", "detected", "ineffective",
    "on-move", "terminal", "max-phases", "city-score", "loss-penalty", "fog", "setup-zone"])
def test_omitted_fields_collide_characterization(key_input, field):
    key, state, params = key_input
    original = key(state, params)
    if field in {"fractional-strength", "name", "detected", "ineffective"}:
        attribute, value = {"fractional-strength": ("currentStrength", 100.9),
            "name": ("longName", "renamed"), "detected": ("detected", True),
            "ineffective": ("ineffective", True)}[field]
        state["units"][0][attribute] = value
    elif field in {"on-move", "terminal"}:
        state["status"]["onMove" if field == "on-move" else "isTerminal"] = "red" if field == "on-move" else True
    elif field in {"max-phases", "city-score", "loss-penalty"}:
        params["score"][{"max-phases": "maxPhases", "city-score": "cityScore", "loss-penalty": "lossPenalty"}[field]] = 9
    elif field == "fog":
        params["map"]["fogOfWar"] = True
    else:
        params["map"]["hexes"][0]["setup"] = "setup-type-red"
    assert key(state, params) == original


def test_second_stacked_unit_omitted_characterization(key_input, make_unit):
    key, state, params = key_input
    original = key(state, params)
    state["units"].append(make_unit("B", unit_type="armor"))
    assert key(state, params) == original
    state["units"].reverse()
    assert key(state, params) != original


def test_unused_terrain_exception_characterization(key_input):
    key, state, params = key_input
    params["map"]["hexes"][1]["terrain"] = "unused"
    with pytest.raises(KeyError) as caught:
        key(state, params)
    assert caught.value.args == ("unused",)
