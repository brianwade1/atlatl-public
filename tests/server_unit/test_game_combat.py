"""S05 combat oracles are literal arithmetic, independent of engine tables."""

from copy import deepcopy

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]

# Each tuple: shooter type, target type, terrain, shooter strength, target
# strength, remaining strength, credited loss, removed. Below-threshold cleanup
# credits the remaining positive strength but does not set that strength to zero.
CASES = [
    ("infantry", "infantry", "clear", 100, 100, 50, 50, False),
    ("infantry", "infantry", "clear", 100, 75, 25, 75, True),
    ("infantry", "infantry", "urban", 100, 100, 75, 25, False),
    ("infantry", "infantry", "rough", 100, 100, 75, 25, False),
    ("infantry", "infantry", "water", 100, 100, 50, 50, False),
    ("infantry", "infantry", "unused", 100, 100, 50, 50, False),
    ("infantry", "infantry", "marsh", 100, 100, 50, 50, False),
    ("infantry", "armor", "clear", 100, 100, 75, 25, False),
    ("mechinf", "infantry", "clear", 100, 100, 62.5, 37.5, False),
    ("armor", "mechinf", "clear", 100, 100, 62.5, 37.5, False),
    ("artillery", "armor", "marsh", 100, 100, 50, 50, False),
    ("infantry", "artillery", "clear", 100, 100, 25, 100, True),
    ("armor", "armor", "urban", 100, 100, 50, 50, False),
    ("armor", "infantry", "rough", 100, 100, 87.5, 12.5, False),
    ("artillery", "mechinf", "marsh", 100, 100, 25, 100, True),
    ("infantry", "infantry", "clear", 60.5, 90.75, 60.5, 30.25, False),
    ("infantry", "infantry", "clear", 100, 99.9, 49.9, 99.9, True),
    ("infantry", "infantry", "clear", 99.8, 100, 50.1, 49.9, False),
    ("infantry", "mechinf", "clear", 100, 100, 50, 50, False),
    ("mechinf", "mechinf", "clear", 100, 100, 50, 50, False),
    ("mechinf", "armor", "clear", 100, 100, 62.5, 37.5, False),
    ("mechinf", "artillery", "clear", 100, 100, 25, 100, True),
    ("armor", "artillery", "clear", 100, 100, 50, 50, False),
    ("artillery", "infantry", "clear", 100, 100, 50, 50, False),
    ("artillery", "artillery", "clear", 100, 100, 25, 100, True),
]


@pytest.mark.parametrize("attacker,target,terrain,attack_strength,target_strength,remaining,credit,removed",
    CASES, ids=["threshold-equal", "threshold-cleanup", "urban-cover", "rough-cover",
               "water", "unused", "marsh-infantry", "infantry-armor", "mech-infantry",
               "armor-mech", "artillery-marsh-armor", "infantry-artillery", "urban-armor",
               "armor-covered-infantry", "artillery-marsh-mech", "fractional",
               "threshold-below", "threshold-above", "infantry-mech", "mech-mech",
               "mech-armor", "mech-artillery", "armor-artillery", "artillery-infantry",
               "artillery-artillery"])
@pytest.mark.parametrize("faction,score_factor", [("blue", 1), ("red", -2)])
def test_combat_results(game_factory, make_map, make_unit, unit_world, attacker, target, terrain,
                        attack_strength, target_strength, remaining, credit, removed, faction, score_factor):
    enemy = "red" if faction == "blue" else "blue"
    board = make_map(terrain_overrides={(1, 0): terrain})
    game = game_factory(map_data=board, units=[
        make_unit("shooter", faction, attacker, attack_strength),
        make_unit("reserve", faction, hex="hex-0-2"),
        make_unit("target", enemy, target, target_strength, hex="hex-1-0", can_move=False)])
    state = game.initial_state()
    state["status"]["onMove"] = faction
    for u in state["units"]:
        u["canMove"] = u["faction"] == faction
    before = deepcopy(state)
    result = game.transition(state, {"type": "fire", "source": f"{faction} shooter", "target": f"{enemy} target"})
    assert state == before
    shooter, reserve, victim = result["units"]
    assert shooter["currentStrength"] == attack_strength
    assert shooter["hex"] == "hex-0-0"
    assert not shooter["canMove"]
    assert reserve["canMove"] and reserve["currentStrength"] == 100
    assert victim["currentStrength"] == pytest.approx(remaining)
    assert victim["ineffective"] is removed
    assert victim["hex"] == (None if removed else "hex-1-0")
    assert not victim["canMove"]
    assert game.score(result) == pytest.approx(credit * score_factor)
    assert result["status"] == dict(before["status"], score=pytest.approx(credit * score_factor))
    _, _, rebuilt = unit_world(result["units"], map_input=board)
    assert set(rebuilt.occupancy) == ({"hex-0-0", "hex-0-2"} if removed else
                                    {"hex-0-0", "hex-0-2", "hex-1-0"})
    rebuilt_target = rebuilt.unitIndex[f"{enemy} target"]
    if removed:
        assert rebuilt_target.hex is None
    else:
        assert rebuilt_target.hex.id == "hex-1-0"


def test_defensive_term_clamps_damage_to_zero(game_factory, make_unit, monkeypatch):
    game = game_factory(units=[make_unit(), make_unit("B", hex="hex-0-2"),
                              make_unit(faction="red", hex="hex-1-0", can_move=False)])
    monkeypatch.setitem(import_server("combat").defensivefp["infantry"], "infantry", 2)
    result = game.transition(game.initial_state(), {"type": "fire", "source": "blue A", "target": "red A"})
    assert result["units"][2]["currentStrength"] == 100
    assert result["units"][2]["hex"] == "hex-1-0"
    assert not result["units"][2]["ineffective"]
    assert not result["units"][0]["canMove"]
    assert game.score(result) == 0


@pytest.mark.parametrize("faction,factor", [("blue", 1), ("red", -2)])
def test_overkill_credit_characterization(game_factory, make_unit, make_map, faction, factor):
    enemy = "red" if faction == "blue" else "blue"
    game = game_factory(map_data=make_map(terrain_overrides={(1, 0): "marsh"}), units=[
        make_unit(faction=faction), make_unit("reserve", faction, hex="hex-0-2"),
        make_unit(faction=enemy, unit_type="artillery", strength=60, hex="hex-1-0", can_move=False)])
    state = game.initial_state()
    state["status"]["onMove"] = faction
    for unit in state["units"]:
        unit["canMove"] = unit["faction"] == faction
    result = game.transition(state, {"type": "fire", "source": f"{faction} A", "target": f"{enemy} A"})
    # 100 * 1.5 * 2 * 0.5 = 150 damage against only 60 strength.
    assert result["units"][2]["currentStrength"] == -90
    assert result["units"][2]["ineffective"]
    assert result["units"][2]["hex"] is None
    assert game.score(result) == 150 * factor


def test_last_shooter_advances_but_elimination_does_not_end_match(game_factory, make_unit):
    game = game_factory(units=[make_unit(), make_unit(faction="red", strength=75,
                                                    hex="hex-1-0", can_move=False)])
    result = game.transition(game.initial_state(), {"type": "fire", "source": "blue A", "target": "red A"})
    assert result["status"] == {"cityOwner": {}, "score": 75, "phaseCount": 1,
                                "isTerminal": False, "onMove": "red", "setupMode": False}
    assert all(not u["canMove"] for u in result["units"])
    assert game.legal_actions(result) == [{"type": "pass"}]
