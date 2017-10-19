#!/usr/bin/python3
import argparse
import logging
import os
import time

from tipsi_tools.unix import run


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('run_filebeat')

parser = argparse.ArgumentParser(description='run filebeat')
parser.add_argument('-e', '--env', dest='env', action='append', default=[],
                    help='env vars to check: -e HOST_TYPE=amazon')
parser.add_argument(nargs='?', dest='yaml_template',
                    default='./ext_configs/filebeat/config.yaml')
args = parser.parse_args()


def environment_ok():
    required_env = dict([x.split('=') for x in args.env])
    for key, value in required_env.items():
        log.info('Check: {} {}'.format(key, value))
        env_value = os.environ.get(key, None)
        if env_value != value:
            log.info('Environment is not ok: {} => {} != {} '.format(key, value, env_value))
            return False
    return True


def main():
    if not environment_ok():
        while 1:
            time.sleep(9**10)
    if not os.path.exists(args.yaml_template):
        log.exception('Cannot find file: {}'.format(args.yaml_template))
        exit(1)
    run('tipsi_env_yaml {} /tmp/filebeat.yml'.format(args.yaml_template))
    log.info('Start filebeat')
    out = run('/usr/bin/filebeat -e -c /tmp/filebeat.yml')  # NOQA
    log.exception('Filebeat exited: {}'.format(out))

if __name__ == '__main__':
    main()
