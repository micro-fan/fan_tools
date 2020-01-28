from google.cloud import storage

from fan_tools.backup import BackupMonitoring


class GCloud(BackupMonitoring):
    def __init__(self, *args, bucket_name=None, prefix='backup/', **kwargs):
        # from google.cloud import storage
        super().__init__(*args, **kwargs)
        assert bucket_name, 'You should define bucket-name'
        self.prefix = prefix
        self.cli = storage.Client()
        self.bucket = self.cli.get_bucket(bucket_name)

    def get_backups_list(self):
        items = list(self.bucket.list_blobs(prefix=self.prefix))
        return [s.name.replace(self.prefix, '') for s in items]

    def perform_upload(self, src_name, dst_name):
        self.log.debug('Upload {src_name} => {dst_name}')
        blob = self.bucket.blob(dst_name)
        blob.upload_from_filename(src_name)
