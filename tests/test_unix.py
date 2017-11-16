import pytest
from tipsi_tools.unix import succ


def test_succ_handle_error():
    stderr = []
    with pytest.raises(AssertionError):
        succ('bash randomcommand', stderr=stderr)
    assert stderr, 'Should have something: {}'.format(stderr)
