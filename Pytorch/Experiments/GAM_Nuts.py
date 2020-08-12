import torch
import torch.nn as nn
import torch.distributions as td
import os

from Pytorch.Util.GridUtil import Grid


class GAM_Nuts(Grid):
    def main(self, n, steps, bijected=True, model_param={}):

        from Tensorflow.Effects.bspline import get_design
        from Pytorch.Models.GAM import GAM
        from Pytorch.Samplers.Hamil import Hamil

        no_basis = 20
        X_dist = td.Uniform(-10., 10)
        X = X_dist.sample(torch.Size([n]))
        Z = torch.tensor(get_design(X.numpy(), degree=2, no_basis=no_basis),
                         dtype=torch.float32, requires_grad=False)

        gam = GAM(order=1, bijected=bijected, **model_param)
        gam.reset_parameters()
        gam.true_model = gam.vec
        y = gam.likelihood(Z).sample()

        # sample
        hamil = Hamil(gam, Z, y, torch.ones_like(gam.vec))
        hamil.sample_NUTS(steps)

        # save the sampler instance (containing the model instance as attribute)
        # NOTICE: to recover the info, both the model class and the
        # sampler class must be imported, to make them accessible
        hamil.save(self.pathresults + self.hash + '.model')

        # TODO Autocorrelation time & thinning
        # TODO write out 1d / 2d plots


if __name__ == '__main__':
    gam_unittest = GAM_Nuts(root=os.getcwd() + '/Pytorch/Experiments/')

    # (1) bijected # FIXME: fails, since prior model is not implemented!
    gam_unittest.main(n=100, steps=1000, bijected=True, model_param={
        'no_basis':20
    })

    # (2) unbijected
    gam_unittest.main(n=100, steps=1000, bijected=False, model_param={
        'no_basis': 20
    })

    # (3) penK


    # RECONSTRUCTION FROM MODEL FILES: ----------------------------------------------
    # from Pytorch.Models.GAM import GAM
    # from Pytorch.Samplers.Hamil import Hamil
    #
    # # filter a dir for .model files
    # models = [m for m in os.listdir('results/') if m.endswith('.model')]
    #
    # loaded_hamil = torch.load('results/' +models[0])
    # loaded_hamil.chain

print()
