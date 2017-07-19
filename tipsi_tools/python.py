import os


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
