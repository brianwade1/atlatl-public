import gym

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

print("This file needs to be in the server directory to run.")

# Comment out to use an automatically selected seed
# Uncomment for reproducible runs
seed = 12345
random.seed(seed)
numpy.random.seed(seed)
torch.manual_seed(seed)

env = gym_interface.GymEnvironment(role="blue", versusAI="passive", scenario="atomic-city.scn", saveReplay=False, actions19=False, ai="gym", verbose=False)

model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=400, log_interval=100)

model.save("ppo_save")

print(f'eval results: {evaluate_policy(model, model.get_env(), n_eval_episodes=10)}')

N = 100
pos_reward_counter = 0
total_reward = 0
max_reward = float('-inf')
obs = env.reset()
#print('initial obs')
#print(obs)
for i in range(N):
    action, _states = model.predict(obs)
    obs, rewards, dones, info = env.step(action)
    print(f'action {action} reward {rewards} done {dones} obs')
    print(obs)
    total_reward += rewards
    if rewards > max_reward:
        max_reward = rewards
    if rewards > 0:
        pos_reward_counter += 1
    if dones:
        env.reset()
print(f"Average reward per action: {total_reward/N}  Max reward: {max_reward} Pos rewards: {pos_reward_counter}")
 
