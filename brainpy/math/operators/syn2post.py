# -*- coding: utf-8 -*-

import jax.numpy as jnp
from jax import jit, vmap
from jax import ops as jops

from brainpy.math.numpy_ops import as_device_array


_jit_seg_sum = jit(jops.segment_sum, static_argnums=(2, 3))
_jit_seg_prod = jit(jops.segment_prod, static_argnums=(2, 3))
_jit_seg_max = jit(jops.segment_max, static_argnums=(2, 3))
_jit_seg_min = jit(jops.segment_min, static_argnums=(2, 3))


__all__ = [
  'syn2post_sum', 'syn2post',
  'syn2post_prod',
  'syn2post_max',
  'syn2post_min',
  'syn2post_mean',
  'syn2post_softmax',

]


def syn2post_sum(syn_values, post_ids, post_num: int, indices_are_sorted=True):
  """The syn-to-post summation computation.

  This function is equivalent to:

  .. highlight:: python
  .. code-block:: python

    post_val = np.zeros(post_num)
    for syn_i, post_i in enumerate(post_ids):
      post_val[post_i] += syn_values[syn_i]

  Parameters
  ----------
  syn_values: jax.numpy.ndarray, JaxArray, Variable
    The synaptic values.
  post_ids: jax.numpy.ndarray, JaxArray
    The post-synaptic neuron ids.
  post_num: int
    The number of the post-synaptic neurons.

  Returns
  -------
  post_val: jax.numpy.ndarray, JaxArray
    The post-synaptic value.
  """
  post_ids = as_device_array(post_ids)
  syn_values = as_device_array(syn_values)
  if syn_values.dtype == jnp.bool_:
    syn_values = jnp.asarray(syn_values, dtype=jnp.int32)
  return _jit_seg_sum(syn_values, post_ids, post_num, indices_are_sorted)


syn2post = syn2post_sum


def syn2post_prod(syn_values, post_ids, post_num: int, indices_are_sorted=True):
  """The syn-to-post product computation.

  This function is equivalent to:

  .. highlight:: python
  .. code-block:: python

    post_val = np.zeros(post_num)
    for syn_i, post_i in enumerate(post_ids):
      post_val[post_i] *= syn_values[syn_i]

  Parameters
  ----------
  syn_values: jax.numpy.ndarray, JaxArray, Variable
    The synaptic values.
  post_ids: jax.numpy.ndarray, JaxArray
    The post-synaptic neuron ids. If ``post_ids`` is generated by
    ``brainpy.conn.TwoEndConnector``, then it has sorted indices.
    Otherwise, this function cannot guarantee indices are sorted.
    You's better set ``indices_are_sorted=False``.
  post_num: int
    The number of the post-synaptic neurons.
  indices_are_sorted: whether ``post_ids`` is known to be sorted.

  Returns
  -------
  post_val: jax.numpy.ndarray, JaxArray
    The post-synaptic value.
  """
  post_ids = as_device_array(post_ids)
  syn_values = as_device_array(syn_values)
  if syn_values.dtype == jnp.bool_:
    syn_values = jnp.asarray(syn_values, dtype=jnp.int32)
  return _jit_seg_prod(syn_values, post_ids, post_num, indices_are_sorted)


def syn2post_max(syn_values, post_ids, post_num: int, indices_are_sorted=True):
  """The syn-to-post maximum computation.

  This function is equivalent to:

  .. highlight:: python
  .. code-block:: python

    post_val = np.zeros(post_num)
    for syn_i, post_i in enumerate(post_ids):
      post_val[post_i] = np.maximum(post_val[post_i], syn_values[syn_i])

  Parameters
  ----------
  syn_values: jax.numpy.ndarray, JaxArray, Variable
    The synaptic values.
  post_ids: jax.numpy.ndarray, JaxArray
    The post-synaptic neuron ids. If ``post_ids`` is generated by
    ``brainpy.conn.TwoEndConnector``, then it has sorted indices.
    Otherwise, this function cannot guarantee indices are sorted.
    You's better set ``indices_are_sorted=False``.
  post_num: int
    The number of the post-synaptic neurons.
  indices_are_sorted: whether ``post_ids`` is known to be sorted.

  Returns
  -------
  post_val: jax.numpy.ndarray, JaxArray
    The post-synaptic value.
  """
  post_ids = as_device_array(post_ids)
  syn_values = as_device_array(syn_values)
  if syn_values.dtype == jnp.bool_:
    syn_values = jnp.asarray(syn_values, dtype=jnp.int32)
  return _jit_seg_max(syn_values, post_ids, post_num, indices_are_sorted)


def syn2post_min(syn_values, post_ids, post_num: int, indices_are_sorted=True):
  """The syn-to-post minimization computation.

  This function is equivalent to:

  .. highlight:: python
  .. code-block:: python

    post_val = np.zeros(post_num)
    for syn_i, post_i in enumerate(post_ids):
      post_val[post_i] = np.minimum(post_val[post_i], syn_values[syn_i])

  Parameters
  ----------
  syn_values: jax.numpy.ndarray, JaxArray, Variable
    The synaptic values.
  post_ids: jax.numpy.ndarray, JaxArray
    The post-synaptic neuron ids. If ``post_ids`` is generated by
    ``brainpy.conn.TwoEndConnector``, then it has sorted indices.
    Otherwise, this function cannot guarantee indices are sorted.
    You's better set ``indices_are_sorted=False``.
  post_num: int
    The number of the post-synaptic neurons.
  indices_are_sorted: whether ``post_ids`` is known to be sorted.

  Returns
  -------
  post_val: jax.numpy.ndarray, JaxArray
    The post-synaptic value.
  """
  post_ids = as_device_array(post_ids)
  syn_values = as_device_array(syn_values)
  if syn_values.dtype == jnp.bool_:
    syn_values = jnp.asarray(syn_values, dtype=jnp.int32)
  return _jit_seg_min(syn_values, post_ids, post_num, indices_are_sorted)


def syn2post_mean(syn_values, post_ids, post_num: int, indices_are_sorted=True):
  """The syn-to-post mean computation.

  Parameters
  ----------
  syn_values: jax.numpy.ndarray, JaxArray, Variable
    The synaptic values.
  post_ids: jax.numpy.ndarray, JaxArray
    The post-synaptic neuron ids. If ``post_ids`` is generated by
    ``brainpy.conn.TwoEndConnector``, then it has sorted indices.
    Otherwise, this function cannot guarantee indices are sorted.
    You's better set ``indices_are_sorted=False``.
  post_num: int
    The number of the post-synaptic neurons.
  indices_are_sorted: whether ``post_ids`` is known to be sorted.

  Returns
  -------
  post_val: jax.numpy.ndarray, JaxArray
    The post-synaptic value.
  """
  post_ids = as_device_array(post_ids)
  syn_values = as_device_array(syn_values)
  if syn_values.dtype == jnp.bool_:
    syn_values = jnp.asarray(syn_values, dtype=jnp.int32)
  nominator = _jit_seg_sum(syn_values, post_ids, post_num, indices_are_sorted)
  denominator = _jit_seg_sum(jnp.ones_like(syn_values), post_ids, post_num, indices_are_sorted)
  return jnp.nan_to_num(nominator / denominator)


def syn2post_softmax(syn_values, post_ids, post_num: int, indices_are_sorted=True):
  """The syn-to-post softmax computation.

  Parameters
  ----------
  syn_values: jax.numpy.ndarray, JaxArray, Variable
    The synaptic values.
  post_ids: jax.numpy.ndarray, JaxArray
    The post-synaptic neuron ids. If ``post_ids`` is generated by
    ``brainpy.conn.TwoEndConnector``, then it has sorted indices.
    Otherwise, this function cannot guarantee indices are sorted.
    You's better set ``indices_are_sorted=False``.
  post_num: int
    The number of the post-synaptic neurons.
  indices_are_sorted: whether ``post_ids`` is known to be sorted.

  Returns
  -------
  post_val: jax.numpy.ndarray, JaxArray
    The post-synaptic value.
  """
  post_ids = as_device_array(post_ids)
  syn_values = as_device_array(syn_values)
  if syn_values.dtype == jnp.bool_:
    syn_values = jnp.asarray(syn_values, dtype=jnp.int32)
  syn_maxs = _jit_seg_max(syn_values, post_ids, post_num, indices_are_sorted)
  syn_values = syn_values - syn_maxs[post_ids]
  syn_values = jnp.exp(syn_values)
  normalizers = _jit_seg_sum(syn_values, post_ids, post_num, indices_are_sorted)
  softmax = syn_values / normalizers[post_ids]
  return jnp.nan_to_num(softmax)
