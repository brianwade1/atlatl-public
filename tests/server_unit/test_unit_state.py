"""S04 unit identity, occupancy and partial-observation state contracts."""

from copy import deepcopy

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("explicit", [False, True], ids=["defaults", "explicit"])
def test_construction_and_registration(unit_world, make_unit, explicit):
    source = make_unit(name="1 Platoon", strength=73.5, detected=True,
                       can_move=True, ineffective=True)
    if not explicit:
        for field in ("detected", "canMove", "ineffective"):
            del source[field]
    before = deepcopy(source)
    module, board, data = unit_world([source, make_unit(faction="red", hex=None)])
    blue, red = data.units()
    assert blue.uniqueId == "blue 1 Platoon"
    assert blue.type == "infantry"
    assert blue.currentStrength == 73.5
    assert (blue.canMove, blue.ineffective, blue.detected) == (explicit,) * 3
    assert blue.hex is board.hexIndex["hex-0-0"]
    assert data.unitIndex == {"blue 1 Platoon": blue, "red A": red}
    assert data.occupancy == {"hex-0-0": [blue]}
    assert red.hex is None
    assert data.getFaction("blue") == [blue]
    assert data.getFaction("red") == [red]
    assert data.getFaction("white") == []
    data.units().clear()
    assert data.units() == [blue, red]
    assert source == before


def test_empty_unit_data(unit_world):
    _, _, data = unit_world()
    assert data.units() == data.getFaction("blue") == []
    assert data.unitIndex == data.occupancy == {}
    assert not data.hexFull("hex-0-0")


def test_duplicate_ids_characterization(unit_world, make_unit):
    module, board, data = unit_world([make_unit()])
    old = data.units()[0]
    replacement = module.Unit(make_unit(hex="hex-0-1"), data, board)
    assert data.units() == [replacement]
    # Unsupported duplicate input replaces the index but leaves the old occupant.
    assert data.occupancy == {"hex-0-0": [old], "hex-0-1": [replacement]}


def test_placement_removal_and_replacement(unit_world, make_unit):
    _, board, data = unit_world([make_unit(), make_unit(name="B", hex="hex-1-0")])
    actor, other = data.units()
    for destination in ("hex-0-1", "hex-0-1", "hex-0-2"):
        actor.setHex(board.hexIndex[destination], data)
        assert actor.hex is board.hexIndex[destination]
        assert data.occupancy[destination] == [actor]
        assert sum(occupants.count(actor) for occupants in data.occupancy.values()) == 1
        assert data.occupancy["hex-1-0"] == [other]
    assert data.occupancy["hex-0-0"] == data.occupancy["hex-0-1"] == []
    for _ in range(2):
        actor.remove(data)
        assert actor.hex is None
        assert all(actor not in occupants for occupants in data.occupancy.values())
        assert data.unitIndex["blue A"] is actor
    actor.setHex(board.hexIndex["hex-0-0"], data)
    assert data.occupancy["hex-0-0"] == [actor]
    assert data.occupancy["hex-0-2"] == []


@pytest.mark.parametrize("limit,expected", [(0, [False, True, True]),
                                            (1, [False, False, True]),
                                            (2, [False, False, False])])
def test_hex_full_characterization(unit_world, make_unit, monkeypatch, limit, expected):
    _, _, data = unit_world([make_unit()])
    monkeypatch.setattr(import_server("mobility"), "stackingLimit", limit)
    data.occupancy["empty"] = []
    # An absent occupancy key returns False even for a zero stacking limit.
    assert [data.hexFull(h) for h in ("absent", "empty", "hex-0-0")] == expected


@pytest.mark.parametrize("faction", ["blue", "red"])
@pytest.mark.parametrize("value", [False, True])
def test_set_can_move(unit_world, make_unit, faction, value):
    sources = [make_unit(name=str(i), faction=side, ineffective=ineffective,
                         can_move=not value, hex=None)
               for i, (side, ineffective) in enumerate([
                   ("blue", False), ("red", False), ("blue", True), ("red", True)])]
    _, _, data = unit_world(sources)
    data.setCanMove(value, faction)
    assert [u.canMove for u in data.units()] == [
        value if faction == "blue" else not value,
        value if faction == "red" else not value, False, False]


def test_partial_observation_visible_hidden_visible(unit_world, make_unit):
    _, board, data = unit_world([make_unit(detected=True)])
    actor = data.units()[0]
    steps = [("hex-0-1", False, 82.5, False), ("fog", False, 80, True),
             ("hex-0-2", False, 75, True), ("hex-0-2", True, 30, False),
             ("hex-0-0", False, 100, True)]
    for position, ineffective, strength, movable in steps:
        observation = make_unit(hex=position, ineffective=ineffective,
                                strength=strength, can_move=movable, detected=False)
        before = deepcopy(observation)
        actor.partialObsUpdate(observation, data, board)
        expected = None if position == "fog" or ineffective else position
        assert (actor.hex.id if actor.hex else None) == expected
        assert (actor.currentStrength, actor.canMove, actor.ineffective) == (
            strength, movable, ineffective)
        assert {key: occupants for key, occupants in data.occupancy.items() if occupants} == (
            {} if expected is None else {expected: [actor]})
        assert data.unitIndex == {"blue A": actor}
        assert actor.detected is True  # Characterization: this method does not copy detected.
        assert observation == before


def test_fog_is_not_ground_truth_input(unit_world, make_unit):
    module, board, data = unit_world()
    with pytest.raises(KeyError, match="^'fog'$"):
        module.fromPortable([make_unit(hex="fog")], data, board)
    assert data.unitIndex == data.occupancy == {}


@pytest.mark.parametrize("position", [None, "hex-0-1"])
def test_portable_copy_omits_detection_and_is_independent(unit_world, make_unit,
                                                        detection_draws, position):
    source = make_unit(hex=position, detected=True, strength=62.5)
    _, _, data = unit_world([source])
    detection_draws([])
    actor = data.units()[0]
    expected = {key: value for key, value in source.items() if key != "detected"}
    output = actor.portableCopy()
    assert output == expected
    assert actor.detected is True
    output["currentStrength"] = 0
    assert actor.currentStrength == 62.5
