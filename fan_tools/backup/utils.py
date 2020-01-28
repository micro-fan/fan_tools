#!/usr/bin/env python3
"""
Internal helpers for backup tools
"""
import argparse
import asyncio
import logging
import os

from fan_tools.mon_server import MetricsServer

log = logging.getLogger('fan_tools.backup.utils')


def get_backup_server(args, BackupServer):
    enabled = True
    if not args.enabled:
        enabled = False
        backup_command = ''
    else:
        backup_command = os.environ.get('BACKUP_COMMAND')
        if not backup_command:
            BACKUP_DB_CONTAINER = os.environ.get('BACKUP_DB_CONTAINER')
            assert BACKUP_DB_CONTAINER, 'BACKUP_DB_CONTAINER variable must be specified'
            BACKUP_SCRIPT = os.environ.get('BACKUP_DB_SCRIPT', '/create_backup.py')
            backup_command = f'docker exec -i {BACKUP_DB_CONTAINER} {BACKUP_SCRIPT}'

    return BackupServer(
        prefix=args.prefix,
        metric_name=args.metric_name,
        bucket_name=args.bucket,
        backup_command=backup_command,
        enabled=enabled,
    )


def parse_args(environ_defaults={}):
    parser = argparse.ArgumentParser(description='DESCRIPTION')
    parser.add_argument('-m', '--monitoring-group', default='backups')
    parser.add_argument('-b', '--bucket')
    parser.add_argument('-d', '--daemonize', action='store_true', help='daemonize')
    parser.add_argument('-p', '--prefix', default=os.environ.get('BACKUP_PREFIX', 'backups/'))
    parser.add_argument(
        '--enabled',
        action='store_true',
        default=os.environ.get('ENABLE_BACKUP', 'false').lower() != 'false',
    )
    parser.add_argument('--metric-name', default='backup_metric')
    parser.add_argument(
        '--skip-upload', action='store_true', help='Works only in non-daemonized execution'
    )
    # parser.add_argument('-m', '--mode', default='auto', choices=['auto', 'manual'])
    # parser.add_argument('-l', '--ll', dest='ll', action='store_true', help='help')
    defaults = {}
    for k, v in environ_defaults.items():
        if isinstance(v, list):
            name, default = v
            defaults[k] = os.environ.get(name, default)
        else:
            defaults[k] = os.environ.get(v)
    parser.set_defaults(**defaults)
    return parser.parse_args()


def run_main(backup_server, environ_defaults={}):
    args = parse_args(environ_defaults)
    backup_server = get_backup_server(args, backup_server)
    if args.daemonize:
        from sanic import Sanic

        app = Sanic()
        mserver = MetricsServer(app, args.monitoring_group)
        mserver.add_task(backup_server.run_monitoring)
        app.run(host='0.0.0.0', port=os.environ.get('MONITORING_PORT', 80))
    else:
        asyncio.run(backup_server.perform_backup(skip_upload=args.skip_upload))
