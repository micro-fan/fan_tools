import asyncio
from functools import wraps
from unittest import TestCase
from unittest.case import _Outcome


class AIOMask(type):
    '''
    Sometimes test runners check test methods with
    `inspect.iscoroutine` and async functions will return `true`
    so we need to mask these methods by wrapping them into
    callable function, but this require to call such function twice
    You can find this below in:
    `await self.ensure_future(testMethod()())`
    '''
    def wrap_func(func):
        @wraps(func)
        def ret(*args, **kwargs):
            def inner():
                return func(*args, **kwargs)
            return inner
        return ret

    def __new__(cls, name, bases, dct):
        for k, v in dct.items():
            if k.startswith('test'):
                dct[k] = cls.wrap_func(v)
        return super().__new__(cls, name, bases, dct)


class AIOTestCase(TestCase, metaclass=AIOMask):
    '''
    Basically this was just copy-paste from native python test case implementation
    with some changes to test async/await methods.
    It require AIOMask metaclass to deal with some test runners like `nose2` and etc,
    you can read about this in AIOMask docstring
    We provide async support for `setUp`, `tearDown` and test methods, also support async
    functions in `assertRaises`
    '''
    def run(self, result=None):
        self.loop = asyncio.get_event_loop()
        out = self.inner_run(result)
        f = asyncio.ensure_future(out)
        self.loop.run_until_complete(f)
        return f.result()

    async def assertRaises(self, CatchException, callable, *args, **kwargs):
        try:
            await self.ensure_future(callable(*args, **kwargs))
        except CatchException:
            pass

    def ensure_future(self, result):
        try:
            return asyncio.ensure_future(result)
        except TypeError:
            f = asyncio.Future()
            f.set_result(result)
            return f

    async def inner_run(self, result=None):
        orig_result = result
        if result is None:
            result = self.defaultTestResult()
            startTestRun = getattr(result, 'startTestRun', None)
            if startTestRun is not None:
                startTestRun()

        result.startTest(self)

        testMethod = getattr(self, self._testMethodName)
        if (getattr(self.__class__, "__unittest_skip__", False) or
           getattr(testMethod, "__unittest_skip__", False)):
            # If the class or method was skipped.
            try:
                skip_why = (getattr(self.__class__, '__unittest_skip_why__', '')
                            or getattr(testMethod, '__unittest_skip_why__', ''))
                self._addSkip(result, self, skip_why)
            finally:
                result.stopTest(self)
            return
        expecting_failure_method = getattr(testMethod,
                                           "__unittest_expecting_failure__", False)
        expecting_failure_class = getattr(self,
                                          "__unittest_expecting_failure__", False)
        expecting_failure = expecting_failure_class or expecting_failure_method
        outcome = _Outcome(result)
        try:
            self._outcome = outcome

            with outcome.testPartExecutor(self):
                await self.ensure_future(self.setUp())
            if outcome.success:
                outcome.expecting_failure = expecting_failure
                with outcome.testPartExecutor(self, isTest=True):
                    # wrapped into function to prevent generator check return true
                    await self.ensure_future(testMethod()())
                outcome.expecting_failure = False
                with outcome.testPartExecutor(self):
                    await self.ensure_future(self.tearDown())

            self.doCleanups()
            for test, reason in outcome.skipped:
                self._addSkip(result, test, reason)
            self._feedErrorsToResult(result, outcome.errors)
            if outcome.success:
                if expecting_failure:
                    if outcome.expectedFailure:
                        self._addExpectedFailure(result, outcome.expectedFailure)
                    else:
                        self._addUnexpectedSuccess(result)
                else:
                    result.addSuccess(self)
            return result
        finally:
            result.stopTest(self)
            if orig_result is None:
                stopTestRun = getattr(result, 'stopTestRun', None)
                if stopTestRun is not None:
                    stopTestRun()

            # explicitly break reference cycles:
            # outcome.errors -> frame -> outcome -> outcome.errors
            # outcome.expectedFailure -> frame -> outcome -> outcome.expectedFailure
            outcome.errors.clear()
            outcome.expectedFailure = None

            # clear the outcome, no more needed
            self._outcome = None
