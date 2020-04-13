import tensorflow as tf
import tensorflow_probability as tfp

tfd = tfp.distributions


class Hidden:
    def __init__(self, input_shape, no_units=10, activation='relu'):
        """create independent normal priors with MVN(0,tau*I)"""

        self.input_shape = input_shape
        self.no_units = no_units

        identity = lambda x: x
        self.activation = {
            'relu': tf.nn.relu,
            'tanh': tf.math.tanh,
            'sigmoid': tf.math.sigmoid,
            'identity': identity}[activation]

        self.joint = tfd.JointDistributionNamed(dict(
            tau=tfd.InverseGamma(1., 1.),

            # sampling a W matrix
            # Notice: due to tfd.Sample: log_prob looks like this:
            #  joint.log_prob(W,t,b) == tf.math.reduce_sum(log_prob(W)) +log_prob(t) +log_prob(b)
            W=lambda tau: tfd.Sample(
                distribution=tfd.Normal(0., tau),
                sample_shape=(no_units, input_shape)),

            b=tfd.Normal(loc=tf.repeat(0., no_units), scale=1.)
            # y
        ))

    @tf.function
    def dense(self, x, **param):
        return self.activation(tf.linalg.matvec(param['W'], x) + param['b'])



class HiddenFinal(Hidden):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.joint = tfd.JointDistributionNamed(dict(
            tau=tfd.InverseGamma(1., 1.),

            W=lambda tau: tfd.Sample(
                distribution=tfd.Normal(0., tau),
                sample_shape=(self.no_units, self.input_shape)),
        ))

    # FIXME: refactor to HIDDEN STYLE!
    @tf.function
    def dense(self, x, **param):
        return self.activation(tf.linalg.matvec(param['W'], x))


if __name__ == '__main__':
    h = Hidden(input_shape=2, no_units=3, activation='relu')

    # check dense functon
    h.dense(x=tf.constant([1., 2.]),
            W=tf.constant([[1., 1.], [1., 2.], [3., 4.]]),  # three hidden units
            b=tf.constant([0.5, 1., 1.]))

    # check init from prior & dense
    h.init = h.joint.sample()
    h.joint.log_prob(**h.init)
    h.dense(x=tf.constant([1., 2.]),
            W=h.init['W'],
            b=h.init['b'])

print('')
