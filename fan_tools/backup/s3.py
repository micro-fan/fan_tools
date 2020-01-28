import logging
import sys
from py.path import local

import boto3

from fan_tools.backup import BackupMonitoring
from fan_tools.backup.utils import run_main


class S3Backup(BackupMonitoring):
    def __init__(self, bucket_name=None, **kwargs):
        # from google.cloud import storage
        super().__init__(**kwargs)
        assert bucket_name, 'You should define bucket-name'
        self.cli = boto3.resource('s3')
        self.bucket = self.cli.Bucket(bucket_name)

    def get_backups_list(self):
        items = list(self.bucket.objects.filter(Prefix=self.prefix))
        return [local(s.key).basename for s in items]

    def perform_upload(self, src_name, dst_name):
        self.log.debug('Upload {src_name} => {dst_name}')
        self.bucket.upload_file(src_name, dst_name)


def main():
    """
    Example setup for s3.

    BACKUP_COMMAND='touch /dumps/aaa; echo aaa' ENABLE_BACKUP=true fan_s3_backup
    """
    import os
    from fan_tools.fan_logging import setup_logger

    setup_logger('backup_monitoring', enable_stdout=True)

    os.environ['AWS_ACCESS_KEY_ID'] = os.environ['AWS_BACKUP_KEY']
    os.environ['AWS_SECRET_ACCESS_KEY'] = os.environ['AWS_BACKUP_SECRET']

    run_main(S3Backup, environ_defaults={'bucket': 'AWS_BACKUP_BUCKET'})


if __name__ == '__main__':
    main()
