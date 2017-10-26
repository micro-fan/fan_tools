import pytest
from tipsi_tools.testing.aio import AIOTestCase
from tipsi_tools.unix import asucc


class AsyncCase(AIOTestCase):
    async def setUp(self):
        self.setup = True

    async def test_simple(self):
        assert self.setup

    async def division(self):
        1 / 0

    async def test_assertraise(self):
        await self.assertRaises(ZeroDivisionError, self.division)

    def tearDown(self):
        assert self.setup


@pytest.mark.asyncio
async def test_asucc():
    ret, out, err = await asucc('echo 1; echo 2 >&2; echo 3 >&2; echo 4; sleep 1', check_stderr=False)
    assert ret == 0
    assert out == ['1', '4']
    assert err == ['2', '3']
