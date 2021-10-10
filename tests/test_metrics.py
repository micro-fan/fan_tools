import logging

from fan_tools.metrics import send_error_metric, send_metric


def test_01_metric(caplog):
    tags = {'ttt': 'mmm', 'env': 'prod', 'service': 'cool'}
    with caplog.at_level(logging.INFO, logger='fan.metric'):
        send_metric('meme', tags=tags)
        send_metric('meme2')
    assert len(caplog.records) == 2
    l1 = caplog.records[0]
    assert l1.msg['tags'] == tags
    assert l1.msg['message'] == 'meme'
    l2 = caplog.records[1]
    assert l2.msg['tags'] == {'env': 'not_set', 'service': 'not_set'}


def test_02_error_metric(caplog):
    tags = {'ttt': 'mmm', 'env': 'prod', 'service': 'cool', 'error_type': 'lol'}

    with caplog.at_level(logging.ERROR, logger='fan.metric'):
        send_error_metric('meme', tags=tags)
    assert len(caplog.records) == 1
    l1 = caplog.records[0]
    tags_target = {**tags, 'error_type': 'meme'}
    assert l1.msg['tags'] == tags_target
