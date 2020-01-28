import os
import asyncio
import datetime
import logging

from fan_tools.unix import asucc


class BackupMonitoring:
    log = logging.getLogger('BackupMonitoring')
    LOOP = 24 * 60 * 60
    RETRY_TIMEOUT = 5 * 60
    NAME_PATTERN = '%Y%m%d_%H%M.gz'

    def __init__(self, prefix, metric_name, backup_command, enabled=True):
        self.prefix = prefix
        self.metric_name = metric_name
        self.backup_command = backup_command
        self.enabled = enabled
        self.last = datetime.datetime.min

    async def run_monitoring(self, update_metrics):
        self.update_metrics = update_metrics
        while True:
            try:
                self.set_latest_timestamp()
                break
            except Exception:
                self.log.exception('Cannot get latest backup. Sleep 5 seconds')
                await asyncio.sleep(5)

        while True:
            try:
                wait_seconds = (self.last - datetime.datetime.utcnow()).total_seconds() + self.LOOP
                if wait_seconds <= 0:
                    await self.perform_backup()
                    self.set_latest_timestamp()
                    self.log.debug(f'Sleep after backup for: {self.LOOP}')
                    await asyncio.sleep(self.LOOP)
                else:
                    self.log.debug(f'Sleep without backup for: {wait_seconds}. Last: {self.last}')
                    await asyncio.sleep(wait_seconds)
            except Exception:
                self.log.exception(f'During perform_backup call. Sleep for {self.RETRY_TIMEOUT}')
                await asyncio.sleep(self.RETRY_TIMEOUT)

    def set_latest_timestamp(self):
        flist = self.get_backups_list()
        if len(flist) == 0:
            return
        dates = sorted([datetime.datetime.strptime(f, self.NAME_PATTERN) for f in flist])
        self.last = dates[-1]
        self.call_update()

    def call_update(self):
        if self.last > datetime.datetime.min:
            self.update_metrics({self.metric_name: self.last.timestamp()})

    def get_backups_list(self):
        raise NotImplementedError

    async def perform_upload(self, src_name, dst_name):
        raise NotImplementedError

    async def perform_backup(self, skip_upload=False):
        if not self.enabled:
            self.log.debug('Backups disabled. Skip action. To enable set ENABLE_BACKUP=true')
            return

        code, out, err = await asucc(self.backup_command)
        self.log.debug(f'Response: {code} => {out} Err: {err}')
        assert code == 0, code
        fname = out[0].strip()
        src_name = f'/dumps/{fname}'
        dst_name = os.path.join(self.prefix, fname)

        if skip_upload:
            return

        self.perform_upload(src_name, dst_name)
