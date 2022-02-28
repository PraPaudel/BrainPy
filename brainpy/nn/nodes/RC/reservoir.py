# -*- coding: utf-8 -*-

from typing import Optional, Union, Callable

import brainpy.math as bm
from brainpy.initialize import Normal, ZeroInit, Initializer
from brainpy.nn.base import Node
from brainpy.nn.utils import init_param
from brainpy.tools.checking import (check_shape_consistency,
                                    check_float,
                                    check_initializer,
                                    check_string)
from brainpy.types import Tensor

__all__ = [
  'Reservoir',
]


class Reservoir(Node):
  r"""Reservoir node, a pool of leaky-integrator neurons
  with random recurrent connections [1]_.

  Parameters
  ----------
  num_unit: int
    The number of reservoir nodes.
  init_ff: Initializer
    The initialization method for the feedforward connections.
  init_rec: Initializer
    The initialization method for the recurrent connections.
  init_fb: optional, Tensor, Initializer
    The initialization method for the feedback connections.
  init_bias: optional, Tensor, Initializer
    The initialization method for the bias.
  leaky_rate: float
    A float between 0 and 1.
  activation : str, callable, optional
    Reservoir activation function.
    - If a str, should be a :py:mod:`brainpy.math.activations` function name.
    - If a callable, should be an element-wise operator on tensor.
  activation_type : str
    - If "internal" (default), then leaky integration happens on states transformed
    by the activation function:

    .. math::

        r[n+1] = (1 - \alpha) \cdot r[t] +
        \alpha \cdot f(W_{ff} \cdot u[n] + W_{fb} \cdot b[n] + W_{rec} \cdot r[t])

    - If "external", then leaky integration happens on internal states of
    each neuron, stored in an ``internal_state`` parameter (:math:`x` in
    the equation below).
    A neuron internal state is the value of its state before applying
    the activation function :math:`f`:

    .. math::

        x[n+1] &= (1 - \alpha) \cdot x[t] +
        \alpha \cdot f(W_{ff} \cdot u[n] + W_{rec} \cdot r[t] + W_{fb} \cdot b[n]) \\
        r[n+1] &= f(x[n+1])
  ff_connectivity : float, optional
    Connectivity of input neurons, i.e. ratio of input neurons connected
    to reservoir neurons. Must be in [0, 1], by default 0.1
  rec_connectivity : float, optional
    Connectivity of recurrent weights matrix, i.e. ratio of reservoir
    neurons connected to other reservoir neurons, including themselves.
    Must be in [0, 1], by default 0.1
  fb_connectivity : float, optional
    Connectivity of feedback neurons, i.e. ratio of feedabck neurons
    connected to reservoir neurons. Must be in [0, 1], by default 0.1
  spectral_radius : float, optional
    Spectral radius of recurrent weight matrix, by default None
  noise_rec : float, optional
    Gain of noise applied to reservoir internal states, by default 0.0
  noise_in : float, optional
    Gain of noise applied to feedforward signals, by default 0.0
  noise_fb : float, optional
    Gain of noise applied to feedback signals, by default 0.0
  noise_type : optional, str, callable
    Distribution of noise. Must be a random variable generator
    distribution (see :py:class:`brainpy.math.random.RandomState`),
    by default "normal". 
  seed: optional, int
    The seed for random sampling in this node.

  References
  ----------
  .. [1] Lukoševičius, Mantas. "A practical guide to applying echo state networks."
         Neural networks: Tricks of the trade. Springer, Berlin, Heidelberg, 2012. 659-686.
  """

  def __init__(
      self,
      num_unit: int,
      leaky_rate: float = 0.3,
      activation: Union[str, Callable] = 'tanh',
      activation_type: str = 'internal',
      init_ff: Union[Initializer, Callable, Tensor] = Normal(),
      init_rec: Union[Initializer, Callable, Tensor] = Normal(),
      init_fb: Optional[Union[Initializer, Callable, Tensor]] = Normal(),
      init_bias: Optional[Union[Initializer, Callable, Tensor]] = ZeroInit(),
      ff_connectivity: float = 0.1,
      rec_connectivity: float = 0.1,
      fb_connectivity: float = 0.1,
      spectral_radius: Optional[float] = None,
      noise_ff: float = 0.,
      noise_rec: float = 0.,
      noise_fb: float = 0.,
      noise_type: str = 'normal',
      seed: Optional[int] = None,
      **kwargs
  ):
    super(Reservoir, self).__init__(**kwargs)

    # parameters
    self.num_unit = num_unit
    assert num_unit > 0, f'Must be a positive integer, but we got {num_unit}'
    self.leaky_rate = leaky_rate
    check_float(leaky_rate, 'leaky_rate', 0., 1.)
    self.activation = bm.activations.get(activation)
    self.activation_type = activation_type
    check_string(activation_type, 'activation_type', ['internal', 'external'])
    self.rng = bm.random.RandomState(seed)

    # initializations
    check_initializer(init_ff, 'init_ff', allow_none=False)
    check_initializer(init_rec, 'init_rec', allow_none=False)
    check_initializer(init_fb, 'init_fb', allow_none=True)
    check_initializer(init_bias, 'init_bias', allow_none=True)
    self.init_ff = init_ff
    self.init_fb = init_fb
    self.init_rec = init_rec
    self.init_bias = init_bias
    check_float(ff_connectivity, 'ff_connectivity', 0., 1.)
    check_float(rec_connectivity, 'rec_connectivity', 0., 1.)
    check_float(fb_connectivity, 'fb_connectivity', 0., 1.)
    self.ff_connectivity = ff_connectivity
    self.rec_connectivity = rec_connectivity
    self.fb_connectivity = fb_connectivity
    check_float(spectral_radius, 'spectral_radius', allow_none=True)
    self.spectral_radius = spectral_radius

    # noises
    check_float(noise_ff, 'noise_ff')
    check_float(noise_fb, 'noise_fb')
    check_float(noise_rec, 'noise_rec')
    self.noise_ff = noise_ff
    self.noise_fb = noise_fb
    self.noise_rec = noise_rec
    self.noise_type = noise_type
    check_string(noise_type, 'noise_type', ['normal', 'uniform'])

  def ff_init(self):
    unique_shape, free_shapes = check_shape_consistency(self.input_shapes, -1, True)
    self.set_output_shape(unique_shape + (self.num_unit,))
    # initialize feedforward weights
    weight_shape = (sum(free_shapes), self.num_unit)
    self.Wff = init_param(self.init_ff, weight_shape)
    if self.ff_connectivity < 1.:
      self.Wff[self.rng.random(weight_shape) > self.ff_connectivity] = 0.
    if self.trainable:
      self.Wff = bm.TrainVar(self.Wff)
    # initialize recurrent weights
    recurrent_shape = (self.num_unit, self.num_unit)
    self.Wrec = init_param(self.init_rec, recurrent_shape)
    if self.rec_connectivity < 1.:
      self.Wrec[self.rng.random(recurrent_shape) > self.rec_connectivity] = 0.
    if self.spectral_radius is not None:
      current_sr = max(abs(bm.linalg.eig(self.Wrec)[0]))
      self.Wrec *= self.spectral_radius / current_sr
    self.bias = init_param(self.init_bias, (self.num_unit,))
    if self.trainable:
      self.Wrec = bm.TrainVar(self.Wrec)
      self.bias = None if (self.bias is None) else bm.TrainVar(self.bias)
    # initialize feedback weights
    self.Wfb = None
    # initialize internal state
    self.state = bm.Variable(bm.zeros((self.num_unit,), dtype=bm.float_))

  def fb_init(self):
    if self.feedback_shapes is not None:
      check_initializer(self.init_fb, 'init_fb', allow_none=False)
      unique_shape, free_shapes = check_shape_consistency(self.feedback_shapes, -1, True)
      fb_shape = (sum(free_shapes), self.num_unit)
      self.Wfb = init_param(self.init_fb, fb_shape)
      if self.fb_connectivity < 1.:
        self.Wfb[self.rng.random(fb_shape) > self.fb_connectivity] = 0.
      if self.trainable:
        self.Wfb = bm.TrainVar(self.Wfb)

  def call(self, ff, fb=None, **kwargs):
    # inputs
    x = bm.concatenate(ff, axis=-1)
    if self.noise_ff > 0: x += self.noise_ff * self.rng.uniform(-1, 1, x.shape)
    hidden = bm.dot(x, self.Wff)
    # feedback
    if self.Wfb is not None:
      assert fb is not None, 'Do not provide feedback signals'
      fb = bm.concatenate(fb, axis=-1)
      if self.noise_fb: fb += self.noise_fb * self.rng.uniform(-1, 1, fb.shape)
      hidden += bm.dot(fb, self.Wfb)
    # recurrent
    hidden += bm.dot(self.state, self.Wrec)
    if self.activation_type == 'internal':
      hidden = self.activation(hidden)
    if self.noise_rec > 0.: hidden += self.noise_rec * self.rng.uniform(-1, -1, self.state.shape)
    # new state/output
    state = (1 - self.leaky_rate) * self.state + self.leaky_rate * hidden
    if self.activation_type == 'external':
      state = self.activation(state)
    self.state.value = state
    return state