"""Independent numeric oracles for every S03 rule-table entry."""

import math

import pytest

from tests.support.imports import import_server

pytestmark = [pytest.mark.core, pytest.mark.unit]

TYPES = ("infantry", "mechinf", "armor", "artillery")
TERRAINS = ("clear", "water", "rough", "unused", "marsh", "urban")
MOVEMENT = (
    (100, math.inf, 100, math.inf, 100, 100),
    (50, math.inf, 100, math.inf, 100, 100),
    (50, math.inf, 100, math.inf, 100, 100),
    (50, math.inf, 100, math.inf, math.inf, 100),
)
TERRAIN_MULTIPLIERS = (
    (1, 1, .5, 1, 1, .5),
    (1, 1, 1, 1, 2, 1),
    (1, 1, 1, 1, 2, 1),
    (1, 1, 1, 1, 2, 1),
)
FIREPOWER = ((1, 1, .5, 1.5), (.75, 1, .75, 1.5),
             (.5, .75, 1, 1), (1, .75, .5, 1.5))


@pytest.mark.parametrize("unit_index", range(4), ids=TYPES)
@pytest.mark.parametrize("terrain_index", range(6), ids=TERRAINS)
def test_mobility_and_terrain_coefficients(engine_imports, unit_index, terrain_index):
    unit_type, terrain = TYPES[unit_index], TERRAINS[terrain_index]
    mobility, combat = import_server("mobility"), import_server("combat")
    assert mobility.cost[unit_type][terrain] == MOVEMENT[unit_index][terrain_index]
    assert combat.terrain_multiplier[unit_type][terrain] == TERRAIN_MULTIPLIERS[unit_index][terrain_index]


@pytest.mark.parametrize("attacker", range(4), ids=TYPES)
@pytest.mark.parametrize("target", range(4), ids=TYPES)
def test_firepower_coefficients(engine_imports, attacker, target):
    combat = import_server("combat")
    assert combat.firepower[TYPES[attacker]][TYPES[target]] == FIREPOWER[attacker][target]
    assert combat.defensivefp[TYPES[attacker]][TYPES[target]] == 0


def test_scalar_rules_and_table_domains(engine_imports):
    combat, mobility = import_server("combat"), import_server("mobility")
    assert combat.range == dict(zip(TYPES, (1, 1, 1, 2)))
    assert combat.sight == dict.fromkeys(TYPES, 2)
    assert combat.pDetect == 1.0
    assert combat.ineffectiveThreshold == .50
    assert combat.firepower_scaling == .5
    assert mobility.stackingLimit == 1
    for table in (mobility.cost, combat.terrain_multiplier, combat.firepower, combat.defensivefp):
        assert set(table) == set(TYPES)
        domain = TERRAINS if table is mobility.cost or table is combat.terrain_multiplier else TYPES
        assert all(set(row) == set(domain) for row in table.values())


def test_characterization_shared_table_rows(engine_imports):
    combat, mobility = import_server("combat"), import_server("mobility")
    assert mobility.cost["mechinf"] is mobility.cost["armor"]
    assert mobility.cost["artillery"] is not mobility.cost["armor"]
    assert combat.terrain_multiplier["mechinf"] is combat.terrain_multiplier["armor"]
    assert combat.terrain_multiplier["artillery"] is combat.terrain_multiplier["armor"]
