from unittest import mock

import pytest
from asgi_lifespan import LifespanManager

from fan_tools.backup import BackupMonitoring
from fan_tools.backup.utils import get_app, run_main


BS = None


class TestBackup(BackupMonitoring):
    def __init__(self, *args, **kwargs):
        kwargs.pop('bucket_name')
        super().__init__(*args, **kwargs)
        self.monitoring = False
        global BS
        BS = self

    def get_backups_list(self):
        return []

    def perform_upload(self, src_name, dst_name):
        pass

    def run_monitoring(self):
        self.monitoring = True


APP = None


@pytest.fixture
def mock_env(monkeypatch):
    mp = monkeypatch
    mp.setenv('BACKUP_COMMAND', 'sleep 0')

    def _set_app(app, *args, **kwargs):
        print(f'SIDEE: {app=} {args=} {kwargs=}')
        global APP
        APP = app

    with mock.patch('uvicorn.run', side_effect=_set_app):
        yield


@pytest.mark.asyncio
async def test_01_general(mock_env):
    fake_args = mock.MagicMock()
    fake_args.daemonize = True
    fake_args.bucket = 'test_bucket'
    assert not APP
    run_main(TestBackup, args=fake_args)
    assert BS
    assert not BS.monitoring
    async with LifespanManager(APP):
        assert BS.monitoring
