from pathlib import Path

import pytest

from fan_tools.python import auto_directory, py_rel_path, rel_path
from fan_tools.unix import cd


def test_01_rel_path():
    rel_path('./test_rel_path.py', check=True)
    rel_path('../pyproject.toml', check=True)


def test_02_py_rel_path_deprecated():
    with pytest.deprecated_call():
        py_rel_path('./test_rel_path.py', check=True)
        py_rel_path('../pyproject.toml', check=True)


def test_03_auto_directory(tmpdir):
    with cd(tmpdir):
        auto_directory('./dir_from_string')

    assert (tmpdir / 'dir_from_string').exists

    pth = Path(tmpdir / 'dir_from_path')
    assert not pth.exists(), (pth, tmpdir)
    auto_directory(pth)
    assert pth.exists()
