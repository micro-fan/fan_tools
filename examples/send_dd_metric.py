#!/usr/bin/env python3
"""
# set DD_KEY, get from https://app.datadoghq.com/organization-settings/api-keys
export DD_KEY=use_your_key_here

# Run vector container
docker run --rm -v $(pwd)/examples/send_dd_metric.toml:/etc/vector/vector.toml -e DD_KEY=$DD_KEY -p 9998:9998/udp timberio/vector:0.14.X-debian
"""
import argparse
import logging

from fan_tools.metrics import send_error_metric, send_metric
from fan_tools.otel.log import enable_otel_logger


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
log = logging.getLogger('send_dd_metric')


def parse_args():
    parser = argparse.ArgumentParser(description='DESCRIPTION')
    # parser.add_argument('-m', '--mode', default='auto', choices=['auto', 'manual'])
    # parser.add_argument('-l', '--ll', dest='ll', action='store_true', help='help')
    return parser.parse_args()


def main():
    args = parse_args()
    enable_otel_logger(vector_info=('localhost', 9998))

    send_metric('test', tags={'service': '1'})
    # send_error_metric('test_error')
    # send_error_metric('test_error2')


if __name__ == '__main__':
    main()
