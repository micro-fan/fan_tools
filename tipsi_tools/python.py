import os
import sys
from decimal import ROUND_HALF_UP, Decimal


def execfile(fname, _globals, _locals):
    """
    Usage: execfile('path/to/file.py', globals(), locals())
    """
    if os.path.exists(fname):
        with open(fname) as f:
            code = compile(f.read(), os.path.basename(fname), 'exec')
            exec(code, _globals, _locals)
            return True
    else:
        return False


def rel_path(path, check=True, depth=1):
    d = os.path.dirname(sys._getframe(depth).f_code.co_filename)
    full = os.path.abspath(os.path.join(d, path))
    if check and not os.path.exists(full):
        raise Exception('No such path: {!r}'.format(full))
    return full


def auto_directory(rel_name):
    """
    if you're using py.path you make do that as:
    py.path.local(full_path).ensure_dir()
    """
    dir_name = rel_path(rel_name, check=False)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name, exist_ok=True)
    return dir_name


def usd_round(amount):
    return amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
