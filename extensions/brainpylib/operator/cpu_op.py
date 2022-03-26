# -*- coding: utf-8 -*-

import collections.abc
import ctypes
from functools import partial
from types import LambdaType
from typing import Callable, Union, Sequence

import jax.numpy as jnp
import numba
import numpy as np
from jax import core
from jax.abstract_arrays import ShapedArray
from jax.interpreters import xla
from jax.lib import xla_client
from numba import types
from numba.core.dispatcher import Dispatcher

_lambda_no = 0
ctypes.pythonapi.PyCapsule_New.argtypes = [
  ctypes.c_void_p,  # void* pointer
  ctypes.c_char_p,  # const char *name
  ctypes.c_void_p,  # PyCapsule_Destructor destructor
]
ctypes.pythonapi.PyCapsule_New.restype = ctypes.py_object


def _compile_cpu_signature(func, input_dtypes, input_shapes,
                           output_dtypes, output_shapes):
  code_scope = dict(
    func_to_call=func,
    input_shapes=input_shapes,
    input_dtypes=input_dtypes,
    output_shapes=output_shapes,
    output_dtypes=output_dtypes,
    carray=numba.carray,
  )

  args_in = [
    f'carray(input_ptrs[{i}], input_shapes[{i}], dtype=input_dtypes[{i}])'
    for i in range(len(input_shapes))
  ]
  args_out = [
    f'carray(output_ptrs[{i}], output_shapes[{i}], dtype=output_dtypes[{i}])'
    for i in range(len(output_shapes))
  ]

  code_string = '''
def xla_cpu_custom_call_target(output_ptrs, input_ptrs):
  args_out = (
    {args_out}
  )
  args_in = (
    {args_in}
  )
  func_to_call(args_out, args_in)
    '''.format(args_in=",\n    ".join(args_in),
               args_out=",\n    ".join(args_out))
  # print(code_string)
  exec(compile(code_string.strip(), '', 'exec'), code_scope)

  new_f = code_scope['xla_cpu_custom_call_target']
  wrapper = numba.cfunc(types.void(types.CPointer(types.voidptr),
                                   types.CPointer(types.voidptr)))
  xla_c_rule = wrapper(new_f)
  target_name = xla_c_rule.native_name.encode("ascii")
  capsule = ctypes.pythonapi.PyCapsule_New(
    xla_c_rule.address,  # A CFFI pointer to a function
    b"xla._CUSTOM_CALL_TARGET",  # A binary string
    None  # PyCapsule object run at destruction
  )
  xla_client.register_custom_call_target(target_name, capsule, "cpu")
  return target_name


def _func_translation(func, abs_eval_fn, c, *inputs):
  input_shapes = [c.get_shape(arg) for arg in inputs]
  input_dtypes = tuple(shape.element_type() for shape in input_shapes)
  input_dimensions = tuple(shape.dimensions() for shape in input_shapes)
  output_abstract_arrays = abs_eval_fn(*tuple(ShapedArray(shape.dimensions(), shape.element_type())
                                              for shape in input_shapes))
  output_shapes = tuple(array.shape for array in output_abstract_arrays)
  output_dtypes = tuple(array.dtype for array in output_abstract_arrays)
  output_layouts = map(lambda shape: range(len(shape) - 1, -1, -1), output_shapes)
  xla_output_shapes = [xla_client.Shape.array_shape(*arg)
                       for arg in zip(output_dtypes, output_shapes, output_layouts)]
  xla_output_shape = xla_client.Shape.tuple_shape(xla_output_shapes)
  target_name = _compile_cpu_signature(func,
                                       input_dtypes, input_dimensions,
                                       output_dtypes, output_shapes)

  return xla_client.ops.CustomCallWithLayout(
    c,
    target_name,
    operands=inputs,
    operand_shapes_with_layout=input_shapes,
    shape_with_layout=xla_output_shape,
  )


def register_cpu_op(
    func: Callable,
    out_shapes: Union[Callable, ShapedArray, Sequence[ShapedArray]]
):
  # primitive
  prim = core.Primitive(f'_lambda_func{_lambda_no}'
                        if (isinstance(func, LambdaType) and func.__name__ == "<lambda>")
                        else func.__name__)
  prim.multiple_results = True

  # user defined function
  if not isinstance(func, Dispatcher):
    func = numba.jit(fastmath=True, nopython=True)(func)

  # output shape evaluation function
  def abs_eval_rule(*input_shapes):
    if callable(out_shapes):
      shapes = out_shapes(*input_shapes)
    elif isinstance(out_shapes, ShapedArray):
      shapes = [out_shapes]
    elif isinstance(out_shapes, (tuple, list)):
      shapes = out_shapes
      for elem in out_shapes:
        if not isinstance(elem, ShapedArray):
          raise ValueError(f'Elements in "out_shapes" must be instances of '
                           f'jax.abstract_arrays.ShapedArray, but we got '
                           f'{type(elem)}: {elem}')
    else:
      raise ValueError(f'Unknown type {type(out_shapes)}, only '
                       f'supports function, ShapedArray or '
                       f'list/tuple of ShapedArray.')

    # output shapes
    if not isinstance(shapes, collections.abc.Collection):
      return [shapes]
    else:
      return shapes

  # output evaluation function
  def eval_rule(*inputs):
    # compute the output shapes
    output_shapes = abs_eval_rule(*inputs)
    # Preallocate the outputs
    outputs = tuple(np.zeros(shape.shape, dtype=shape.dtype) for shape in output_shapes)
    # convert inputs to a tuple
    inputs = tuple(np.asarray(arg) for arg in inputs)
    # call the kernel
    func(outputs, inputs)
    # Return the outputs
    return tuple(outputs)

  def bind_primitive(*inputs):
    result = prim.bind(*inputs)
    return result[0] if len(result) == 1 else result

  # binding
  prim.def_abstract_eval(abs_eval_rule)
  prim.def_impl(eval_rule)
  # registering
  xla.backend_specific_translations['cpu'][prim] = partial(_func_translation, func, abs_eval_rule)
  return bind_primitive


if __name__ == '__main__':
  def abs_eval(*ins):
    return ins

  import brainpy as bp
  bp.math.set_platform('cpu')

  def custom_op(outs, ins):
    y, y1 = outs
    x, x2 = ins
    y[:] = x + 1
    y1[:] = x2 + 2


  z = jnp.ones((1, 2), dtype=jnp.float32)
  op = register_cpu_op(custom_op, abs_eval)

  from jax import jit
  jit_op = jit(op)

  print(jit_op(z, z))
