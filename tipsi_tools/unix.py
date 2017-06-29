import os
import socket
import subprocess
import time
import re
from contextlib import closing
from collections import ChainMap


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


def succ(cmd, check_stderr=True):
    '''
    Alias to run with check return code and stderr
    '''
    code, out, err = run(cmd)
    if code != 0:
        for l in out:
            print(l)
    assert code == 0, 'Return: {} {}\nStderr: {}'.format(code, cmd, err)
    if check_stderr:
        assert err == [], 'Error: {} {}'.format(err, code)
    return code, out, err


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
    Act's similar to bash 'source' or '.' commands.
    '''
    rex = re.compile('(?:export |declare -x )?(.*?)="(.*?)"')
    out = call_out('source {} && export'.format(fname))
    out = [x for x in out if 'export' in x or 'declare' in x]
    out = {k:v for k, v in [rex.match(x).groups() for x in out if rex.match(x)]}
    for k, v in out.items():
        os.environ[k] = v
