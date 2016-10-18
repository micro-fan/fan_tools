from tipsi_tools.testing.aio import AIOTestCase


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
