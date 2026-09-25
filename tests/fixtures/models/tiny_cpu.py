"""Parameter-bearing CPU model with an independently specified y = 2x + 1."""

import torch


class TinyCPU(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.scale = torch.nn.Parameter(torch.tensor(2.0))
        self.bias = torch.nn.Parameter(torch.tensor(1.0))

    def forward(self, value):
        return self.scale * value + self.bias
