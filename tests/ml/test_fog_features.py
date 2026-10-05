"""Temporal fog features use real map/unit objects and controlled snapshots."""

import numpy as np
import pytest
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.ml, pytest.mark.unit]


@pytest.mark.parametrize("role", ["blue", "red"])
def test_trails_counts_and_returned_alias(obsmod, unit_world, make_unit, role):
    enemy = "red" if role == "blue" else "blue"
    units = [make_unit(faction=role), make_unit("seen", enemy, hex="hex-2-1", strength=60),
             make_unit("hidden", enemy, hex=None), make_unit("dead", enemy, hex="hex-3-2", ineffective=True)]
    _, board, data = unit_world(units)
    trail = obsmod.FadingTrailFeature(role, board, .25)
    result = trail.update(data)
    expected = np.zeros((3, 4)); expected[1, 2] = .6
    np.testing.assert_array_equal(result, expected)
    assert obsmod.fractionHiddenOpforFeature(role, data, board) == (1, 2)
    data.unitIndex[f"{enemy} seen"].hex = None
    assert trail.update(data) is result
    np.testing.assert_allclose(result, expected * .75)
    trail.update(data)
    np.testing.assert_allclose(result, expected * .75**2)
    result[0, 0] = 8
    assert trail.update(data)[0, 0] == 6  # intentionally exposed mutable matrix
    _, _, empty = unit_world([])
    assert obsmod.fractionHiddenOpforFeature(role, empty, board) == (0, 0)


def test_distribution_diffusion_normalization_and_repeated_update(obsmod, unit_world, make_unit):
    _, board, data = unit_world([make_unit(faction="red", hex="hex-1-1")])
    dist = obsmod.OpforDistrib(.01, board, data, "blue")
    assert dist.sum == 1
    assert dist.distr["hex-1-1"] == 1
    dist.update(data, data)
    # Interior infantry has six destinations on this clear board.
    expected = {key: 0. for key in board.hexIndex}
    expected["hex-1-1"] = .94
    for key in ["hex-1-0", "hex-2-1", "hex-2-2", "hex-1-2", "hex-0-2", "hex-0-1"]:
        expected[key] = .01
    assert dist.distr == pytest.approx(expected)
    assert dist.getNormalizedDist() is dist.distr
    for _ in range(3):
        dist.update(data, data)
        values = dist.getNormalizedDist()
        assert set(values) == set(board.hexIndex)
        assert sum(values.values()) == pytest.approx(1)
        assert all(np.isfinite(v) and v >= 0 for v in values.values())


def test_distribution_fully_culled(obsmod, unit_world, make_unit):
    _, board, data = unit_world([make_unit(), make_unit(faction="red", hex="hex-0-1")])
    dist = obsmod.OpforDistrib(.01, board, data, "blue")
    assert dist.sum == 0
    assert set(dist.getNormalizedDist().values()) == {0}
    dist.update(data, data)
    assert set(dist.getNormalizedDist().values()) == {0}


def test_distribution_normalizes_multiple_enemies_and_culls_visible_mass(obsmod, unit_world, make_unit):
    _, board, data = unit_world([make_unit("A", "red", hex="hex-0-0"), make_unit("B", "red", hex="hex-3-2")])
    dist = obsmod.OpforDistrib(.01, board, data, "blue")
    result = dist.getNormalizedDist()
    assert dist.sum == 1
    assert result["hex-0-0"] == result["hex-3-2"] == .5
    assert sum(result.values()) == 1
    _, _, friendlies = unit_world([make_unit(hex="hex-0-1")])
    dist.cull(friendlies)
    assert dist.distr["hex-0-0"] == 0
    assert dist.sum == .5
    assert dist.getNormalizedDist()["hex-3-2"] == 1
    _, board, empty = unit_world([])
    # Empty input never dereferences the absent prototype.
    dist = obsmod.OpforDistrib(.01, board, empty, "blue")
    dist.update(empty, empty)
    assert set(dist.getNormalizedDist().values()) == {0}


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K39: friendly-only distribution has no prototype")
def test_distribution_friendly_only(obsmod, unit_world, make_unit):
    _, board, data = unit_world([make_unit()])
    try:
        dist = obsmod.OpforDistrib(.01, board, data, "blue")
    except AttributeError as exc:
        if str(exc) == "'OpforDistrib' object has no attribute 'opforUnitProto'":
            raise KnownDefect("K39: missing enemy prototype") from exc
        raise
    assert not any(dist.getNormalizedDist().values())


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K40: newly hidden enemy divides by zero")
def test_newly_hidden_without_prior_hidden(obsmod, unit_world, make_unit):
    _, board, prior = unit_world([make_unit(faction="red", hex="hex-2-1")])
    _, _, current = unit_world([make_unit(faction="red", hex=None)])
    dist = obsmod.OpforDistrib(.01, board, prior, "blue")
    try:
        dist.update(current, prior)
    except ZeroDivisionError as exc:
        if str(exc) == "division by zero" and dist.sum == 1:
            raise KnownDefect("K40: zero prior hidden count") from exc
        raise
    assert all(np.isfinite(v) for v in dist.getNormalizedDist().values())


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K41: new track uses Hex object as dictionary key")
def test_newly_hidden_keys_are_hex_ids(obsmod, unit_world, make_unit):
    visible = [make_unit("A", "red", hex="hex-2-1"), make_unit("B", "red", hex="hex-3-2")]
    _, board, data = unit_world(visible)
    dist = obsmod.OpforDistrib(.01, board, data, "blue")
    data.unitIndex["red B"].hex = None
    _, _, current = unit_world([make_unit("A", "red", hex=None), make_unit("B", "red", hex=None)])
    dist.add(current, data)
    wrong_key = data.unitIndex["red A"].hex
    if wrong_key in dist.distr and dist.distr[wrong_key] == 2 and dist.sum == 4:
        with pytest.raises(KeyError) as failure:
            dist.move(current)
        assert failure.value.args == (wrong_key,)
        raise KnownDefect("K41: exact Hex key and failed diffusion lookup")
    assert set(dist.distr) == set(board.hexIndex)


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K42: initially hidden enemy dereferences None")
def test_initially_hidden_distribution(obsmod, unit_world, make_unit):
    _, board, data = unit_world([make_unit(faction="red", hex=None)])
    try:
        dist = obsmod.OpforDistrib(.01, board, data, "blue")
    except AttributeError as exc:
        if str(exc) == "'NoneType' object has no attribute 'id'":
            raise KnownDefect("K42: hidden enemy has no hex") from exc
        raise
    assert all(np.isfinite(v) for v in dist.getNormalizedDist().values())
