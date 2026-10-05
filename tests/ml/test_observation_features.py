"""Literal channel oracles on an asymmetric 4-column, 3-row board."""

from copy import deepcopy
from types import SimpleNamespace
import numpy as np
import pytest
from tests.support.isolation import KnownDefect

pytestmark = [pytest.mark.ml, pytest.mark.unit]


def expected_channels(game, state):
    # Independent portable-data oracle: no production feature calls.
    result = np.zeros((17, 3, 4))
    for u in state["units"]:
        if u["hex"] in (None, "fog"):
            continue
        x, y = map(int, u["hex"].split("-")[1:])
        result[0, y, x] = float(u["canMove"] and not u["ineffective"])
        result[1 if u["faction"] == "blue" else 2, y, x] = 0 if u["ineffective"] else u["currentStrength"] / 100
        result[3 + ["infantry", "mechinf", "armor", "artillery"].index(u["type"]), y, x] = 1
    for h in game.mapData.hexes():
        result[7 + ["clear", "water", "rough", "urban", "marsh", "unused"].index(h.terrain), h.y_offset, h.x_offset] = 1
    for key, faction in state["status"]["cityOwner"].items():
        x, y = map(int, key.split("-")[1:])
        result[13 if faction == "blue" else 14, y, x] = 1
    result[15] = 1 - .9 ** state["status"]["phaseCount"]
    result[16] = state["status"]["score"] / 1000
    return result


@pytest.mark.parametrize("faction", ["blue", "red"])
@pytest.mark.parametrize("ineffective,movable", [(False, True), (False, False), (True, True)])
def test_unit_features(obsmod, faction, ineffective, movable):
    u = SimpleNamespace(faction=faction, ineffective=ineffective, canMove=movable, currentStrength=37, type="armor")
    for side, fn in [("blue", obsmod.blueUnitFeature), ("red", obsmod.redUnitFeature)]:
        assert fn(u) == (.37 if faction == side and not ineffective else 0)
        assert obsmod.strengthUnitFeature(u, side) == fn(u)
    assert obsmod.canMoveFeature(u) == float(movable and not ineffective)
    for kind in ["infantry", "mechinf", "armor", "artillery"]:
        assert obsmod.unitTypeFeatureFactory(kind)(u) == float(kind == "armor")


def test_hex_factories(obsmod):
    for terrain in ["clear", "water", "rough", "urban", "marsh", "unused"]:
        for actual in ["clear", "water", "rough", "urban", "marsh", "unused"]:
            assert obsmod.terrainFeatureFactory(terrain)(SimpleNamespace(terrain=actual)) == float(terrain == actual)
    assert obsmod.constantFeatureFactory(-.25)(None) == -.25
    for faction in ["blue", "red"]:
        fn = obsmod.cityOwnerFeatureFactory(faction)
        assert fn("hex-1-2", {"hex-1-2": faction}) == 1
        assert fn("missing", {}) == 0
        assert fn("hex-1-2", {"hex-1-2": "neutral"}) == 0


@pytest.mark.parametrize("terrain,channel", [("clear",7),("water",8),("rough",9),("urban",10),("marsh",11),("unused",12)])
def test_all_terrain_channels_on_asymmetric_cell(obsmod, rectangular_game, terrain, channel):
    game, state = rectangular_game
    game.mapData.hexIndex["hex-1-2"].terrain = terrain
    actual = obsmod.observation_np(game,state)
    np.testing.assert_array_equal(actual, expected_channels(game,state))
    assert actual[channel,2,1] == 1
    assert actual[7:13,2,1].sum() == 1


@pytest.mark.parametrize("flip", [False, True])
def test_numpy_layout_append_and_input_preservation(obsmod, rectangular_game, flip):
    game, state = rectangular_game
    state["status"]["cityOwner"] = {"hex-1-1": "blue", "hex-2-0": "red"}
    original = deepcopy(state)
    expected = expected_channels(game, state)
    if flip:
        expected[[1, 2]] = expected[[2, 1]]
        expected[[13, 14]] = expected[[14, 13]]
        expected[16] *= -1
    extra = np.arange(12).reshape(3, 4)
    actual = obsmod.observation_np(game, state, flip, [extra])
    assert actual.shape == (18, 3, 4)
    np.testing.assert_allclose(actual[:17], expected)
    np.testing.assert_array_equal(actual[17], extra)
    assert state == original
    with pytest.raises(ValueError, match="same shape"):
        obsmod.observation_np(game, state, appendFeatures=[np.zeros((4, 3))])


@pytest.mark.parametrize("kind", ["infantry", "mechinf", "armor", "artillery"])
def test_missing_and_ineffective_units(obsmod, rectangular_game, kind):
    game, state = rectangular_game
    state["units"][0].update(type=kind, ineffective=True)
    state["units"][1]["hex"] = None
    np.testing.assert_array_equal(obsmod.observation_np(game, state), expected_channels(game, state))
    state["units"] = []
    assert not obsmod.observation_np(game, state)[:7].any()


def test_torch_dtype_and_append(obsmod, rectangular_game):
    import torch
    game, state = rectangular_game
    extra = np.full((3, 4), .42)
    actual = obsmod.observation(game, state, appendFeatures=[extra])
    assert actual.dtype == torch.float32
    np.testing.assert_allclose(actual.numpy(), np.concatenate([expected_channels(game, state), extra[None]]))


@pytest.mark.xfail(strict=True, raises=KnownDefect, reason="K38: Torch wrapper ignores flipFactions")
def test_torch_forwards_flip(obsmod, rectangular_game):
    game, state = rectangular_game
    state["status"]["cityOwner"] = {"hex-1-1":"blue", "hex-2-0":"red"}
    actual = obsmod.observation(game, state, flipFactions=True).numpy()
    wrong = expected_channels(game, state).astype(np.float32)
    if np.array_equal(actual, wrong):
        raise KnownDefect("K38: exact unflipped tensor")
    np.testing.assert_allclose(actual, obsmod.observation_np(game, state, True), rtol=1e-6)


@pytest.mark.parametrize("action,actor,target", [
    ({"type": "pass"}, None, None),
    ({"type": "move", "mover": "blue A", "destination": "hex-2-1"}, (2, 0), (1, 2)),
    ({"type": "fire", "source": "blue A", "target": "red A"}, (2, 0), (0, 3)),
    ({"type": "fire", "source": "missing", "target": "missing"}, None, None),
])
def test_action_masks(obsmod, rectangular_game, action, actor, target):
    game, state = rectangular_game
    for actual, coordinate in zip(obsmod.action_maps(action, game, state), [actor, target]):
        expected = np.zeros((3, 4))
        if coordinate is not None:
            expected[coordinate] = 1
        np.testing.assert_array_equal(actual, expected)
    assert not obsmod.zero_map(game, state).any()
    assert obsmod.actor_map("blue A", game, state)[2, 0] == 1
    assert not obsmod.actor_map("unknown", game, state).any()
    state["units"][0]["hex"] = None
    assert not obsmod.actor_map("blue A", game, state).any()
