import os
import sys
from decimal import Decimal, ROUND_HALF_UP


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


def usd_round(amount):
    return amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
