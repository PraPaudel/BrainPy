# -*- coding: utf-8 -*-

import sys
import logging

import jax.numpy as jnp
import matplotlib.pyplot as plt
import numpy as np

import brainpy.math as bm
from brainpy import errors, math
from brainpy.analysis import stability, constants as C, utils
from brainpy.analysis.numeric.lowdim_analyzer import *

_file = sys.stderr

__all__ = [
  'PhasePlane1D',
  'PhasePlane2D',
]


class PhasePlane1D(Num1DAnalyzer):
  """Phase plane analyzer for 1D dynamical system.

  This class can help users fast check:

  - Vector fields
  - Fixed points

  Parameters
  ----------
  model : Any, Integrator, sequence of Integrator, DynamicalSystem
      A model of the population, the integrator function,
      or a list/tuple of integrator functions.
  target_vars : dict
      The target/dynamical variables.
  fixed_vars : dict
      The fixed variables.
  target_pars : dict, optional
      The parameters which can be dynamical varied.
  pars_update : dict, optional
      The parameters to update.
  resolutions : float, dict

  """

  def __init__(self,
               model,
               target_vars,
               fixed_vars=None,
               target_pars=None,
               pars_update=None,
               resolutions=None,
               **kwargs):
    if (target_pars is not None) and len(target_pars) > 0:
      raise errors.AnalyzerError(f'Phase plane analysis does not support "target_pars". '
                                 f'While we detect "target_pars={target_pars}".')
    super(PhasePlane1D, self).__init__(model=model,
                                       target_vars=target_vars,
                                       fixed_vars=fixed_vars,
                                       target_pars=target_pars,
                                       pars_update=pars_update,
                                       resolutions=resolutions,
                                       **kwargs)
    # print(f'I am {PhasePlane1D.__name__}.')

  def plot_vector_field(self, show=False, with_plot=True, with_return=False):
    """Plot the vector filed."""
    print('I am creating vector fields ...')

    # Nullcline of the x variable
    y_val = self.F_fx(self.resolutions[self.x_var])
    y_val = np.asarray(y_val)

    # visualization
    if with_plot:
      label = f"d{self.x_var}dt"
      x_style = dict(color='lightcoral', alpha=.7, linewidth=4)
      plt.plot(np.asarray(self.resolutions[self.x_var]), y_val, **x_style, label=label)
      plt.axhline(0)
      plt.xlabel(self.x_var)
      plt.ylabel(label)
      plt.xlim(*utils.rescale(self.target_vars[self.x_var], scale=(self.lim_scale - 1.) / 2))
      plt.legend()
      if show: plt.show()
    # return
    if with_return:
      return y_val

  def plot_fixed_point(self, show=False, with_plot=True, with_return=False):
    """Plot the fixed point."""
    print('I am searching fixed points ...')

    # fixed points and stability analysis
    fps, _ = self._get_fixed_points(self.resolutions[self.x_var])
    container = {a: [] for a in stability.get_1d_stability_types()}
    for i in range(len(fps)):
      x = fps[i]
      dfdx = self.F_dfxdx(x)
      fp_type = stability.stability_analysis(dfdx)
      print(f"Fixed point #{i + 1} at {self.x_var}={x} is a {fp_type}.")
      container[fp_type].append(x)

    # visualization
    if with_plot:
      for fp_type, points in container.items():
        if len(points):
          plot_style = stability.plot_scheme[fp_type]
          plt.plot(points, [0] * len(points), '.', markersize=20, **plot_style, label=fp_type)
      plt.legend()
      if show:
        plt.show()

    # return
    if with_return:
      return fps


class PhasePlane2D(Num2DAnalyzer):
  """Phase plane analyzer for 2D dynamical system.

  Parameters
  ----------
  model : Any
    A model of the population, the integrator function,
    or a list/tuple of integrator functions.
  target_vars : dict
    The target/dynamical variables.
  fixed_vars : dict
    The fixed variables.
  target_pars : dict, optional
    The parameters which can be dynamical varied.
  pars_update : dict, optional
    The parameters to update.
  resolutions : float, dict
  """

  def __init__(self,
               model,
               target_vars,
               fixed_vars=None,
               target_pars=None,
               pars_update=None,
               resolutions=None,
               **kwargs):
    if (target_pars is not None) and len(target_pars) > 0:
      raise errors.AnalyzerError(f'Phase plane analysis does not support "target_pars". '
                                 f'While we detect "target_pars={target_pars}".')
    super(PhasePlane2D, self).__init__(model=model,
                                       target_vars=target_vars,
                                       fixed_vars=fixed_vars,
                                       target_pars=target_pars,
                                       pars_update=pars_update,
                                       resolutions=resolutions,
                                       **kwargs)
    # print(f'I am {PhasePlane2DNum.__name__}.')

  @property
  def F_vmap_brentq_fy(self):
    if C.F_vmap_brentq_fy not in self.analyzed_results:
      f_opt = bm.jit(bm.vmap(utils.jax_brentq(self.F_fy)))
      self.analyzed_results[C.F_vmap_brentq_fy] = f_opt
    return self.analyzed_results[C.F_vmap_brentq_fy]

  def plot_vector_field(self, with_plot=True, with_return=False,
                        plot_method='streamplot', plot_style=None, show=False):
    """Plot the vector field.

    Parameters
    ----------
    with_plot: bool
    with_return : bool
    show : bool
    plot_method : str
        The method to plot the vector filed. It can be "streamplot" or "quiver".
    plot_style : dict, optional
        The style for vector filed plotting.

        - For ``plot_method="streamplot"``, it can set the keywords like "density",
          "linewidth", "color", "arrowsize". More settings please check
          https://matplotlib.org/api/_as_gen/matplotlib.pyplot.streamplot.html.
        - For ``plot_method="quiver"``, it can set the keywords like "color",
          "units", "angles", "scale". More settings please check
          https://matplotlib.org/api/_as_gen/matplotlib.pyplot.quiver.html.
    """
    print('I am creating vector fields ...')

    # get dx, dy
    xs = self.resolutions[self.x_var]
    ys = self.resolutions[self.y_var]
    X, Y = bm.meshgrid(xs, ys)
    dx = self.F_fx(X, Y)
    dy = self.F_fy(X, Y)
    X, Y = np.asarray(X), np.asarray(Y)
    dx, dy = np.asarray(dx), np.asarray(dy)

    # vector field
    if with_plot:
      if plot_method == 'quiver':
        if plot_style is None:
          plot_style = dict(units='xy')
        if (not np.isnan(dx).any()) and (not np.isnan(dy).any()):
          speed = np.sqrt(dx ** 2 + dy ** 2)
          dx = dx / speed
          dy = dy / speed
        plt.quiver(X, Y, dx, dy, **plot_style)
      elif plot_method == 'streamplot':
        if plot_style is None:
          plot_style = dict(arrowsize=1.2, density=1, color='thistle')
        linewidth = plot_style.get('linewidth', None)
        if linewidth is None:
          if (not np.isnan(dx).any()) and (not np.isnan(dy).any()):
            min_width, max_width = 0.5, 5.5
            speed = np.nan_to_num(np.sqrt(dx ** 2 + dy ** 2))
            linewidth = min_width + max_width * (speed / speed.max())
        plt.streamplot(X, Y, dx, dy, linewidth=linewidth, **plot_style)
      else:
        raise ValueError(f'Unknown plot_method "{plot_method}", only supports "quiver" and "streamplot".')

      plt.xlabel(self.x_var)
      plt.ylabel(self.y_var)
      if show:
        plt.show()

    if with_return:
      return dx, dy

  def plot_nullcline(self, with_plot=True, with_return=False, y_style=None, x_style=None,
                     show=False, coords=None, tol_nullcline=1e-7):
    """Plot the nullcline."""
    print('I am computing fx-nullcline ...')

    if coords is None:
      coords = dict()
    x_coord = coords.get(self.x_var, None)
    y_coord = coords.get(self.y_var, None)

    # Nullcline of the x variable
    # ---------------------------
    xy_values_in_fx,  = self._get_fx_nullcline_points(coords=x_coord, tol=tol_nullcline)
    x_values_in_fx = np.asarray(xy_values_in_fx[:, 0])
    y_values_in_fx = np.asarray(xy_values_in_fx[:, 1])
    if with_plot:
      if x_style is None:
        x_style = dict(color='cornflowerblue', alpha=.7, marker='.')
        x_style = dict(color='cornflowerblue', alpha=.7, )
      plt.plot(x_values_in_fx, y_values_in_fx, '.', **x_style, label=f"{self.x_var} nullcline")

    # Nullcline of the y variable
    # ---------------------------
    print('I am computing fy-nullcline ...')
    xy_values_in_fy,  = self._get_fy_nullcline_points(coords=y_coord, tol=tol_nullcline)
    x_values_in_fy = np.asarray(xy_values_in_fy[:, 0])
    y_values_in_fy = np.asarray(xy_values_in_fy[:, 1])
    if with_plot:
      if y_style is None:
        y_style = dict(color='lightcoral', alpha=.7, marker='.')
        y_style = dict(color='lightcoral', alpha=.7, )
      plt.plot(x_values_in_fy, y_values_in_fy, '.', **y_style, label=f"{self.y_var} nullcline")

    if with_plot:
      plt.xlabel(self.x_var)
      plt.ylabel(self.y_var)
      scale = (self.lim_scale - 1.) / 2
      plt.xlim(*utils.rescale(self.target_vars[self.x_var], scale=scale))
      plt.ylim(*utils.rescale(self.target_vars[self.y_var], scale=scale))
      plt.legend()
      if show:
        plt.show()

    if with_return:
      return {self.x_var: (x_values_in_fx, y_values_in_fx),
              self.y_var: (x_values_in_fy, y_values_in_fy)}

  def plot_fixed_point(self, with_plot=True, with_return=False, show=False,
                       tol_unique=1e-2, tol_loss=1e-7, loss_screen=None):
    """Plot the fixed point and analyze its stability.
    """
    print('I am searching fixed points ...')

    # candidates
    candidates = []
    for key in self.analyzed_results.keys():
      if key.startswith(C.fx_nullcline_points) or key.startswith(C.fy_nullcline_points):
        candidates.append(self.analyzed_results[key][0])
    if len(candidates) == 0:
      raise errors.AnalyzerError(f'No nullcline points are found, please call '
                                 f'".{self.plot_nullcline.__name__}()" first.')
    candidates = jnp.vstack(candidates)

    # get fixed points
    if len(candidates):
      fixed_points, _, _ = self._get_fixed_points(jnp.asarray(candidates),
                                                  tol_loss=tol_loss,
                                                  tol_unique=tol_unique,
                                                  loss_screen=loss_screen)
      print('I am trying to filter out duplicate fixed points ...')
      fixed_points = np.asarray(fixed_points)
      fixed_points, _ = utils.keep_unique(fixed_points, tol=tol_unique)
      print(f'{C.prefix}Found {len(fixed_points)} fixed points.')
    else:
      print(f'{C.prefix}Found no fixed points.')
      return

    # stability analysis
    # ------------------
    container = {a: {'x': [], 'y': []} for a in stability.get_2d_stability_types()}
    for i in range(len(fixed_points)):
      x = fixed_points[i, 0]
      y = fixed_points[i, 1]
      fp_type = stability.stability_analysis(self.F_jacobian(x, y))
      print(f"{C.prefix}#{i + 1} {self.x_var}={x}, {self.y_var}={y} is a {fp_type}.")
      container[fp_type]['x'].append(x)
      container[fp_type]['y'].append(y)

    # visualization
    # -------------
    if with_plot:
      for fp_type, points in container.items():
        if len(points['x']):
          plot_style = stability.plot_scheme[fp_type]
          plt.plot(points['x'], points['y'], '.', markersize=20, **plot_style, label=fp_type)
      plt.legend()
      if show:
        plt.show()

    if with_return:
      return fixed_points

  def plot_trajectory(self, initials, duration, plot_duration=None, axes='v-v', show=False):
    """Plot trajectories according to the settings.

    Parameters
    ----------
    initials : list, tuple, dict
        The initial value setting of the targets. It can be a tuple/list of floats to specify
        each value of dynamical variables (for example, ``(a, b)``). It can also be a
        tuple/list of tuple to specify multiple initial values (for example,
        ``[(a1, b1), (a2, b2)]``).
    duration : int, float, tuple, list
        The running duration. Same with the ``duration`` in ``NeuGroup.run()``.

        - It can be a int/float (``t_end``) to specify the same running end time,
        - Or it can be a tuple/list of int/float (``(t_start, t_end)``) to specify
          the start and end simulation time.
        - Or, it can be a list of tuple (``[(t1_start, t1_end), (t2_start, t2_end)]``)
          to specify the specific start and end simulation time for each initial value.
    plot_duration : tuple, list, optional
        The duration to plot. It can be a tuple with ``(start, end)``. It can
        also be a list of tuple ``[(start1, end1), (start2, end2)]`` to specify
        the plot duration for each initial value running.
    axes : str
        The axes to plot. It can be:

         - 'v-v': Plot the trajectory in the 'x_var'-'y_var' axis.
         - 't-v': Plot the trajectory in the 'time'-'var' axis.
    show : bool
        Whether show or not.
    """

    print('plot trajectory ...')

    if axes not in ['v-v', 't-v']:
      raise errors.BrainPyError(f'Unknown axes "{axes}", only support "v-v" and "t-v".')

    # 1. format the initial values
    if isinstance(initials, dict):
      initials = [initials]
    elif isinstance(initials, (list, tuple)):
      if isinstance(initials[0], (int, float)):
        initials = [{self.target_var_names[i]: v for i, v in enumerate(initials)}]
      elif isinstance(initials[0], dict):
        initials = initials
      elif isinstance(initials[0], (tuple, list)) and isinstance(initials[0][0], (int, float)):
        initials = [{self.target_var_names[i]: v for i, v in enumerate(init)} for init in initials]
      else:
        raise ValueError
    else:
      raise ValueError

    # 2. format the running duration
    if isinstance(duration, (int, float)):
      duration = [(0, duration) for _ in range(len(initials))]
    elif isinstance(duration[0], (int, float)):
      duration = [duration for _ in range(len(initials))]
    else:
      assert len(duration) == len(initials)

    # 3. format the plot duration
    if plot_duration is None:
      plot_duration = duration
    if isinstance(plot_duration[0], (int, float)):
      plot_duration = [plot_duration for _ in range(len(initials))]
    else:
      assert len(plot_duration) == len(initials)

    # 5. run the network
    for init_i, initial in enumerate(initials):
      traj_group = utils.Trajectory(model=self.model,
                                    size=1,
                                    target_vars=initial,
                                    fixed_vars=self.fixed_vars,
                                    pars_update=self.pars_update)

      #   5.2 run the model
      traj_group.run(duration=duration[init_i], report=False, )

      #   5.3 legend
      legend = f'$traj_{init_i}$: '
      for key in self.target_var_names:
        legend += f'{key}={initial[key]}, '
      legend = legend[:-2]

      #   5.4 trajectory
      start = int(plot_duration[init_i][0] / math.get_dt())
      end = int(plot_duration[init_i][1] / math.get_dt())

      #   5.5 visualization
      if axes == 'v-v':
        lines = plt.plot(traj_group.mon[self.x_var][start: end, 0],
                         traj_group.mon[self.y_var][start: end, 0],
                         label=legend)
        utils.add_arrow(lines[0])
      else:
        plt.plot(traj_group.mon.ts[start: end],
                 traj_group.mon[self.x_var][start: end, 0],
                 label=legend + f', {self.x_var}')
        plt.plot(traj_group.mon.ts[start: end],
                 traj_group.mon[self.y_var][start: end, 0],
                 label=legend + f', {self.y_var}')

    # 6. visualization
    if axes == 'v-v':
      plt.xlabel(self.x_var)
      plt.ylabel(self.y_var)
      scale = (self.lim_scale - 1.) / 2
      plt.xlim(*utils.rescale(self.target_vars[self.x_var], scale=scale))
      plt.ylim(*utils.rescale(self.target_vars[self.y_var], scale=scale))
      plt.legend()
    else:
      plt.legend(title='Initial values')

    if show:
      plt.show()

  def plot_limit_cycle_by_sim(self, initials, duration, tol=0.001, show=False):
    """Plot trajectories according to the settings.

    Parameters
    ----------
    initials : list, tuple
        The initial value setting of the targets.

        - It can be a tuple/list of floats to specify each value of dynamical variables
          (for example, ``(a, b)``).
        - It can also be a tuple/list of tuple to specify multiple initial values (for
          example, ``[(a1, b1), (a2, b2)]``).
    duration : int, float, tuple, list
        The running duration. Same with the ``duration`` in ``NeuGroup.run()``.

        - It can be a int/float (``t_end``) to specify the same running end time,
        - Or it can be a tuple/list of int/float (``(t_start, t_end)``) to specify
          the start and end simulation time.
        - Or, it can be a list of tuple (``[(t1_start, t1_end), (t2_start, t2_end)]``)
          to specify the specific start and end simulation time for each initial value.
    show : bool
        Whether show or not.
    """
    print('plot limit cycle ...')

    # 1. format the initial values
    if isinstance(initials, dict):
      initials = [initials]
    elif isinstance(initials, (list, tuple)):
      if isinstance(initials[0], (int, float)):
        initials = [{self.dvar_names[i]: v for i, v in enumerate(initials)}]
      elif isinstance(initials[0], dict):
        initials = initials
      elif isinstance(initials[0], (tuple, list)) and isinstance(initials[0][0], (int, float)):
        initials = [{self.dvar_names[i]: v for i, v in enumerate(init)} for init in initials]
      else:
        raise ValueError
    else:
      raise ValueError

    # 2. format the running duration
    if isinstance(duration, (int, float)):
      duration = [(0, duration) for _ in range(len(initials))]
    elif isinstance(duration[0], (int, float)):
      duration = [duration for _ in range(len(initials))]
    else:
      assert len(duration) == len(initials)

    # 5. run the network
    for init_i, initial in enumerate(initials):
      traj_group = utils.Trajectory(model=self.model,
                                    size=1,
                                    target_vars=initial,
                                    fixed_vars=self.fixed_vars,
                                    pars_update=self.pars_update)

      #   5.2 run the model
      traj_group.run(duration=duration[init_i], report=False, )
      x_data = traj_group.mon[self.x_var][:, 0]
      y_data = traj_group.mon[self.y_var][:, 0]
      max_index = utils.find_indexes_of_limit_cycle_max(x_data, tol=tol)
      if max_index[0] != -1:
        x_cycle = x_data[max_index[0]: max_index[1]]
        y_cycle = y_data[max_index[0]: max_index[1]]
        # 5.5 visualization
        lines = plt.plot(x_cycle, y_cycle, label='limit cycle')
        utils.add_arrow(lines[0])
      else:
        print(f'No limit cycle found for initial value {initial}')

    # 6. visualization
    plt.xlabel(self.x_var)
    plt.ylabel(self.y_var)
    scale = (self.lim_scale - 1.) / 2
    plt.xlim(*utils.rescale(self.target_vars[self.x_var], scale=scale))
    plt.ylim(*utils.rescale(self.target_vars[self.y_var], scale=scale))
    plt.legend()

    if show:
      plt.show()
