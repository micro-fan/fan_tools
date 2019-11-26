import asyncio
import logging
import os
import re
import socket
import subprocess
import time
from asyncio.subprocess import PIPE
from collections import ChainMap
from contextlib import closing, contextmanager, suppress

log = logging.getLogger('fan_tools.unix')


class ExecError(Exception):
    def __init__(self, exit_code, cmd, stdout, stderr):
        self.exit_code = exit_code
        self.cmd = cmd
        self.stdout = stdout
        self.stderr = stderr
        super().__init__()

    def __str__(self):
        return f'Return: {self.exit_code} Command: {self.cmd}\nStderr: {self.stderr}'

    def __repr__(self):
        desc = str(self).replace('\n', '\t')
        return f'<ExecException `{desc}`>'


def _prepare(out):
    out = out.decode('utf8').strip('\n').split('\n')
    if out == ['']:
        return []
    return out


def run(command):
    '''
    Run command in shell, accepts command construction from list
    Return (return_code, stdout, stderr)
    stdout and stderr - as list of strings
    '''
    if isinstance(command, list):
        command = ' '.join(command)
    out = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return (out.returncode, _prepare(out.stdout), _prepare(out.stderr))


def succ(cmd, check_stderr=False, stdout=None, stderr=None):
    '''
    Alias to run with check return code and stderr
    '''
    code, out, err = run(cmd)

    # Because we're raising error, sometimes we want to process stdout/stderr after catching error
    # so we're copying these outputs if required
    if stdout is not None:
        stdout[:] = out
    if stderr is not None:
        stderr[:] = err

    if code != 0:
        for l in out:
            print(l)
    if code != 0:
        raise ExecError(code, cmd, out, err)
    if check_stderr and err != []:
        raise ExecError(code, cmd, out, err)
    return code, out, err


async def process_pipe(out, pipe, proc, log_fun):
    while True:
        line = await pipe.readline()
        line = line.decode('utf8').strip('\n')
        if line:
            out.append(line)
            log_fun(line)
        if not line and proc.returncode is not None:
            return
        await asyncio.sleep(0)


async def asucc(
    cmd, check_stderr=False, pid_future=None, with_log=True, stdout=None, stderr=None, loop=None
):
    proc = await asyncio.create_subprocess_shell(
        cmd, stdin=PIPE, stderr=PIPE, stdout=PIPE, loop=loop
    )
    if pid_future and not pid_future.done():
        pid_future.set_result(proc.pid)

    # see succ comments for these values
    out = stdout if stdout is not None else []
    err = stderr if stderr is not None else []

    if with_log:
        log_warning = log.warning
        log_debug = log.debug
    else:
        skip = lambda x: x
        log_warning, log_debug = skip, skip

    asyncio.ensure_future(process_pipe(err, proc.stderr, proc, log_warning), loop=loop)
    asyncio.ensure_future(process_pipe(out, proc.stdout, proc, log_debug), loop=loop)

    try:
        code = await proc.wait()
        if code != 0:
            raise ExecError(code, cmd, out, err)
        if check_stderr and err != []:
            raise ExecError(code, cmd, out, err)
        return code, out, err
    except asyncio.CancelledError as e:
        if not proc.returncode:
            log.exception('Going to kill process: [{}] {}. Children first'.format(proc.pid, cmd))
            await asucc('pkill -9 -P {} || true'.format(proc.pid))
            with suppress(ProcessLookupError):
                proc.terminate()
            await asyncio.sleep(0.1)
            if not proc.returncode:
                with suppress(ProcessLookupError):
                    proc.kill()
        raise e


def check_socket(host, port):
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.settimeout(10)
        try:
            conn_ex = sock.connect_ex((host, port))
            if conn_ex == 0:
                return True
            return False
        except:
            return False


def wait_result(func, result, timeout):
    t = time.time()
    while True:
        res = func()
        if result is None and res is None:
            return True
        elif res == result:
            return True
        time.sleep(1)
        if (time.time() - t) > timeout:
            return False


def wait_socket(host, port, timeout=120):
    '''
    Wait for socket opened on remote side. Return False after timeout
    '''
    return wait_result(lambda: check_socket(host, port), True, timeout)


def wait_no_socket(host, port, timeout=120):
    return wait_result(lambda: check_socket(host, port), False, timeout)


def interpolate_sysenv(line, defaults={}):
    '''
    Format line system environment variables + defaults
    '''
    map = ChainMap(os.environ, defaults)
    return line.format(**map)


def source(fname):
    '''
    Acts similar to bash 'source' or '.' commands.
    '''
    rex = re.compile('(?:export |declare -x )?(.*?)="(.*?)"')
    out = call_out('source {} && export'.format(fname))
    out = [x for x in out if 'export' in x or 'declare' in x]
    out = {k: v for k, v in [rex.match(x).groups() for x in out if rex.match(x)]}
    for k, v in out.items():
        os.environ[k] = v


@contextmanager
def cd(dir_name):
    """
    do something in other directory and return back after block ended
    """
    old_path = os.path.abspath('.')
    os.chdir(dir_name)
    try:
        yield
        os.chdir(old_path)
    except Exception:
        os.chdir(old_path)
        raise
