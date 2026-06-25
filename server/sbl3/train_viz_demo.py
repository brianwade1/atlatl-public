
import os
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))
os.chdir(SERVER_DIR)

from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.policies import ActorCriticCnnPolicy
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor, NatureCNN
from stable_baselines3.common.utils import get_schedule_fn
from stable_baselines3.common.callbacks import EvalCallback

import gymnasium as gym
import torch as th
from torch import nn as nn
import gym_interface

import numpy as np
import random

import hexagdly

from collections import OrderedDict

class HexBlock(nn.Module):
    def __init__(self, in_channels, out_channels, residual=True):
        super().__init__()
        self.in_channels, self.out_channels = in_channels, out_channels
        self.hexConv2d = hexagdly.Conv2d(in_channels, out_channels, kernel_size=1, stride=1)
        self.norm = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()
        self.residual = residual

    def forward(self, x):
        residual = x
        x = self.hexConv2d(x)
        x = self.norm(x)
        if self.residual:
            x += residual
        x = self.relu(x)
        return x

class MyCNN(BaseFeaturesExtractor):
    """
    Replacement for NatureCNN (network from Atari Nature paper)

    :param observation_space: (gym.Space)
    :param features_dim: (int) Number of features extracted.
        This corresponds to the number of unit for the last layer.
    """

    def __init__(self, observation_space: gym.spaces.Box, features_dim: int = 512):
        super(MyCNN, self).__init__(observation_space, features_dim)
        # We assume CxHxW images (channels first)
        n_input_channels = observation_space.shape[0]
        n_residual_layers = 7
        convs_per_layer = 64
        self.layers = OrderedDict()
        self.layers.update( {'conv': HexBlock(n_input_channels, convs_per_layer, residual=False)} )
        for i in range(n_residual_layers):
            layer_name = "resid"+str(i+1)
            self.layers.update( {layer_name: HexBlock(convs_per_layer, convs_per_layer)} ) 
        self.layers.update( {'flatten': nn.Flatten()})
        self.cnn = nn.Sequential(self.layers)
        print( "----------------")
        print(f"Model print demo")
        print( "----------------")
        print(self.cnn)
        model = self.cnn
        pytorch_total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(f"----------------------------------")
        print(f"Parameter count {pytorch_total_params}")
        print(f"----------------------------------")
        self.print_toggle = True

        # Compute shape by doing one forward pass
        with th.no_grad():
            n_flatten = self.cnn(th.as_tensor(observation_space.sample()[None]).float()).shape[1]

        self.linear = nn.Sequential(nn.Linear(n_flatten, features_dim), nn.ReLU())

    def forward(self, observations: th.Tensor) -> th.Tensor:
        # if self.print_toggle:
        #     print(observations)
        #     self.print_toggle = False
        #return self.linear(self.cnn(observations))
        x = observations
        if self.print_toggle:
            print("-----------------------------------------")
            print("Demo of accessing activations and weights")
            print("-----------------------------------------")
            print(f"obs {observations.shape}")
        for layer_key in self.layers:
            layer = self.layers[layer_key]
            x = layer(x)
            if self.print_toggle:
                print(f"layer {layer_key} output {x.shape}")
                if layer_key != "flatten":
                    kernels = layer.hexConv2d.kernel0.cpu().detach().clone()
                    print(f"kernel 0 weight shape {kernels.shape}")
                    kernels = layer.hexConv2d.kernel1.cpu().detach().clone()
                    print(f"kernel 1 weight shape {kernels.shape}")
        x = self.linear(x)
        if self.print_toggle:
            print(f"linear {x.shape}")
            self.print_toggle = False
        return x

# Comment out to use an automatically selected seed
# Uncomment for reproducible runs
# seed = 12345
# random.seed(seed)
# np.random.seed(seed)
# th.manual_seed(seed)

# This is an example of how to connect to the standard Gym environments
# env = gym.make('CartPole-v1')

env = gym_interface.GymEnvironment(role="blue", versusAI="shootback", scenario="column-6x6-2v1.scn", saveReplay=False, actions19=False, ai="gym12", verbose=False)

policy_kwargs = { "features_extractor_class" : MyCNN }
policy = ActorCriticCnnPolicy
model = PPO(policy, env, clip_range=0.1, policy_kwargs=policy_kwargs, verbose=1)
# Evaluation is apparently done deterministically (max probability action only)
#model.learn(total_timesteps=4000000, log_interval=1000, eval_env=env, eval_freq=50000, n_eval_episodes=1000, eval_log_path="cjds_logs") 
eval_callback = EvalCallback(env, log_path="cjds_logs", eval_freq=50000, n_eval_episodes=1000, deterministic=True, render=False)
model.learn(total_timesteps=400, log_interval=1000, callback=eval_callback)

model.save("ppo_save")

print(f'eval results: {evaluate_policy(model, model.get_env(), n_eval_episodes=10)}')

N = 100
pos_reward_counter = 0
total_reward = 0
max_reward = float('-inf')
obs, info = env.reset()
#print('initial obs')
#print(obs)
# for i in range(N):
#     action, _states = model.predict(obs)
#     obs, rewards, dones, info = env.step(action)
#     print(f'action {action} reward {rewards} done {dones} obs')
#     print(obs)
#     total_reward += rewards
#     if rewards > max_reward:
#         max_reward = rewards
#     if rewards > 0:
#         pos_reward_counter += 1
#     if dones:
#         env.reset()
# print(f"Average reward per action: {total_reward/N}  Max reward: {max_reward} Pos rewards: {pos_reward_counter}")
 
