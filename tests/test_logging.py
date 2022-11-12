import logging
from unittest.mock import MagicMock

from fan_tools.fan_logging import setup_logger


def test_01_js_formatter(tmp_path):
    mm = MagicMock()
    setup_logger('in_test', root_dir=tmp_path, json_params={'get_context': mm})
    mm.assert_not_called()
    logging.debug('test')
    mm.assert_called_once()
