"""S04 finite detection draws, sight boundaries, and observer serialization."""

from copy import deepcopy

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]


@pytest.mark.parametrize("draw,expected", [(0.499, True), (0.5, False), (0.501, False)],
                         ids=["below", "equal", "above"])
def test_detection_probability_boundary(unit_world, make_unit, detection_draws,
                                         monkeypatch, draw, expected):
    _, _, data = unit_world([make_unit(), make_unit(faction="red", hex="hex-0-2")])
    monkeypatch.setattr(import_server("combat"), "pDetect", 0.5)
    detection_draws([draw, draw])
    data.updateDetectionStatus()
    assert [u.detected for u in data.units()] == [expected, expected]


def test_detection_directions_are_independent(unit_world, make_unit, detection_draws, monkeypatch):
    _, _, data = unit_world([make_unit(), make_unit(faction="red", hex="hex-0-1")])
    monkeypatch.setattr(import_server("combat"), "pDetect", 0.5)
    detection_draws([0.1, 0.9])
    data.updateDetectionStatus()
    assert [u.detected for u in data.units()] == [True, False]


def test_retained_detection_leaving_sight_and_reacquisition(unit_world, make_unit, detection_draws):
    _, board, data = unit_world([make_unit(detected=True),
                                make_unit(faction="red", hex="hex-0-2", detected=True)],
                               rows=4, cols=1)
    blue, red = data.units()
    detection_draws([])  # Previous detection short-circuits randomness in sight.
    data.updateDetectionStatus()
    assert (blue.detected, red.detected) == (True, True)
    red.setHex(board.hexIndex["hex-0-3"], data)
    data.updateDetectionStatus()
    assert (blue.detected, red.detected) == (False, False)
    red.setHex(board.hexIndex["hex-0-2"], data)
    detection_draws([0, 0])
    data.updateDetectionStatus()
    assert (blue.detected, red.detected) == (True, True)


@pytest.mark.parametrize("case", ["friendly", "ineffective-first", "ineffective-last", "alone", "empty"])
def test_no_observer_clears_detection_without_random_draws(unit_world, make_unit, detection_draws, case):
    sources = [make_unit(detected=True), make_unit(faction="red", hex="hex-0-1", detected=True)]
    if case == "friendly":
        sources[1].update(faction="blue", longName="B")
    elif case.startswith("ineffective"):
        sources[0 if case.endswith("first") else 1].update(ineffective=True, hex=None)
    else:
        sources = sources[:1] if case == "alone" else []
    _, _, data = unit_world(sources)
    detection_draws([])
    data.updateDetectionStatus()
    assert all(not u.detected for u in data.units())


def test_sight_belongs_to_observer_type(unit_world, make_unit, detection_draws, monkeypatch):
    _, _, data = unit_world([make_unit(),
                            make_unit(faction="red", unit_type="artillery", hex="hex-0-2")])
    monkeypatch.setitem(import_server("combat").sight, "infantry", 1)
    detection_draws([0])
    data.updateDetectionStatus()
    assert [u.detected for u in data.units()] == [True, False]


@pytest.mark.parametrize("observer", ["white", "blue", "red"])
def test_observer_fields_and_serialization_side_effect(unit_world, make_unit, detection_draws,
                                                      monkeypatch, observer):
    sources = [make_unit(strength=72.5), make_unit(faction="red", hex="hex-0-1", can_move=False)]
    _, _, data = unit_world(sources)
    monkeypatch.setattr(import_server("combat"), "pDetect", 0.5)
    detection_draws([0.9, 0.9, 0.1, 0.1])
    expected = deepcopy(sources)
    for record in expected:
        if observer != "white" and record["faction"] != observer:
            record["hex"] = "fog"
    first = data.toPortable(observer)
    assert first == expected  # Exact keys include strength/flags/name even when hidden.
    second = data.toPortable(observer)
    assert second == [dict(record, detected=True) for record in sources]
    assert [u.detected for u in data.units()] == [True, True]
    assert first == expected
    second[0]["currentStrength"] = 0
    assert data.units()[0].currentStrength == 72.5


@pytest.mark.parametrize("observer", ["white", "blue", "red"])
def test_removed_unit_serialization(unit_world, make_unit, detection_draws, observer):
    sources = [make_unit(), make_unit(faction="red", hex=None, ineffective=True)]
    _, _, data = unit_world(sources)
    detection_draws([])
    expected = deepcopy(sources)
    for record in expected:
        if observer != "white" and record["faction"] != observer:
            record["hex"] = "fog"
    assert data.toPortable(observer) == expected


@pytest.mark.parametrize("operation", ["updateDetectionStatus", "toPortable"])
def test_live_unplaced_enemy_characterization(unit_world, make_unit, detection_draws, operation):
    _, _, data = unit_world([make_unit(detected=True),
                            make_unit(faction="red", hex=None, detected=True)])
    detection_draws([])
    with pytest.raises(AttributeError, match="^'NoneType' object has no attribute 'x_grid'$"):
        getattr(data, operation)()
    # The failed operation has already cleared detection on both units.
    assert [u.detected for u in data.units()] == [False, False]


@pytest.mark.parametrize("observer", ["white", "blue", "red"])
def test_unplaced_unit_without_enemy_characterization(unit_world, make_unit, detection_draws, observer):
    source = make_unit(hex=None, detected=True)
    _, _, data = unit_world([source])
    detection_draws([])
    assert data.toPortable(observer) == [dict(source, detected=False,
                                             hex="fog" if observer == "red" else None)]
