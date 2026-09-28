"""S06 loading and generator contracts, with explicit legacy characterizations."""

from collections import Counter
from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import random

import pytest

from tests.support.builders import make_scenario
from tests.support.imports import import_server
from tests.support.process_helpers import run_python


pytestmark = [pytest.mark.core, pytest.mark.unit,
              pytest.mark.usefixtures("engine_imports", "rng")]

FAMILIES = [
    pytest.param("clear_square_factory", dict(size=4, min_units=1, max_units=2), id="clear"),
    pytest.param("hierarchy_factory", dict(size=10, min_parents=1, max_parents=2,
                 hierarchy_depth=3, hierarchy_branching=2), id="hierarchy"),
    pytest.param("invasion_factory", dict(width=5, height=6, n_blue=2, n_red=2), id="invasion"),
]


def without_detection(value):
    result = deepcopy(value)
    for unit in result["units"]:
        unit.pop("detected")
    return result


@pytest.mark.parametrize("form", ["bare", "relative", "absolute", "relative-dir",
                                  "absolute-dir", "home-file", "home-dir"])
def test_resolve_and_load_path_forms(form, tmp_path, monkeypatch):
    scenario = import_server("scenario")
    folder = tmp_path / "scenario files"
    folder.mkdir()
    path = folder / "small game.scn"
    expected = make_scenario()
    path.write_text(json.dumps(expected), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(scenario, "DEFAULT_SCENARIO_DIR", folder)
    # Control only home expansion; retain all ordinary Path resolution.
    expanduser = Path.expanduser
    monkeypatch.setattr(Path, "expanduser", lambda self:
                        tmp_path / str(self)[2:] if str(self).startswith(("~/", "~\\"))
                        else expanduser(self))
    filename, directory = {
        "bare": (path.name, None), "relative": (Path("scenario files") / path.name, None),
        "absolute": (path, tmp_path / "ignored"),
        "relative-dir": (path.name, "scenario files"),
        "absolute-dir": (path.name, folder),
        "home-file": ("~/scenario files/small game.scn", None),
        "home-dir": (path.name, "~/scenario files"),
    }[form]
    assert scenario.resolve_scenario_path(filename, directory) == path
    assert scenario.from_file_factory(filename, directory)() == expected
    if form in {"bare", "absolute", "absolute-dir", "home-file", "home-dir"}:
        monkeypatch.chdir(folder)
        assert scenario.resolve_scenario_path(filename, directory) == path


def test_file_factory_utf8_eager_loading_and_shared_object(tmp_path):
    path = tmp_path / "unicode.scn"
    expected = make_scenario()
    expected["units"][0]["longName"] = "Éclaireurs 山"
    path.write_text(json.dumps(expected, ensure_ascii=False), encoding="utf-8")
    factory = import_server("scenario").from_file_factory(path)
    path.unlink()
    first = factory()
    assert first == expected
    assert factory() is first
    first["units"][0]["currentStrength"] = 75
    assert factory()["units"][0]["currentStrength"] == 75


@pytest.mark.parametrize("contents,error,match", [
    pytest.param(None, FileNotFoundError, "missing.scn", id="missing"),
    pytest.param('{"map":', json.JSONDecodeError, "Expecting value", id="invalid-json"),
])
def test_file_factory_load_errors(tmp_path, contents, error, match):
    path = tmp_path / "missing.scn"
    if contents is not None:
        path.write_text(contents, encoding="utf-8")
    with pytest.raises(error, match=match):
        import_server("scenario").from_file_factory(path)


@pytest.mark.parametrize("payload,stage,key", [
    pytest.param({}, "construct", "map", id="missing-map"),
    pytest.param({"map": {"hexes": [], "edges": [], "paths": []}},
                 "initial", "units", id="missing-units"),
])
def test_file_factory_defers_schema_consumption(tmp_path, payload, stage, key):
    path = tmp_path / "incomplete.scn"
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = import_server("scenario").from_file_factory(path)()
    assert loaded == payload
    with pytest.raises(KeyError) as exc:
        game = import_server("game").Game(loaded)
        assert stage == "initial"
        game.initial_state()
    assert exc.value.args == (key,)


@pytest.mark.parametrize("side,margin,coordinates", [
    ("north", 1, [(0,0),(0,1),(1,0),(1,1),(2,0),(2,1),(3,0),(3,1)]),
    ("south", 1, [(0,3),(1,3),(2,3),(3,3)]),
    ("west", 1, [(0,0),(0,1),(0,2),(0,3),(1,0),(1,1),(1,2),(1,3)]),
    ("east", 1, [(3,0),(3,1),(3,2),(3,3)]),
    ("ns-middle", 1, [(0,2),(1,2),(2,2),(3,2)]),
    ("ew-middle", 1, [(2,0),(2,1),(2,2),(2,3)]),
    ("north", 2, [(0,0),(1,0),(2,0),(3,0)]),
    ("south", 2, []), ("east", 2, []),
    ("west", 2, [(0,0),(0,1),(0,2),(0,3)]),
    ("ns-middle", 2, [(0,1),(0,2),(0,3),(1,1),(1,2),(1,3),
                       (2,1),(2,2),(2,3),(3,1),(3,2),(3,3)]),
    ("ew-middle", 2, [(1,0),(1,1),(1,2),(1,3),(2,0),(2,1),(2,2),(2,3),
                       (3,0),(3,1),(3,2),(3,3)]),
    ("ns-middle", 0, []), ("ew-middle", 0, []),
    ("unknown", 1, [(2,0),(2,1),(2,2),(2,3)]),
])
def test_setup_regions(side, margin, coordinates):
    assert import_server("scenario").get_setup_hex_ids(4, side, margin) == [
        f"hex-{x}-{y}" for x, y in coordinates]


@pytest.mark.parametrize("bounds,expected", [
    ((1,2,3,4), ["hex-1-3", "hex-1-4", "hex-2-3", "hex-2-4"]),
    ((2,2,1,1), ["hex-2-1"]), ((2,1,0,2), []), ((0,2,2,1), []),
])
def test_rect_regions(bounds, expected):
    assert import_server("scenario").get_rect_region_ids(*bounds) == expected


def test_flip_colors_values_and_shallow_sharing():
    original = make_scenario()
    original["units"][0]["metadata"] = {"orders": ["hold"]}
    before = deepcopy(original)
    flipped = import_server("scenario").flip_colors(original)
    expected = deepcopy(before)
    expected["units"][0]["faction"] = "red"
    expected["units"][1]["faction"] = "blue"
    assert flipped == expected
    assert original == before
    assert flipped is not original
    assert flipped["units"] is not original["units"]
    assert all(a is not b for a, b in zip(flipped["units"], original["units"]))
    assert flipped["map"] is original["map"]
    assert flipped["score"] is original["score"]
    assert flipped["units"][0]["metadata"] is original["units"][0]["metadata"]
    assert import_server("scenario").flip_colors(flipped) == before


@pytest.mark.parametrize("name,options", FAMILIES)
@pytest.mark.parametrize("cycle", [0, 1, 2])
@pytest.mark.parametrize("seed", [0, 1729])
def test_seeded_sequences_and_cycles(name, options, cycle, seed):
    constructor = getattr(import_server("scenario"), name)
    left = constructor(**options, scenarioSeed=seed, scenarioCycle=cycle)
    right = constructor(**options, scenarioSeed=seed, scenarioCycle=cycle)
    a, b = [], []
    for index in range(6):
        random.seed(index)
        a.append(without_detection(left()))
        random.seed(100 + index)
        b.append(without_detection(right()))
    assert a == b
    if cycle:
        assert a[cycle:] == a[:-cycle]
    else:
        assert a[0] != a[1]


@pytest.mark.parametrize("name,options", FAMILIES[:2])
def test_balance_alternates_and_cycles_generated_pairs(name, options):
    scenario = import_server("scenario")
    factory = getattr(scenario, name)(**options, scenarioSeed=31, scenarioCycle=2, balance=True)
    values = [factory() for _ in range(6)]
    for first, second in zip(values[::2], values[1::2]):
        assert second == scenario.flip_colors(first)
        assert second["map"] is first["map"]
        assert second["score"] is first["score"]
    assert without_detection(values[0]) != without_detection(values[2])
    assert without_detection(values[0]) == without_detection(values[4])


@pytest.mark.parametrize("name,options", FAMILIES)
@pytest.mark.parametrize("fog", [False, True])
def test_generated_schema_counts_regions_and_scores(name, options, fog):
    scenario = import_server("scenario")
    factory = getattr(scenario, name)(**options, scenarioSeed=19, num_cities=3,
                                    max_phases=7, fog_of_war=fog)
    for _ in range(3):
        value = factory()
        width, height = (5, 6) if name == "invasion_factory" else (options["size"],)*2
        cells = {(h["x_offset"], h["y_offset"]): h for h in value["map"]["hexes"]}
        assert set(cells) == {(x,y) for x in range(width) for y in range(height)}
        assert {h["terrain"] for h in cells.values()} <= {"clear", "urban"}
        cities = {xy for xy, h in cells.items() if h["terrain"] == "urban"}
        assert 1 <= len(cities) <= 3
        assert value["map"]["fogOfWar"] is fog
        assert value["score"] == {"maxPhases": 7, "lossPenalty": -1, "cityScore": 24}
        units = value["units"]
        assert len({(u["faction"],u["longName"]) for u in units}) == len(units)
        assert all(u["currentStrength"] == 100 and u["type"] == "infantry" for u in units)
        assert all(not u["ineffective"] and isinstance(u["detected"], bool) for u in units)
        by_faction = {f: [u for u in units if u["faction"] == f] for f in ("blue", "red")}
        ids = {f: {u["hex"] for u in group} for f, group in by_faction.items()}
        if name == "invasion_factory":
            assert [len(g) for g in by_faction.values()] == [2, 2]
            assert value["map"]["initialCityOwnership"] == "red"
            for faction, group in by_faction.items():
                assert len(ids[faction]) == len(group)
                for u in group:
                    _, x, y = u["hex"].split("-")
                    assert cells[int(x), int(y)]["setup"] == "setup-type-" + faction
            assert all(cells[xy]["setup"] == "setup-type-red" for xy in cities)
            assert {f"hex-{x}-{y}" for x,y in cities}.isdisjoint(ids["red"])
        else:
            assert all(h["setup"] is None for h in cells.values())
            # Independent coordinate oracle, not the helper used by the factory.
            low, high = ({0,1}, {3}) if width == 4 else ({0,1,2,3,4}, {6,7,8,9})
            regions = {
                "north": {f"hex-{x}-{y}" for x in range(width) for y in low},
                "south": {f"hex-{x}-{y}" for x in range(width) for y in high},
                "west": {f"hex-{x}-{y}" for x in low for y in range(height)},
                "east": {f"hex-{x}-{y}" for x in high for y in range(height)},
            }
            assert any(ids["blue"] <= regions[a] and ids["red"] <= regions[b]
                       for a,b in [("north","south"),("south","north"),
                                   ("east","west"),("west","east")])
            for faction, group in by_faction.items():
                if name == "clear_square_factory":
                    assert 1 <= len(group) <= 2
                    assert len(ids[faction]) == len(group)
                    assert [u["longName"] for u in group] == [str(i) for i in range(len(group))]
                else:
                    parents = len(group) // 4
                    assert parents in (1, 2)
                    assert {u["longName"] for u in group} == {
                        f"{leaf}/{branch}/{parent}" for parent in range(1, parents+1)
                        for branch in (1,2) for leaf in (1,2)}


@pytest.mark.parametrize("name,options", FAMILIES)
def test_rng_restored_before_serialization_characterization(name, options, monkeypatch):
    # Ensure every enemy pair is in sight; predict draws with an independent RNG.
    combat = import_server("combat")
    monkeypatch.setitem(combat.sight, "infantry", 100)
    monkeypatch.setattr(combat, "pDetect", 0.5)
    random.seed(444)
    before = random.getstate()
    factory = getattr(import_server("scenario"), name)(**options, scenarioSeed=9)
    assert random.getstate() == before
    value = factory()
    counts = Counter(u["faction"] for u in value["units"])
    oracle = random.Random()
    oracle.setstate(before)
    for _ in range(2 * counts["blue"] * counts["red"]):
        oracle.random()
    assert random.getstate() == oracle.getstate()
    assert random.getstate() != before


@pytest.mark.parametrize("name,options", FAMILIES)
def test_detection_uses_ambient_rng_not_scenario_seed(name, options, monkeypatch):
    combat = import_server("combat")
    monkeypatch.setitem(combat.sight, "infantry", 100)
    monkeypatch.setattr(combat, "pDetect", 0.5)
    # A single pair makes the two ambient outcomes hand-checkable.
    options = dict(options)
    if name == "clear_square_factory":
        options.update(min_units=1, max_units=1)
    elif name == "hierarchy_factory":
        options.update(min_parents=1, max_parents=1, hierarchy_depth=2, hierarchy_branching=1)
    else:
        options.update(n_blue=1, n_red=1)
    factory = getattr(import_server("scenario"), name)
    random.seed(0)  # first two draws > .5
    first = factory(**options, scenarioSeed=5)()
    random.seed(4)  # first two draws < .5
    second = factory(**options, scenarioSeed=5)()
    assert without_detection(first) == without_detection(second)
    assert [u["detected"] for u in first["units"]] == [False, False]
    assert [u["detected"] for u in second["units"]] == [True, True]


@pytest.mark.parametrize("name,options", FAMILIES[:2])
def test_balanced_return_does_not_consume_rng(name, options):
    factory = getattr(import_server("scenario"), name)(**options, balance=True, scenarioSeed=1)
    factory()
    before = random.getstate()
    factory()
    assert random.getstate() == before


@pytest.mark.parametrize("name,options,error,message", [
    ("clear_square_factory", dict(size=3), "Exception", "Requested size (3) too small (minimum is 4)"),
    ("clear_square_factory", dict(size=4,min_units=9,max_units=9), "IndexError", "Cannot choose from an empty sequence"),
    ("clear_square_factory", dict(size=4,min_units=2,max_units=1), "ValueError", "empty range"),
    ("hierarchy_factory", dict(size=9), "Exception", "Requested size (9) too small (minimum is 10)"),
    ("hierarchy_factory", dict(hierarchy_depth=5), "IndexError", "list index out of range"),
    ("hierarchy_factory", dict(min_parents=2,max_parents=1), "ValueError", "empty range"),
    ("hierarchy_factory", dict(hierarchy_depth=1), "TypeError", "unsupported operand type(s) for +=: 'int' and 'NoneType'"),
    ("hierarchy_factory", dict(hierarchy_depth=0), "TypeError", "unsupported operand type(s) for +=: 'int' and 'NoneType'"),
    ("hierarchy_factory", dict(hierarchy_depth=2,hierarchy_branching=101), "IndexError", "list index out of range"),
    ("invasion_factory", dict(width=2,height=1), "KeyError", "hex-0--1"),
    ("invasion_factory", dict(width=2,height=4,n_blue=5,n_red=0), "IndexError", "Cannot choose from an empty sequence"),
    ("invasion_factory", dict(width=2,height=4,n_blue=0,n_red=4,num_cities=1), "IndexError", "Cannot choose from an empty sequence"),
], ids=["clear-too-small", "clear-over-capacity", "clear-reversed-counts",
        "hierarchy-too-small", "hierarchy-too-deep", "hierarchy-reversed-counts",
        "hierarchy-depth-one", "hierarchy-depth-zero", "hierarchy-over-capacity",
        "invasion-too-short", "invasion-over-capacity", "invasion-no-city-cells"])
def test_invalid_inputs_bounded_and_rng_leak(name, options, error, message, tmp_path):
    run_python(f'''
import random
from tests.support.imports import server_imports, import_server
with server_imports():
    random.seed(444)
    before = random.getstate()
    factory = getattr(import_server("scenario"), {name!r})(**{options!r}, scenarioSeed=7)
    assert random.getstate() == before
    try:
        factory()
    except Exception as exc:
        assert type(exc).__name__ == {error!r}, repr(exc)
        assert {message!r} in str(exc), repr(exc)
    else:
        raise AssertionError("Expected unsupported-input exception")
    assert random.getstate() != before, "Failure unexpectedly restored caller RNG"
''', cwd=tmp_path, timeout=10)


def test_hierarchy_cross_branch_collisions_characterization(tmp_path):
    run_python('''
from collections import Counter
from tests.support.imports import server_imports, import_server
with server_imports():
    value = import_server("scenario").hierarchy_factory(
        size=10, min_parents=2, max_parents=2, hierarchy_depth=3,
        hierarchy_branching=3, scenarioSeed=7)()
    assert len(value["units"]) == 36
    counts = Counter((u["faction"], u["hex"]) for u in value["units"])
    assert max(counts.values()) > 1
    # Each leaf sibling group removes its own occupied cells, but other
    # branches get a fresh candidate list and can reuse those cells.
    groups = {}
    for u in value["units"]:
        key = (u["faction"], u["longName"].split("/", 1)[1])
        groups.setdefault(key, []).append(u["hex"])
    assert all(len(set(hexes)) == 3 for hexes in groups.values())
''', cwd=tmp_path, timeout=10)


@pytest.mark.parametrize("name,options", [
    ("clear_square_factory", dict(size=4,min_units=-1,max_units=-1)),
    ("hierarchy_factory", dict(min_parents=1,max_parents=1,hierarchy_branching=0)),
    ("invasion_factory", dict(width=1,height=2,n_blue=-1,n_red=-1,num_cities=0)),
])
def test_nonpositive_counts_produce_empty_units_characterization(name, options, tmp_path):
    run_python(f'''
import random
from tests.support.imports import server_imports, import_server
with server_imports():
    random.seed(444)
    before = random.getstate()
    value = getattr(import_server("scenario"), {name!r})(**{options!r}, scenarioSeed=7)()
    assert value["units"] == []
    assert random.getstate() == before
''', cwd=tmp_path, timeout=10)


def test_city_attempts_can_repeat_and_invasion_score_is_configurable():
    value = import_server("scenario").invasion_factory(
        width=1, height=4, n_blue=0, n_red=0, num_cities=10,
        scenarioSeed=7, city_score=13)()
    cities = [h for h in value["map"]["hexes"] if h["terrain"] == "urban"]
    assert len(cities) == 2  # Ten placements into the two-cell red half.
    assert value["score"]["cityScore"] == 13


@pytest.mark.parametrize("depth,branching", [(2,1), (2,3), (3,2), (4,2)])
def test_hierarchy_names_depth_and_branching(depth, branching):
    value = import_server("scenario").hierarchy_factory(
        min_parents=1, max_parents=1, hierarchy_depth=depth,
        hierarchy_branching=branching, scenarioSeed=31)()
    expected = {"/".join(map(str, (*path, 1)))
                for path in product(range(1, branching+1), repeat=depth-1)}
    for faction in ("blue", "red"):
        names = [u["longName"] for u in value["units"] if u["faction"] == faction]
        assert len(names) == branching ** (depth-1)
        assert set(names) == expected


@pytest.mark.parametrize("name,options", FAMILIES[:2])
def test_square_city_attempts_are_not_unique_city_counts(name, options):
    value = getattr(import_server("scenario"), name)(
        **options, scenarioSeed=7, num_cities=101)()
    unique = sum(h["terrain"] == "urban" for h in value["map"]["hexes"])
    assert 0 < unique < 101
