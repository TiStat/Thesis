import tensorflow as tf
import tensorflow_probability as tfp

tfd = tfp.distributions
tfb = tfp.bijectors


class Data_BNN_1D:
    def __init__(self, n, grid=(0, 10, 0.5)):
        """One dimensional effect"""
        from Python.Effects.Cases1D.Bspline_GMRF import Bspline_GMRF
        self.gmrf = Bspline_GMRF(xgrid=grid)

        self.n = n
        self.X = tfd.Uniform(grid[0], grid[1]).sample((self.n,))
        self.y = self.true_likelihood(self.X).sample((self.n,))

    def true_likelihood(self, X):
        self.mu = tf.constant(self.gmrf.spl(X), dtype=tf.float32)
        y = tfd.MultivariateNormalDiag(
            loc=self.mu,
            scale_diag=tf.repeat(1., self.mu.shape[0]))
        return y


class Data_BNN_2D:
    def __init__(self, n, grid=(0, 10, 0.5)):
        """complex two dimensional effect, no main effects"""
        from Python.Effects.Cases2D.K.GMRF_K import GMRF_K
        self.gmrf = GMRF_K(xgrid=grid, ygrid=grid)

        self.n = n
        self.X = tf.stack(
            values=[tfd.Uniform(grid[0], grid[1]).sample((self.n,)),
                    tfd.Uniform(grid[0], grid[1]).sample((self.n,))],
            axis=1)
        self.y = self.true_likelihood(self.X).sample((self.n,))

    def true_likelihood(self, X):
        self.mu = tf.constant(self.gmrf.surface(X), dtype=tf.float32)
        y = tfd.MultivariateNormalDiag(
            loc=self.mu,
            scale_diag=tf.repeat(1., self.mu.shape[0]))
        return y


if __name__ == '__main__':
    from Python.Bayesian.Models.BNN import BNN
    # (0) (generating data) ----------------------------------
    data = Data_BNN_2D(n=1000, grid=(0, 10, 0.5))

    # (1) (setting up posterior model) -----------------------
    bnn = BNN(hunits=[2, 10, 9, 8, 1], activation='relu')
    # data = Data_BNN_2D(n=1000, grid=(0, 10, 0.5))
    # bnn.unnormalized_log_prob = bnn._closure_log_prob(data.X, data.y)

    # (2) (sampling posterior) -------------------------------
    # FIXME BNN initial
    # from Python.Bayesian.Samplers import AdaptiveHMC
    # bnn._initialize_from_prior()
    # adHMC = AdaptiveHMC(initial=initial,
    #             bijectors=tfb.Identity(),
    #             log_prob=bnn.unnormalized_log_prob)
    #
    # samples, traced = adHMC.sample_chain(
    #     logdir='/home/tim/PycharmProjects/Thesis/TFResults')