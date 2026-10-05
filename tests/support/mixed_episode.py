"""S18-F hand-scripted episode; no engine imports or production rule tables."""

from copy import deepcopy

from tests.support.builders import make_map, make_scenario, make_unit


def episode():
    board = make_map(rows=7, cols=4, terrain_overrides={(1, 0): "urban"})
    board["fogOfWar"] = True
    scenario = make_scenario(board, [
        make_unit("shooter", hex="hex-0-0"),
        make_unit("capturer", strength=60, hex="hex-1-1"),
        make_unit("scout", hex="hex-0-3"),
        make_unit("defender", "red", strength=60, hex="hex-1-0", can_move=False),
        make_unit("shooter", "red", hex="hex-2-0", can_move=False),
        make_unit("capturer", "red", hex="hex-2-1", can_move=False),
        make_unit("hidden", "red", hex="hex-0-6", can_move=False),
    ], max_phases=4, city_score=12)
    actions = [
        {"type": "fire", "source": "blue shooter", "target": "red defender"},
        {"type": "move", "mover": "blue capturer", "destination": "hex-1-0"},
        {"type": "move", "mover": "blue scout", "destination": "hex-0-4"},
        {"type": "fire", "source": "red shooter", "target": "blue capturer"},
        {"type": "move", "mover": "red capturer", "destination": "hex-1-0"},
        {"type": "pass"},
        {"type": "move", "mover": "blue scout", "destination": "hex-0-3"},
        {"type": "pass"}, {"type": "pass"},
    ]
    # Literal intermediate changes and independently calculated phase/score table.
    # Urban infantry damage is 25; each 60-strength victim is removed at 35.
    # Red loss credits +60; blue loss costs -120. City phases add +12 or -12.
    changes = [None, (3, {"currentStrength": 35, "hex": None, "ineffective": True}),
        (1, {"hex": "hex-1-0"}), (2, {"hex": "hex-0-4"}),
        (1, {"currentStrength": 35, "hex": None, "ineffective": True}),
        (5, {"hex": "hex-1-0"}), None, (2, {"hex": "hex-0-3"}), None, None]
    availability = [
        [1,1,1,0,0,0,0], [0,1,1,0,0,0,0], [0,0,1,0,0,0,0],
        [0,0,0,0,1,1,1], [0,0,0,0,0,1,1], [0,0,0,0,0,0,1],
        [1,0,1,0,0,0,0], [1,0,0,0,0,0,0], [0,0,0,0,1,1,1],
        [0,0,0,0,1,1,1],  # Terminal advance does not refresh availability.
    ]
    phases = [0,0,0,1,1,1,2,2,3,4]
    scores = [0,60,60,72,-48,-48,-60,-60,-72,-84]
    owners = ["red","red","red","blue","blue","blue","red","red","red","red"]
    units = deepcopy(scenario["units"])
    states = []
    for index in range(10):
        if changes[index]:
            position, values = changes[index]
            units[position].update(values)
        for unit, movable in zip(units, availability[index], strict=True):
            unit["canMove"] = bool(movable)
            unit["detected"] = any(
                not unit["ineffective"] and not other["ineffective"]
                and unit["faction"] != other["faction"]
                and cube_distance(unit["hex"], other["hex"]) <= 2
                for other in units)
        states.append({"units": deepcopy(units), "status": {
            "cityOwner": {"hex-1-0": owners[index]}, "score": scores[index],
            "phaseCount": phases[index], "isTerminal": index == 9,
            "onMove": "blue" if phases[index] % 2 == 0 else "red", "setupMode": False}})
    transcripts = {}
    for role in ("blue", "red"):
        records = [{"type": "parameters", "parameters": deepcopy(scenario)}]
        for state in states:
            observation = deepcopy(state)
            for unit in observation["units"]:
                if unit["faction"] != role and not unit["detected"]:
                    unit["hex"] = "fog"
            records.append({"type": "observation", "observation": observation})
        transcripts[role] = records
    return scenario, actions, states, transcripts


def cube_distance(first, second):
    """Independent odd-q offset-to-cube distance, without engine grid centers."""
    def cube(hex_id):
        _, q, row = hex_id.split("-")
        q, row = int(q), int(row)
        z = row - (q - q % 2) // 2
        return q, -q-z, z
    return max(abs(a-b) for a, b in zip(cube(first), cube(second), strict=True))
