"""S02 consumers validate inputs/oracles; comprehensive engine coverage is S03+."""

import json

import numpy as np
import pytest

from tests.support.builders import load_fixture
from tests.support.imports import import_server

pytestmark = pytest.mark.core


@pytest.mark.parametrize("case", ["first", "second"])
@pytest.mark.unit
def test_factories_do_not_share_mutable_inputs(case, make_map, make_unit, make_scenario, make_state):
    map_data = make_map(terrain_overrides={(1, 2): "urban"})
    units = [make_unit(), make_unit("B")]
    scenario = make_scenario(map_data, units)
    state = make_state(units, city_owner={"hex-1-2": "blue"})
    scenario["map"]["hexes"][0]["terrain"] = "water"
    scenario["units"][0]["currentStrength"] = 1
    state["units"][1]["longName"] = "changed"
    assert map_data["hexes"][0]["terrain"] == "clear"
    assert units[0]["currentStrength"] == 100
    assert units[1]["longName"] == "B"
    assert make_map()["hexes"][0]["terrain"] == "clear"
    assert make_scenario(units=[])["units"] == []


@pytest.mark.parametrize("path", [
    "maps/hex_geometry.json", "scenarios/movement_corridors.json",
    "scenarios/combat_duel.json", "scenarios/setup_exchange.json",
    "scenarios/city_scoring.json", "observations/fog_sequence.json",
    "observations/rectangular_features.json", "scenarios/tiny_episode.json",
    "scenarios/hierarchy_units.json", "protocol/protocol_messages.json",
    "replay/replay_sequences.json", "models/numeric.json",
], ids=lambda path: path.split("/")[-1][:-5])
@pytest.mark.unit
def test_reusable_json_is_fresh(path):
    original = load_fixture(path)
    mutated = load_fixture(path)
    mutated.clear()
    assert load_fixture(path) == original
    assert original["note"]


@pytest.mark.parametrize("oracle_index", [0, 1, 2], ids=["corner-even", "interior-odd", "interior-even"])
@pytest.mark.unit
def test_hand_authored_geometry_loads(engine_imports, hex_geometry, oracle_index):
    module = import_server("map")
    map_data = module.MapData()
    module.fromPortable(hex_geometry["map"], map_data)
    oracle = hex_geometry["oracles"][oracle_index]
    cell = map_data.hexIndex[oracle["id"]]
    assert [cell.x_grid, cell.y_grid] == oracle["center"]
    assert [[p["x"], p["y"]] for p in cell.getPoints(map_data)] == oracle["vertices"]
    assert [h.id for h in module.getNeighborHexes(cell, map_data)] == oracle["neighbors"]
    assert map_data.getDimensions() == hex_geometry["dimensions"]


@pytest.mark.parametrize("subset, dimensions", [
    ("single", {"width": 1, "height": 1}),
    ("empty", {"width": 0, "height": 0}),
    ("irregular", {"width": 3, "height": 2}),
])
@pytest.mark.unit
def test_geometry_subsets(engine_imports, hex_geometry, subset, dimensions):
    module = import_server("map")
    portable = hex_geometry["map"]
    portable["hexes"] = [h for h in portable["hexes"]
        if f"hex-{h['x_offset']}-{h['y_offset']}" in hex_geometry["subsets"][subset]]
    map_data = module.MapData()
    module.fromPortable(portable, map_data)
    assert map_data.getDimensions() == dimensions


@pytest.mark.integration
def test_scripted_episode_has_independent_final_score(engine_imports, tiny_episode):
    game = import_server("game").Game(tiny_episode["scenario"])
    state = game.initial_state()
    for action in tiny_episode["actions"]:
        assert action in game.legal_actions(state)
        state = game.transition(state, action)
    assert game.is_terminal(state)
    assert game.score(state) == tiny_episode["final_score"] == 50
    assert state["status"]["phaseCount"] == tiny_episode["final_phase"] == 4


@pytest.mark.parametrize("unit_type", ["infantry", "armor", "artillery"])
@pytest.mark.parametrize("terrain", ["clear", "rough", "marsh", "water", "urban", "unused"])
@pytest.mark.integration
def test_corridor_variants_are_valid_inputs(engine_imports, movement_corridors, make_unit, unit_type, terrain):
    map_module, unit_module = import_server("map"), import_server("unit")
    portable = movement_corridors["line"]
    assert portable["hexes"][1]["terrain"] == "clear"
    portable["hexes"][1]["terrain"] = terrain
    map_data, unit_data = map_module.MapData(), unit_module.UnitData()
    map_module.fromPortable(portable, map_data)
    unit = unit_module.Unit(make_unit(unit_type=unit_type), unit_data, map_data)
    assert unit.type == unit_type
    assert map_data.hexIndex["hex-0-1"].terrain == terrain
    if terrain == "clear":
        targets = {h.id for h in unit.findMoveTargets(map_data, unit_data)}
        assert movement_corridors["exact_budget"][unit_type] in targets
        assert movement_corridors["over_budget"][unit_type] not in targets


@pytest.mark.integration
def test_corridor_blocker_and_alternative(engine_imports, movement_corridors, make_unit):
    map_module, unit_module = import_server("map"), import_server("unit")
    for layout in ("line", "alternative"):
        map_data, unit_data = map_module.MapData(), unit_module.UnitData()
        map_module.fromPortable(movement_corridors[layout], map_data)
        actor = unit_module.Unit(make_unit(unit_type="armor"), unit_data, map_data)
        unit_module.Unit(movement_corridors["blocker"], unit_data, map_data)
        targets = {h.id for h in actor.findMoveTargets(map_data, unit_data)}
        assert "hex-0-1" not in targets
        if layout == "line":
            assert targets == set()
        else:
            assert "hex-1-1" in targets  # Two clear steps via hex-1-0 cost 100.


@pytest.mark.parametrize("owner", ["blue", "red", "neutral"])
@pytest.mark.integration
def test_city_fixture_ownership_variants(engine_imports, city_scoring, owner):
    scenario = city_scoring["scenario"]
    scenario["map"]["initialCityOwnership"] = owner
    game = import_server("game").Game(scenario)
    state = game.transition(game.initial_state(), {"type": "pass"})
    assert game.score(state) == 2 * city_scoring["per_city"][owner]


@pytest.mark.parametrize("role", ["white", "blue", "red"])
@pytest.mark.integration
def test_fog_oracles_match_controlled_detection(engine_imports, fog_sequence, role, detection_draws):
    game = import_server("game").Game(fog_sequence["scenario"])
    detection_draws([0.25] * 20)
    for frame in fog_sequence["frames"]:
        expected = frame["truth"] if role == "white" else frame["observations"][role]
        assert game.observation(frame["truth"], role) == expected


@pytest.mark.integration
def test_duel_and_setup_inputs(engine_imports, combat_duel, setup_exchange):
    game_class = import_server("game").Game
    game = game_class(combat_duel["scenario"])
    state = game.transition(game.initial_state(), combat_duel["action"])
    assert state["units"][2]["currentStrength"] == combat_duel["expected_strength"]
    assert game.score(state) == combat_duel["expected_score"]
    assert state["status"]["phaseCount"] == 0
    setup = game_class(setup_exchange["scenario"])
    for action in (setup_exchange["move"], setup_exchange["exchange"]):
        assert setup._is_legal_setup(setup.initial_state(), action)


@pytest.mark.integration
def test_protocol_replay_and_numeric_inputs(protocol_messages, replay_sequences, model_and_numeric_data):
    for message in protocol_messages["valid"].values():
        assert json.loads(json.dumps(message)) == message
    assert replay_sequences["normal"][0]["type"] == "parameters"
    assert replay_sequences["two_games"][2]["type"] == "parameters"
    assert replay_sequences["two_games"][2]["parameters"]["score"]["maxPhases"] == 2
    with np.load(model_and_numeric_data["archive"]) as archive:
        np.testing.assert_array_equal(archive["matrix"], [[1, 2], [3, 4]])
        assert archive["matrix"].dtype == np.float32
        np.testing.assert_array_equal(archive["results"].mean(axis=1), [2, 3])
    np.testing.assert_array_equal(np.loadtxt(model_and_numeric_data["data_file"]), [1, 2, 3, 4])


@pytest.mark.parametrize("terrain", ["clear", "rough", "marsh", "water", "urban", "unused"])
@pytest.mark.integration
def test_rectangular_feature_inputs(engine_imports, rectangular_features, terrain):
    fixture = rectangular_features
    scenario = fixture["scenario"]
    for cell in scenario["map"]["hexes"]:
        if [cell["x_offset"], cell["y_offset"]] == fixture["variant_coordinate"]:
            cell["terrain"] = terrain
    game = import_server("game").Game(scenario)
    assert game.mapData.getDimensions() == {"width": 4, "height": 3}
    assert game.mapData.hexIndex["hex-1-2"].terrain == terrain
    assert [(u["faction"], u["hex"], u["currentStrength"]) for u in fixture["state"]["units"]] == [
        ("blue", "hex-0-2", 75), ("red", "hex-3-0", 60)]
    assert fixture["state"]["status"]["phaseCount"] == 2
    assert game.score(fixture["state"]) == -7


@pytest.mark.integration
def test_hierarchy_input_center_oracle(engine_imports, hierarchy_units):
    scenario = hierarchy_units["scenario"]
    game = import_server("game").Game(scenario)
    units = [u for u in scenario["units"] if u["faction"] == "blue" and not u["ineffective"]]
    points = [game.mapData.hexIndex[u["hex"]] for u in units]
    total = sum(u["currentStrength"] for u in units)
    center = [sum(getattr(p, axis) * u["currentStrength"] for p, u in zip(points, units)) / total
              for axis in ("x_grid", "y_grid")]
    assert center == pytest.approx(hierarchy_units["blue_weighted_center"])
    assert [sum(getattr(p, axis) for p in points) / len(points)
            for axis in ("x_grid", "y_grid")] == hierarchy_units["blue_unweighted_center"]
    unit_module = import_server("unit")
    unit_data = unit_module.UnitData()
    unit_module.fromPortable(scenario["units"], unit_data, game.mapData)
    assert import_server("abstract_state").getCM(unit_data.getFaction("blue")) == pytest.approx(
        hierarchy_units["blue_euclidean_center"])
