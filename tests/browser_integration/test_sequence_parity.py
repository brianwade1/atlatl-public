"""S18-C: literal vertical-corridor oracles in even and odd columns."""

from copy import deepcopy

import pytest

pytestmark = [pytest.mark.browser, pytest.mark.integration]


@pytest.mark.parametrize("col", [0, 1], ids=["even-column", "odd-column"])
@pytest.mark.parametrize("kind", ["infantry", "mechinf", "armor", "artillery"])
@pytest.mark.parametrize("case", ["clear", "rough", "marsh", "water", "occupied"])
def test_corridor_movement_and_fire_have_independent_oracles(
        model_page, unit_world, make_map, make_unit, col, kind, case):
    # All off-corridor cells are impassable, so the only routes are vertical.
    # Infantry can pay one 100-point entry; mobile units can pay two 50-point
    # entries. Rough/marsh cost 100, except artillery cannot enter marsh.
    terrain = {(x, y): "water" for x in range(3) for y in range(4)}
    terrain.update({(col, y): "clear" for y in range(4)})
    if case in {"rough", "marsh", "water"}:
        terrain[col, 1] = case
    board = make_map(rows=4, cols=3, terrain_overrides=terrain)
    records = [make_unit("actor", unit_type=kind, hex=f"hex-{col}-0")]
    if case == "occupied":
        records.append(make_unit("blocker", hex=f"hex-{col}-2"))
    expected_moves = []
    if case != "water" and not (case == "marsh" and kind == "artillery"):
        expected_moves.append(f"hex-{col}-1")
        if case == "clear" and kind != "infantry":
            expected_moves.append(f"hex-{col}-2")
    _, python_board, units = unit_world(records, map_input=board)
    before = deepcopy(records)
    assert sorted(h.id for h in units.units()[0].findMoveTargets(python_board, units)) == expected_moves
    browser_moves = model_page.evaluate('''c => {
        GameMap.fromPortable(c.map); Unit.fromPortable2(c.units);
        for (let i=0;i<c.units.length;i++) Unit.units[i].partialObsUpdate(c.units[i]);
        return Unit.units[0].findMoveTargets().map(h => h.id).sort();
    }''', {"map": board, "units": records})
    assert browser_moves == expected_moves
    assert records == before


@pytest.mark.parametrize("col", [0, 1], ids=["even-column", "odd-column"])
@pytest.mark.parametrize("kind", ["infantry", "mechinf", "armor", "artillery"])
def test_vertical_fire_ring_excludes_friendly_removed_and_distant_units(
        model_page, unit_world, make_map, make_unit, col, kind):
    board = make_map(rows=4, cols=3)
    records = [
        make_unit("actor", unit_type=kind, hex=f"hex-{col}-0"),
        make_unit("near", "red", hex=f"hex-{col}-1"),
        make_unit("outer", "red", hex=f"hex-{col}-2"),
        make_unit("distant", "red", hex=f"hex-{col}-3"),
        make_unit("friend", hex=f"hex-{2 if col == 0 else 0}-0"),
        make_unit("removed", "red", hex=None, ineffective=True, can_move=False),
    ]
    expected = ["red near", "red outer"] if kind == "artillery" else ["red near"]
    _, _, units = unit_world(records, map_input=board)
    assert sorted(u.uniqueId for u in units.units()[0].findFireTargets(units)) == expected
    actual = model_page.evaluate('''c => {
        GameMap.fromPortable(c.map); Unit.fromPortable2(c.units);
        for (let i=0;i<c.units.length;i++)
            Unit.units[i].partialObsUpdate({...c.units[i],hex:c.units[i].hex ?? 'fog'});
        return Unit.units[0].findFireTargets().map(u => u.uniqueId).sort();
    }''', {"map": board, "units": records})
    assert actual == expected
