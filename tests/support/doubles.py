"""Finite boundary doubles; these do not implement or replace engine rules."""

from copy import deepcopy
import json


class RecordingClient:
    def __init__(self, replies=()):
        self.received = []
        self.replies = iter(deepcopy(replies))
        self.response_fn = None

    def __call__(self, message, response_fn=None):
        self.received.append(json.loads(message))
        self.response_fn = response_fn
        reply = next(self.replies, None)
        return None if reply is None else json.dumps(reply)


class FiniteAsyncIterator:
    def __init__(self, values):
        self.values = iter(values)

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.values)
        except StopIteration:
            raise StopAsyncIteration from None


class WebSocketDouble(FiniteAsyncIterator):
    """Incoming and sent values are wire strings, as in websockets."""
    def __init__(self, incoming=()):
        super().__init__(incoming)
        self.sent = []
        self.closed = False

    async def send(self, message):
        if self.closed:
            raise RuntimeError("WebSocket double is closed")
        self.sent.append(message)

    async def close(self):
        self.closed = True


class FiniteDispenser:
    def __init__(self, games):
        self.games = iter(games)

    def get_next_game(self):
        return next(self.games)


class FiniteGame:
    """Two-ply tree: blue chooses left/right, red chooses low/high.

    Leaf scores: left=(3,5), right=(-2,7). Minimax choice left, value 3.
    States are tuples of action names; parameter/observation values are fresh.
    """
    def __init__(self):
        self.leaves = {("left", "low"): 3, ("left", "high"): 5,
                       ("right", "low"): -2, ("right", "high"): 7}

    def players(self):
        return ["blue", "red"]

    def initial_state(self):
        return ()

    def max_player(self):
        return "blue"

    def on_move(self, state):
        return "blue" if len(state) % 2 == 0 else "red"

    def is_terminal(self, state):
        return state in self.leaves

    def score(self, state):
        return self.leaves.get(state, 0)

    def legal_actions(self, state):
        if self.is_terminal(state):
            return []
        return ["left", "right"] if not state else ["low", "high"]

    def transition(self, state, action):
        if action not in self.legal_actions(state):
            raise ValueError("Illegal finite-tree action")
        return (*state, action)

    def parameters(self):
        return {"name": "finite-tree"}

    def observation(self, state, player):
        return {"path": list(state), "role": player}


class ControlledPrediction:
    """Stable-Baselines predict signature: (action, recurrent state)."""
    def __init__(self, actions):
        self.actions = iter(actions)
        self.calls = []

    def predict(self, observation, state=None, episode_start=None, deterministic=False):
        self.calls.append(deepcopy((observation, state, episode_start, deterministic)))
        return deepcopy(next(self.actions)), state
