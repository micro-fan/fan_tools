import pytest
from fan_tools.unix import succ, ExecError


def test_succ_handle_error():
    stderr = []
    with pytest.raises(ExecError) as e:
        succ('bash randomcommand', stderr=stderr)
    assert stderr, 'Should have something: {}'.format(stderr)
    assert e.value.exit_code == 127, e.value
