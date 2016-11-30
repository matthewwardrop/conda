# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import os
from functools import reduce
from logging import getLogger
from os.path import basename, dirname, join, splitext

from ..utils import on_win

try:
    from cytoolz.itertoolz import accumulate, concat
except ImportError:
    from .._vendor.toolz.itertoolz import accumulate, concat


log = getLogger(__name__)


def tokenized_startswith(test_iterable, startswith_iterable):
    return all(t == sw for t, sw in zip(test_iterable, startswith_iterable))


def get_all_directories(files):
    directories = sorted(set(tuple(f.split('/')[:-1]) for f in files))
    return directories or ()


def get_leaf_directories(files):
    # type: (List[str]) -> List[str]
    # give this function a list of files, and it will hand back a list of leaf directories to
    #   pass to os.makedirs()
    directories = get_all_directories(files)
    leaves = []

    def _process(x, y):
        if not tokenized_startswith(y, x):
            leaves.append(x)
        return y
    last = reduce(_process, directories)

    if not leaves:
        leaves.append(directories[-1])
    elif not tokenized_startswith(last, leaves[-1]):
        leaves.append(last)

    return tuple('/'.join(leaf) for leaf in leaves)


def explode_directories(child_directories):
    # get all directories including parents
    return set(concat(accumulate(join, directory.split('/')) for directory in child_directories))


def pyc_path(path, python_major_minor_version):
    pyver_string = python_major_minor_version.replace('.', '')
    if pyver_string.startswith('2'):
        return path + 'c'
    else:
        py_file = basename(path)
        basename_root, extension = splitext(py_file)
        pyc_file = "__pycache__/%s.cpython-%s.%sc" % (basename_root, pyver_string, extension)
        return path.rreplace(py_file, pyc_file, 1)


def missing_pyc_files(python_major_minor_version, files):
    # returns a tuple of tuples, with the inner tuple being the .py file and the missing .pyc file
    py_files = (f for f in files if f.endswith('.py'))
    pyc_matches = ((py_file, pyc_path(py_file, python_major_minor_version)) for py_file in py_files)
    result = tuple(match for match in pyc_matches if match[1] not in files)
    return result


def parse_entry_point_def(ep_definition):
    cmd_mod, func = ep_definition.rsplit(':', 1)
    command, module = cmd_mod.rsplit("=", 1)
    command, module, func = command.strip(), module.strip(), func.strip()
    return command, module, func


def get_python_path(version=None):
    if on_win:
        return "python.exe"
    if version and '.' not in version:
        version = '.'.join(version)
    return join("bin", "python%s" % version or '')


def get_bin_directory_short_path():
    return 'Scripts' if on_win else 'bin'


def win_path_ok(path):
    return path.replace('/', '\\') if on_win else path


def win_path_double_escape(path):
    return path.replace('\\', '\\\\') if on_win else path


def win_path_backout(path):
    return path.replace('\\', '/') if on_win else path


def maybe_right_pad(path):
    return path if path.endswith(os.sep) else path + os.sep
