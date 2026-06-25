import os
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))
os.chdir(SERVER_DIR)

import gymnasium as gym

from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.policies import ActorCriticPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.utils import get_schedule_fn
from stable_baselines3.common.preprocessing import is_image_space

import gym_interface
import random

import numpy
import torch

print(f"Running from server directory: {SERVER_DIR}")

# Comment out to use an automatically selected seed
# Uncomment for reproducible runs
seed = 12345
random.seed(seed)
numpy.random.seed(seed)
torch.manual_seed(seed)

env = gym_interface.GymEnvironment(role="blue", versusAI="passive", scenario="2v1-5x5.scn", saveReplay=False, actions19=False, ai="gym", verbose=False)

model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=4000, log_interval=100)

model.save("ppo_save")

print(f'eval results: {evaluate_policy(model, model.get_env(), n_eval_episodes=10)}')

N = 10
obs, info = env.reset()
#print('initial obs')
#print(obs)
for episode in range(N):
    obs, info = env.reset()
    done = False
    pos_reward_counter = 0
    total_reward = 0
    max_reward = float('-inf')
    step_counter = 0
    while not done:
        step_counter += 1
        action, _states = model.predict(obs)
        obs, rewards, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        #print(f'action {action} reward {rewards} done {done} obs')
        #print(obs)
        total_reward += rewards
        if rewards > max_reward:
            max_reward = rewards
        if rewards > 0:
            pos_reward_counter += 1
    print(f"Episode {episode + 1}: Total reward: {total_reward}  Max reward: {max_reward} Pos rewards: {pos_reward_counter} Steps: {step_counter}")
 
