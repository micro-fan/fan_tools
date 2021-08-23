import itertools
import os
import sys
import warnings
import zipfile
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, BinaryIO, Dict, Iterable, List, Optional, Union


def execfile(fname: Union[str, Path], _globals: Dict[str, Any], _locals: Dict[str, Any]):
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


def rel_path(path: str, check=False, depth=1) -> Path:
    d = Path(sys._getframe(depth).f_code.co_filename).parent
    full = (d / path).resolve()
    if check and not full.exists():
        raise Exception('No such path: {!r}'.format(full))
    return full


def py_rel_path(*args, **kwargs):
    message = 'Use `rel_path` function instead'
    warnings.warn(message, DeprecationWarning, stacklevel=2)
    return rel_path(*args, depth=2, **kwargs)


def auto_directory(path: Union[str, Path]) -> Path:
    """
    if you're using py.path you make do that as:
    py.path.local(full_path).ensure_dir()
    """
    if isinstance(path, str):
        dir_path = rel_path(path)
    else:
        dir_path = path
    dir_path.mkdir(exist_ok=True)
    return dir_path


def usd_round(amount: Union[str, Decimal]) -> Decimal:
    if isinstance(amount, str):
        amount = Decimal(amount)
    return amount.quantize(Decimal('.01'), rounding=ROUND_HALF_UP)


def root_directory(target: Union[Path, BinaryIO], exclude: Optional[List[str]] = None) -> Path:
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


def dict_contains(superset: Dict[Any, Any], subset: Dict[Any, Any]) -> bool:
    """
    partial comparison dictionaries

    $ dict_contains({'a': 1, 'b': 2}, {'a': 1}) # => True
    $ dict_contains({'a': 1, 'b': 2}, {'b': 1}) # => True
    $ dict_contains({'a': 1, 'b': 2}, {'c': 3}) # => False
    $ dict_contains({'a': 1, 'b': 2}, {'b': 2}) # => False
    """

    for k, v in subset.items():
        if k not in superset:
            return False
        if isinstance(v, dict):
            if not dict_contains(superset[k], subset[k]):
                return False
        else:
            if v != superset[k]:
                return False
    return True


def slide(iterable: Iterable[Any], size=2) -> Iterable[Any]:
    return itertools.zip_longest(*[itertools.islice(iterable, i, sys.maxsize) for i in range(size)])


def expand_dot(pattern: Dict[str, Any]) -> Dict[str, Any]:
    """
    {'a.b.c': 1} => {'a':{'b':{'c': 1}}}
    """
    out = {}
    for k, v in pattern.items():
        if '.' in k:
            curr = out
            for sub_k, has_next in slide(k.split('.')):
                if has_next:
                    curr = curr.setdefault(sub_k, {})
                else:
                    curr[sub_k] = v
        else:
            out[k] = v
    return out
