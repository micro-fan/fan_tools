from fan_tools.python import rel_path, py_rel_path


def test_01_rel_path():
    rel_path('./test_rel_path.py', check=True)
    rel_path('../setup.py', check=True)


def test_02_py_rel_path():
    py_rel_path('./test_rel_path.py', check=True)
    py_rel_path('../setup.py', check=True)
