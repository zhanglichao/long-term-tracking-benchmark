from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import functools
import json
import numpy as np
import os
import pickle
import sys


def str2bool(x):
    x = x.strip().lower()
    if x in ['t', 'true', 'y', 'yes', '1']:
        return True
    if x in ['f', 'false', 'n', 'no', '0']:
        return False
    raise ValueError('warning: unclear value: {}'.format(x))


def str2bool_or_none(x):
    try:
        return str2bool(x)
    except ValueError:
        return None


def bool2str(x):
    return str(x).lower()


def default_if_none(x, value):
    return value if x is None else x


def harmonic_mean(*args):
    assert all([x >= 0 for x in args])
    if any([x == 0 for x in args]):
        return 0.
    return np.asscalar(1. / np.mean(1. / np.asfarray(args)))


def geometric_mean(*args):
    assert all([x >= 0 for x in args])
    if any([x == 0 for x in args]):
        return 0.
    return np.asscalar(np.exp(np.mean(np.log(args))))


def cache(protocol, filename, func, makedir=True, ignore_existing=False, verbose=False):
    '''Caches the result of a function in a file.

    Args:
        func -- Function with no arguments.
        makedir -- Create parent directory if it does not exist.
        ignore_existing -- Ignore existing cache file and call function.
            If it existed, the old cache file will be over-written.
    '''
    if (not ignore_existing) and os.path.exists(filename):
        if verbose:
            print('load from cache: {}'.format(filename), file=sys.stderr)
        with open(filename, 'r') as r:
            result = protocol.load(r)
    else:
        dir = os.path.dirname(filename)
        if makedir and (not os.path.exists(dir)):
            os.makedirs(dir)
        result = func()
        # Write to a temporary file and then perform atomic rename.
        # This guards against partial cache files.
        tmp = filename + '.tmp'
        with open(tmp, 'w') as w:
            protocol.dump(result, w)
        os.rename(tmp, filename)
    return result


cache_json = functools.partial(cache, json)
cache_pickle = functools.partial(cache, pickle)


def dict_sum(xs, initializer=None):
    if initializer is None:
        total = {}
    else:
        total = dict(initializer)
    for x in xs:
        for k, v in x.items():
            if k in total:
                total[k] += v
            else:
                total[k] = v
    return total


def dict_sum_strict(xs, initializer):
    total = dict(initializer)
    for x in xs:
        for k in initializer.keys():
            total[k] += x[k]
    return total


def map_dict(f, x):
    return {k: f(v) for k, v in x.items()}


class SparseTimeSeries(object):
    '''Dictionary with integer keys in sorted order.'''

    def __init__(self, frames=None):
        self._frames = {} if frames is None else dict(frames)

    def __len__(self):
        return len(self._frames)

    def __getitem__(self, t):
        return self._frames[t]

    def __setitem__(self, t, value):
        self._frames[t] = value

    def __delitem__(self, t):
        del self._frames[t]

    def get(self, t, default):
        return self._frames.get(t, default)

    def setdefault(self, t, default):
        return self._frames.setdefault(t, default)

    def keys(self):
        return self._frames.keys()

    def sorted_keys(self):
        '''Returns times in sequential order.'''
        return sorted(self._frames.keys())

    def values(self):
        return self._frames.values()

    def sorted_items(self):
        '''Returns (time, value) pairs in sequential order.'''
        times = sorted(self._frames.keys())
        return zip(times, [self._frames[t] for t in times])

    def items(self):
        return self._frames.items()

    def __iter__(self):
        for t in sorted(self._frames.keys()):
            yield t

    def __contains__(self, t):
        return t in self._frames


def select_interval(series, min_time=None, max_time=None, init_time=0):
    return SparseTimeSeries({
        t: x for t, x in series.items()
        if ((min_time is None or min_time <= t - init_time) and
            (max_time is None or t - init_time <= max_time))})
