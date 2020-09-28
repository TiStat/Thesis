import numpy as np
import torch.nn as nn
from Pytorch.Layer.Group_HorseShoe import Group_HorseShoe
from Pytorch.Grid.Grid_Layout import GRID_Layout
from Pytorch.Grid.Suits.Suit_Samplers import samplers

# (CONFIG) ---------------------------------------------------------------------
steps = 1000
n = 1000
n_val = 100
batch = 100

# (SAMPLER CHECK UP) -----------------------------------------------------------
cls = Group_HorseShoe
cls_Grid = GRID_Layout

model_param = dict(no_in=2, no_out=1, bias=True, activation=nn.ReLU(), bijected=True)

samplers(cls, cls_Grid, n, n_val, model_param, steps, batch,
         epsilons=np.arange(0.0001, 0.02, 0.002),
         Ls=[1, 2, 3], repeated=30)
