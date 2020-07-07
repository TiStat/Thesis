import torch
import torch.nn as nn
import torch.distributions as td

from hamiltorch.util import flatten, unflatten
from functools import partial


class Hidden(nn.Module):

    def __init__(self, no_in, no_out, bias=True, activation=nn.ReLU()):
        """notice: Due to the inability of writing inplace to nn.Parameters via
        vector_to_parameter(vec, model) whilst keeping the gradients. Using
        vector_to_parameter fails with the sampler.
        The currently expected Interface of log_prob is to recieve a 1D vector
        and use nn.Module & nn.Parameter (surrogate parameters trailing an
        underscore) merely as a skeleton for parsing the 1D
        vector using hamiltorch.util.unflatten (not inplace) - yielding a
        list of tensors. Using the property p_names, the list of tensors can
        be setattr-ibuted and accessed as attribute"""

        super().__init__()
        self.no_in = no_in
        self.no_out = no_out
        self.bias = bias
        self.activation = activation

        self.tau_w = 1.

        self.dist = [td.MultivariateNormal(
            torch.zeros(self.no_in * self.no_out),
            self.tau_w * torch.eye(self.no_in * self.no_out))]

        self.W_ = nn.Parameter(torch.Tensor(no_out, no_in))
        self.W = None

        if bias:
            self.b_ = nn.Parameter(torch.Tensor(self.no_out))
            self.tau_b = 1.
            self.b = None
            self.dist.append(td.Normal(0., 1.))

        self.reset_parameters()

        # occupied space in 1d vector
        self.n_params = sum([tensor.nelement() for tensor in self.parameters()])
        self.n_tensors = len(list(self.parameters()))

        # [tensor.shape for tensor in self.parameters()]
        # [torch.Size([1, 10]), torch.Size([1])]

    @property
    def p_names(self):
        return [p[:-1] for p in self._parameters]

    def reset_parameters(self):
        nn.init.xavier_normal_(self.W_)
        if self.bias:
            nn.init.normal_(self.b_)

    def forward(self, X):
        XW = X @ self.W.t()
        if self.bias:
            XW += self.b
        return self.activation(XW)

    def prior_log_prob(self):
        params = [self.W]
        if self.bias:
            params.append(self.b)
        return sum([dist.log_prob(tensor.view(tensor.nelement()))
                    for tensor, dist in zip(params, self.dist)])

    def likelihood(self, X):
        """:returns the conditional distribution of y | X"""
        return td.Normal(self.forward(X), scale=torch.tensor(1.))

    def log_prob(self, X, y, vec):
        """SG flavour of Log-prob: any batches of X & y can be used"""
        self.vec_to_attrs(vec)  # parsing to attributes
        return self.prior_log_prob().sum() + \
               self.likelihood(X).log_prob(y).sum()

    def closure_log_prob(self, X=None, y=None):
        """log_prob factory, to fix X & y for samplers operating on the entire
        dataset.
        :returns None. changes inplace attribute log_prob"""
        print('Setting up "Full Dataset" mode')
        self.log_prob = partial(self.log_prob, X, y)

    def vec_to_attrs(self, vec):
        """parsing a 1D tensor according to self.parameters & setting them
        as attributes"""
        tensorlist = unflatten(self, vec)
        for name, tensor in zip(self.p_names, tensorlist):
            self.__setattr__(name, tensor)


if __name__ == '__main__':
    no_in = 2
    no_out = 10

    # single Hidden Unit Example
    reg = Hidden(no_in, no_out, bias=True, activation=nn.Identity())
    reg.W = reg.W_.data
    reg.b = reg.b_.data
    reg.forward(X=torch.ones(100, 2))
    reg.prior_log_prob()

    # generate data X, y
    X_dist = td.Uniform(torch.tensor([-10., -10]), torch.tensor([10., 10]))
    X = X_dist.sample(torch.Size([100]))
    X.detach()
    X.requires_grad_()

    y = reg.likelihood(X).sample()
    y.detach()
    y.requires_grad_()

    # create 1D vector from nn.Parameters as Init + SG-Mode
    init_theta = flatten(reg)
    print(reg.log_prob(X, y, init_theta))

    # setting the log_prob to full dataset mode
    reg.closure_log_prob(X, y)
    print(reg.log_prob(init_theta))

    # Estimation example
    import hamiltorch
    import hamiltorch.util

    N = 200
    step_size = .3
    L = 5

    init_theta = hamiltorch.util.flatten(reg)
    params_hmc = hamiltorch.sample(
        log_prob_func=reg.log_prob, params_init=init_theta, num_samples=N,
        step_size=step_size, num_steps_per_sample=L)

    print()
