import os
import sys
import zipfile
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import BinaryIO, List, Union


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


def rel_path(path, check=False, depth=1):
    d = os.path.dirname(sys._getframe(depth).f_code.co_filename)
    full = os.path.abspath(os.path.join(d, path))
    if check and not os.path.exists(full):
        raise Exception('No such path: {!r}'.format(full))
    return full


def py_rel_path(*args, **kwargs):
    return Path(rel_path(*args, depth=2, **kwargs))


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
    if isinstance(amount, str):
        amount = Decimal(amount)
    return amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def root_directory(target: Union[Path, BinaryIO], exclude: List[str] = None) -> Path:
    """Returns the folder that contains the files."""
    exclude = exclude or []
    if isinstance(target, Path):
        files = [f for f in target.glob('**/*') if f.is_file()]
    elif hasattr(target, 'read'):
        with zipfile.ZipFile(target, 'r') as zip_ref:
            files = [
                Path(zip_item.filename) for zip_item in zip_ref.infolist() if not zip_item.is_dir()
            ]
    else:
        raise Exception('Unsupported target object')
    paths = [f for f in files if not any(filter(lambda i: i in str(f), exclude))]
    if len(paths) > 1:
        prefix = os.path.commonpath(paths)
        prefix = '' if prefix == '/' else prefix
        root = Path(prefix)
    elif paths:
        root = paths[0].parent
    else:
        root = Path('')
    return root
