import asyncio

import pytest
from fan_tools.unix import asucc, ExecError



async def test_asucc(event_loop):
    ret, out, err = await asucc(
        'echo 1; echo 2 >&2; echo 3 >&2; echo 4; sleep 1', check_stderr=False
    )
    assert ret == 0
    assert out == ['1', '4']
    assert err == ['2', '3']

    # Test for out not reused from prev run
    ret, out, err = await asucc(
        'echo 1; echo 2 >&2; echo 3 >&2; echo 4; sleep 1', check_stderr=False
    )
    assert ret == 0
    assert out == ['1', '4']
    assert err == ['2', '3']


async def test_asucc_handle_error(event_loop):
    stderr = []
    with pytest.raises(ExecError) as e:
        await asucc('bash randomcommand', stderr=stderr)
    assert stderr, 'Should have something: {}'.format(stderr)
    assert e.value.exit_code == 127, e.value


async def run_sleep(loop):
    return await asucc('sleep 10000', loop=loop)


@pytest.mark.asyncio
async def test_asucc_kill(event_loop):
    asucc_wait = asyncio.ensure_future(run_sleep(event_loop))
    await asyncio.sleep(0.01)
    asucc_wait.cancel()
    await asyncio.sleep(0.01)
    with pytest.raises(asyncio.CancelledError):
        await asucc_wait
