"""S05 status rules, scoring and phase boundaries."""

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("configured", [False, True], ids=["defaults", "configured"])
def test_construction_and_portable_ownership(unit_world, make_map, make_scenario, configured):
    board_input = make_map(terrain_overrides={(0, 0): "urban", (1, 0): "urban"},
                           setup_overrides={(0, 0): "setup-type-blue"})
    board_input["initialCityOwnership"] = "red"
    scenario = make_scenario(board_input, max_phases=6, city_score=10, loss_penalty=-3)
    if not configured:
        del scenario["score"]
    _, board, _ = unit_world(map_input=board_input)
    cls = import_server("status").Status
    status = cls(scenario, board)
    assert (status.max_phases, status.total_city_score_per_phase,
            status.score_per_blue_kill, status.score_per_red_kill,
            status.score_per_city_per_phase) == (
                (6, 10, -3, 1, 5) if configured else (20, 24, -2, 1, 12))
    portable = status.toPortable()
    assert portable == {"cityOwner": {"hex-0-0": "red", "hex-1-0": "red"},
                        "score": 0, "phaseCount": 0, "isTerminal": False,
                        "onMove": "blue", "setupMode": True}
    portable.update(score=-7.5, phaseCount=3, isTerminal=True, onMove="red", setupMode=False)
    restored = cls.fromPortable(portable, scenario, board)
    assert restored.toPortable() == portable
    assert restored.ownerD is not portable["cityOwner"]
    # Characterization: export shares owners; import copies owners.
    assert status.toPortable()["cityOwner"] is status.ownerD
    restored.ownerD["hex-0-0"] = "blue"
    assert portable["cityOwner"]["hex-0-0"] == "red"


@pytest.mark.parametrize("faction,penalty,delta", [
    ("red", -2, 12.5), ("blue", -2, -25), ("blue", -3, -37.5), ("blue", 0, 0)])
def test_kill_score_accumulates(unit_world, make_scenario, faction, penalty, delta):
    _, board, _ = unit_world()
    status = import_server("status").Status(make_scenario(loss_penalty=penalty), board)
    status.score = 4
    assert status.dscoreKill(faction, 12.5) == delta
    assert status.score == 4 + delta


def test_city_shares_neutral_vacancy_and_capture(unit_world, make_map, make_unit, make_scenario):
    portable = make_map(terrain_overrides={(0, 0): "urban", (1, 0): "urban", (2, 0): "urban"})
    _, board, data = unit_world([make_unit(), make_unit(faction="red", hex="hex-1-0")],
                                map_input=portable)
    status = import_server("status").Status(make_scenario(portable, city_score=15), board)
    assert status.score_per_city_per_phase == 5
    assert set(status.ownerD.values()) == {"neutral"}
    assert status.endPhaseDeltaCityScore(data) == 0
    assert status.ownerD == {"hex-0-0": "blue", "hex-1-0": "red", "hex-2-0": "neutral"}
    data.unitIndex["blue A"].remove(data)
    status.updateCityOwnership(data)
    assert status.ownerD["hex-0-0"] == "blue"
    data.unitIndex["red A"].setHex(board.hexIndex["hex-0-0"], data)
    assert status.endPhaseDeltaCityScore(data) == -10
    assert status.ownerD == {"hex-0-0": "red", "hex-1-0": "red", "hex-2-0": "neutral"}
    assert status.score == 0  # Computing a delta does not itself credit it.


def test_zero_cities(unit_world, make_scenario):
    _, board, data = unit_world()
    status = import_server("status").Status(make_scenario(city_score=24), board)
    assert status.ownerD == {}
    assert status.score_per_city_per_phase == status.endPhaseDeltaCityScore(data) == 0


@pytest.mark.parametrize("available,ineffective,complete", [
    (False, False, True), (True, False, False), (True, True, True)])
def test_phase_complete_effective_availability(unit_world, make_unit, make_scenario,
                                             available, ineffective, complete):
    _, board, data = unit_world([make_unit(can_move=available, ineffective=ineffective)])
    status = import_server("status").Status(make_scenario(), board)
    assert status.phaseComplete(data) is complete


def test_empty_and_eliminated_factions_do_not_end_match(unit_world, make_unit, make_scenario):
    for units in ([], [make_unit()], [make_unit(ineffective=True)]):
        _, board, data = unit_world(units)
        status = import_server("status").Status(make_scenario(max_phases=2), board)
        for phase, expected in [(0, False), (1, False), (2, True), (3, True)]:
            status.phases_complete = phase
            assert status.matchComplete(data) is expected
        if not units:
            assert status.phaseComplete(data)


def test_advance_phase_flags_and_terminal_boundary(unit_world, make_unit, make_scenario):
    _, board, data = unit_world([make_unit(), make_unit(faction="red", hex="hex-3-2", can_move=False),
                                make_unit("dead", hex=None, ineffective=True)])
    status = import_server("status").Status(make_scenario(max_phases=2), board)
    status.advancePhase(data)
    assert (status.on_move, status.phases_complete, status.is_terminal) == ("red", 1, False)
    assert [u.canMove for u in data.units()] == [False, True, False]
    status.advancePhase(data)
    assert (status.on_move, status.phases_complete, status.is_terminal) == ("blue", 2, True)
    # Characterization: terminal return occurs before flags are reset.
    assert [u.canMove for u in data.units()] == [False, True, False]


@pytest.mark.parametrize("phase", [2, 3], ids=["at-limit", "past-limit"])
def test_advance_past_limit_characterization(unit_world, make_scenario, phase):
    _, board, data = unit_world()
    status = import_server("status").Status(make_scenario(max_phases=2), board)
    status.phases_complete = phase
    status.advancePhase(data)
    assert status.phases_complete == phase + 1
    assert status.matchComplete(data)
    assert status.is_terminal is False  # advancePhase tests equality, not >=.


def test_phase_complete_counts_off_faction_characterization(unit_world, make_unit, make_scenario):
    _, board, data = unit_world([make_unit(faction="red")])
    status = import_server("status").Status(make_scenario(), board)
    assert status.on_move == "blue"
    assert not status.phaseComplete(data)
