import cProfile
import gc
import subprocess
from collections import defaultdict
from contextlib import contextmanager


class Profiler(cProfile.Profile):
    """
    This profiler is not intended to be used in test or production code
    Requirements: `$ pip install pyprof2calltree`
    Usage:
    >>> with Profiler.instance().profile("profile_name"):
    ...     some_code_to_profile()
    This code will generate `profile_name_1.callgrind` file. Counter increases each time profile
     called with the same name. To view these files use kcachegrind.
    """

    _instance = None

    def __init__(self, *args, **kwargs):
        self._calls = defaultdict(lambda: 0)
        if 'builtins' not in kwargs:
            kwargs['builtins'] = False
        super().__init__(*args, **kwargs)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _f_name(self, f_name):
        self._calls[f_name] += 1
        return "{}_{}.prof".format(f_name, self._calls[f_name])

    @contextmanager
    def profile(self, f_name):
        gc.disable()
        self.enable()
        try:
            yield
        finally:
            self.disable()
            gc.enable()
        self.dump_stats(self._f_name(f_name))
        self.clear()

    def __del__(self):
        for f_name, counter in self._calls.items():
            for i in range(1, counter + 1):
                name = "{}_{}".format(f_name, i)
                cmd = "pyprof2calltree -i {name}.prof -o {name}.calltree".format(name=name)
                subprocess.run(cmd, shell=True, executable='/bin/bash')
