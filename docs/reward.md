# Reward Design in Atlatl

This document explains how the reinforcement learning reward signal is computed in Atlatl and how to modify it.

## Overview

The reward pipeline has two layers:

1. **Game score** — a running integer maintained by the simulation engine that reflects kills and city control.
2. **Reward engineering** (`rewArt`) — a per-step transform applied to the change in game score before it is returned to the RL agent.

---

## Layer 1: Game Score

The simulation tracks a single `score` value from **blue's perspective**. It changes on three types of events.

| Event | Delta |
|---|---|
| Red unit loses `N` strength points | `+N` |
| Blue unit loses `N` strength points | `+N × lossPenalty` (default `−1`) |
| End of each phase, per city held by blue | `+cityScore / num_cities` (default `+24 / num_cities`) |
| End of each phase, per city held by red | `−cityScore / num_cities` |

These parameters are set in the scenario definition. In `server/scenario.py` the default is:

```python
score = {"maxPhases": max_phases, "lossPenalty": -1, "cityScore": 24}
```

The score is computed inside `server/status.py`:

- `dscoreKill()` — called on every combat exchange; adds or subtracts based on which faction was hit.
- `endPhaseDeltaCityScore()` — called at end of each phase; tallies city ownership.
- `advancePhase()` — calls `endPhaseDeltaCityScore()` and adds the result to `self.score`.

### Example: Score After One Step

Suppose the scenario has one city and uses default parameters (`lossPenalty = -1`, `cityScore = 24`). At the start of a phase the score is `0`.

Blue fires on a red infantry unit standing in clear terrain:

```text
damage = 100 × 1.00 × 1.00 × 0.5 = 50
```

Red drops from 100 to 50 strength — exactly at the ineffective threshold, so the unit is removed and all 50 remaining points count as killed.

```text
score += 50     →  score = 50
```

Red then fires back on a blue infantry unit also in clear terrain:

```text
damage = 100 × 1.00 × 1.00 × 0.5 = 50
```

Blue drops from 100 to 50 and is also removed.

```text
score += 50 × (−1)   →  score = 0
```

The phase ends. Blue holds the one city.

```text
score += 24 / 1 = 24   →  score = 24
```

The score returned to the RL agent at the end of this step is `24 − 0 = 24` (assuming `last_score` was `0`).

---

## Layer 2: Reward Engineering (`rewArt`)

At each game step the AI script receives an observation that includes the current `score`. The raw reward for that step is simply the score delta:

```python
raw_reward = obs['status']['score'] - self.last_score
```

This raw delta is then passed through the active `rewArt` object. The default class is `BoronRewArt`.

### Default: `BoronRewArt`

Defined in `server/ai/multigym_ai.py` and `server/ai/gym_ai_surrogate.py`.

```python
class BoronRewArt:
    def __init__(self, own_faction, terminal_bonus=25):
        ...
    def engineeredReward(self, raw_reward, unitData, is_terminal=False):
        current_strength = self._totalFriendlyStrength(self.own_faction, unitData)
        if raw_reward < 0:
            raw_reward = 0
        if is_terminal:
            raw_reward += self.terminal_bonus
        return raw_reward * current_strength / self.original_strength
```

Three adjustments are made to the raw score delta:

1. **Negative rewards are zeroed.** A raw delta below zero (e.g., blue takes casualties before it can fire back) is replaced with `0`. Without this, the agent often learns to avoid combat entirely.

2. **Terminal bonus.** When the episode ends (`is_terminal=True`), a fixed bonus (`terminal_bonus=25` by default) is added to the raw reward. This discourages the agent from taking reckless attacks on the final move just to gain score.

3. **Strength scaling.** The adjusted reward is multiplied by `current_strength / original_strength`, where both values count only the agent's own surviving, effective units. A faction that has lost half its force earns half as much reward for the same score gain. This provides a soft incentive to preserve forces.

The `accumulated_reward` is summed across all intermediate game steps (opponent moves, animations, etc.) and flushed as a single value when `action_result()` is called.

### Alternative: `NoNegativesRewArt`

Also present in the same files but not used by default.

```python
class NoNegativesRewArt:
    def engineeredReward(self, reward, unitData=None, is_terminal=False):
        if reward < 0:
            self.negative_rewards += 1
            return 0
        reward_discount = 10 / (10 + self.negative_rewards)
        return reward * reward_discount
```

Instead of scaling by strength, it tracks a count of negative-reward events over the episode and discounts all future positive rewards accordingly. An agent that took several bad exchanges early in the game earns diminishing returns on later successes.

---

## How to Modify the Reward

### Change the scenario-level score parameters

Open `server/scenario.py` and edit the `score` dict in the factory function for your scenario:

```python
score = {"maxPhases": max_phases, "lossPenalty": -1, "cityScore": 24}
```

| Parameter | Effect |
|---|---|
| `maxPhases` | Maximum number of phases before the episode terminates. |
| `lossPenalty` | Score change per blue strength point lost (negative = penalty). |
| `cityScore` | Total points awarded per phase across all cities; split evenly per city. |

### Adjust `BoronRewArt` parameters

The `terminal_bonus` can be changed at construction time. In `gym_ai_surrogate.py` or `multigym_ai.py`, find where the class is instantiated (in `reset()`) and pass a different value:

```python
# Current default
self.rewArt = self.rewart_class(self.role)  # terminal_bonus defaults to 25

# Disable the terminal bonus
self.rewArt = BoronRewArt(self.role, terminal_bonus=0)

# Increase the terminal bonus
self.rewArt = BoronRewArt(self.role, terminal_bonus=50)
```

Setting `terminal_bonus=0` reproduces the original "Boron" behavior (documented in the class comment).

### Switch to `NoNegativesRewArt`

In `gym_ai_surrogate.py` (for single-agent training) or `multigym_ai.py` (for multi-agent), change the `rewart_class` assignment in `__init__`:

```python
# Default
self.rewart_class = BoronRewArt

# Switch to alternative
self.rewart_class = NoNegativesRewArt
```

### Use raw score deltas (no engineering)

Replace `engineeredReward` with a pass-through in whichever class you are using:

```python
def engineeredReward(self, reward, unitData=None, is_terminal=False):
    return reward
```

This lets negative rewards flow through unchanged and removes the strength-scaling multiplier. Useful as a baseline to compare against engineered variants.

### Write a custom `rewArt` class

Any object with an `engineeredReward(raw_reward, unitData, is_terminal)` signature can be used. For example:

```python
class MyRewArt:
    def __init__(self, own_faction):
        self.own_faction = own_faction

    def engineeredReward(self, raw_reward, unitData, is_terminal=False):
        # your logic here
        return raw_reward
```

Then assign it:

```python
self.rewart_class = MyRewArt
```

`unitData` is an instance of `unit.UnitData`; you can iterate over all units with `unitData.units()` and inspect `.faction`, `.currentStrength`, and `.ineffective`.

---

## Key Files

| File | Role |
|---|---|
| `server/status.py` | Maintains game score; `dscoreKill()` and `advancePhase()` update it. |
| `server/scenario.py` | Sets `maxPhases`, `lossPenalty`, and `cityScore` per scenario. |
| `server/ai/gym_ai_surrogate.py` | `BoronRewArt`, `NoNegativesRewArt`, and single-agent gym AI. |
| `server/ai/multigym_ai.py` | Same reward classes duplicated for the multi-agent gym AI. |
| `server/gym_interface.py` | Gymnasium `Env` wrapper; calls `action_result()` to get the reward. |
| `server/multigym.py` | Multi-agent Gymnasium wrapper. |
