import asyncio
import enum
import logging
import time

from asyncio import CancelledError, Future, Task, shield
from typing import Awaitable, Callable, Coroutine, Dict, List, Optional

from fan_tools.generic.debug import DEBUG_GLOBAL, DebugObject


log = logging.getLogger(__name__)


class State(enum.Enum):
    STARTING = 'starting'
    CALLBACK = 'callback'
    SLEEP = 'sleep'
    BACKOFF = 'backoff'
    ON_ERROR = 'on_error'
    STOPPING = 'stopping'
    STOPPED = 'stopped'


class NamedLogger:
    def __init__(self, name):
        self.name = name

    def _log(self, level, msg, *args, **kwargs):
        msg = f'<{self.name}> {msg}'
        getattr(log, level)(msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log('debug', msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log('info', msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._log('warn', msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log('warning', msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._log('exception', msg, *args, **kwargs)


def serialize_merge(src: Dict, dst: Dict, prefix: str) -> Dict:
    for section in ['values', 'buttons']:
        for name, value in src.get(section, {}).items():
            dst[section][f'{prefix}.{name}'] = value
    return dst


class Timer:
    def __init__(self, parent):
        self.parent = parent
        self.wait_event = asyncio.Event()
        self.wait_futures: List[Future] = []
        self._wait_time = 0

    async def wait(self, timeout: int | float):
        if self.has_wait_futures:
            raise RuntimeError('Already waiting')

        wait_futures: List[Future] = [self._sleep(timeout)]
        self._wait_time = time.time() + timeout
        await self._wait_and_clean(wait_futures)

    async def wait_for(self, coro: Coroutine, timeout: int | float):
        if self.has_wait_futures:
            raise RuntimeError('Already waiting')

        f = self._wait_and_clean([self._sleep(timeout), asyncio.create_task(coro)])
        await f

    async def join(self):
        if self.has_wait_futures:
            await asyncio.wait(self.wait_futures, return_when=asyncio.FIRST_COMPLETED)

    def __repr__(self) -> str:
        return f'<Timer wait={self.current_wait_time:.2f}s>'

    @property
    def has_wait_futures(self) -> bool:
        if not self.wait_futures:
            return False
        return any([not t.done() for t in self.wait_futures])

    @property
    def current_wait_time(self) -> float:
        if not self.has_wait_futures:
            return 0
        return max(self._wait_time - time.time(), 0)

    async def _wait_and_clean(self, fs: List[Future]):
        self.wait_futures = fs
        try:
            await self.join()
        finally:
            for f in fs:
                if not f.done() and not f.get_loop().is_closed():
                    f.cancel()
            self.wait_futures = []

    def _sleep(self, timeout: float | int):
        ret = asyncio.create_task(asyncio.sleep(timeout))
        self._wait_time = time.time() + timeout
        return ret

    def serialize(self):
        return {
            'values': {
                'wait_time': self.current_wait_time.__round__(2),
                'wait_futures': len(self.wait_futures),
            }
        }

    def trigger(self):
        if self.has_wait_futures:
            self.wait_futures[0].cancel()


Callback = Callable[..., None] | Callable[..., Awaitable[None]]
ACTIVE_LOOP = 'active_loop'


class Controller:
    stop_states = {State.STOPPING, State.STOPPED}

    def __init__(self, retry_timeout=5, loop_interval=60, loop_timeout=120, debug=False):
        self.state = State.STOPPED
        self.timer = Timer(self)
        self.retry_timeout = retry_timeout
        self.loop_interval = loop_interval
        self.loop_timeout = loop_timeout

        self.active_loops: Dict[str, Task] = {}
        self.on_stop_callbacks: Dict[str, Callback] = {}

        self.debug: Optional[DebugObject] = None
        self.name = getattr(self, 'name', f'{self.__class__.__name__}_{id(self)}')
        self.log = NamedLogger(self.name)

        if debug:
            if isinstance(debug, DebugObject):
                self.debug = DebugObject(parent=debug, name=self.name, serialize=self.serialize)
            else:
                self.debug = DebugObject(
                    parent=DEBUG_GLOBAL.get(), name=self.name, serialize=self.serialize
                )

            if self.debug:

                def _remove_child():
                    self.debug.parent.remove_child(self.debug)

                self.add_stop_callback(f'debug_{self.name}', _remove_child)

    async def loop_iteration(self):
        """
        main loop work is here
        """

    async def startup(self):
        """
        run before the main loop
        """

    async def shutdown(self):
        """
        run after the main loop
        """

    async def on_error(self, exception) -> Optional[bool]:
        """
        return True if shoult stop
        do reinitialization here if required
        """
        self.log.exception(f'Exception in loop: {self} {exception}')

    def serialize(self, out):
        """
        {'values': {}, 'buttons': {}}
        """
        timer_out = self.timer.serialize()
        out = serialize_merge(timer_out, out, 'timer')
        return out

    def add_stop_callback(self, name: str, callback: Callback):
        """
        add dynamic function to run during stop
        """
        if name in self.on_stop_callbacks:
            raise RuntimeError(f'Callback {name} already registered')
        self.on_stop_callbacks[name] = callback

    def track_task(self, task: Task | Coroutine, name: str | None = None):
        """
        register additional loops, they will stop automatically
        """
        if not isinstance(task, Task):
            task = asyncio.create_task(task)

        if not name:
            name = f'task_{id(task)}_{str(task)}'

        if name in self.active_loops:
            raise RuntimeError(f'Task {name} already registered')

        self.active_loops[name] = task

        def __maybe_remove(*_):
            if name in self.active_loops and self.active_loops[name] == task:
                del self.active_loops[name]

        task.add_done_callback(__maybe_remove)

    def set_state(self, value):
        self.log.debug(f'{self} state changed: {self.state} -> {value}')
        self.state = value
        if self.debug:
            self.debug.track('state', str(value))

    def get_retry_timeout(self):
        return self.retry_timeout

    def get_loop_interval(self):
        return self.loop_interval

    async def start(self):
        if self.state != State.STOPPED:
            raise RuntimeError(f'Cannot start {self} in state {self.state}')

        self.state = State.STARTING
        await self.startup()
        active_loop = asyncio.ensure_future(self.inner_loop())
        self.track_task(active_loop, ACTIVE_LOOP)
        return active_loop

    def trigger_stop(self):
        self.log.debug(f'Triggering stop {self}')

        for name, loop in self.active_loops.items():
            self.log.debug(f'Loop item {name} {loop=}')
        for name, callback in self.on_stop_callbacks.items():
            self.log.debug(f'Callback item {name} {callback=}')

        if self.is_running:
            self.set_state(State.STOPPING)
            self.timer.trigger()

    async def stop(self):
        self.trigger_stop()
        active_loop = self.active_loops.get(ACTIVE_LOOP)
        if active_loop:
            await active_loop

    @property
    def is_running(self):
        return self.state not in self.stop_states

    async def inner_loop(self):
        try:
            while self.is_running:
                try:
                    self.set_state(State.CALLBACK)
                    await self.timer.wait_for(self.loop_iteration(), timeout=self.loop_timeout)
                    self.set_state(State.SLEEP)
                    await self.timer.wait(self.get_loop_interval())
                except CancelledError:
                    self.log.debug(f'Cancelled loop: {self}')
                    break
                except Exception as e:
                    self.log.debug('check should_stop')
                    should_stop = await self._call_on_error(e)
                    if should_stop:
                        log.info(f'Stopping loop because of error: {self}')
                        break
                    self.set_state(State.BACKOFF)
                    timeout = self.get_retry_timeout()
                    self.log.info(f'Retry in {timeout} seconds')
                    await self.timer.wait(timeout)
        finally:
            self.log.debug(f'Shielded shutdown in finally {self.state=}')
            await self._do_shutdown()

    async def _call_on_error(self, error) -> bool:
        self.set_state(State.ON_ERROR)
        should_stop = False
        try:
            should_stop = bool(await self.on_error(error))
        except Exception as e:
            self.log.exception(f'Exception in on_error handler: {e}')
        return should_stop

    async def _do_shutdown(self):
        if active_loop := self.active_loops.get(ACTIVE_LOOP):
            self.log.debug(f'is_cancelled={active_loop.cancelled()}')
        self.set_state(State.STOPPING)

        await self.run_shielded_shutdown()
        await self.stop_tracked_tasks()
        await self.run_on_stop_callbacks()
        self.set_state(State.STOPPED)

    async def run_shielded_shutdown(self):
        try:
            self.log.info(f'shielded shutdown {self=}')
            await shield(self.shutdown())
        except Exception:
            self.log.exception('During shielded shutdown')

    async def stop_tracked_tasks(self):
        wait_tasks = []
        for task_name, task in self.active_loops.items():
            if task_name != ACTIVE_LOOP and not task.done():
                self.log.debug(f'is_cancelled={task.cancelled()}')
                task.cancel()
                wait_tasks.append(task)
        try:
            await asyncio.gather(*wait_tasks, return_exceptions=True)
        except Exception:
            self.log.exception('During stopping active tasks')

    async def run_on_stop_callbacks(self):
        for callback_name, callback in self.on_stop_callbacks.items():
            try:
                if asyncio.iscoroutinefunction(callback):
                    await shield(callback())
                else:
                    callback()
            except Exception as e:
                log.exception(f'Exception in on_stop callback={callback_name}: {e}')

    def __repr__(self):
        return f'<{self.__class__.__name__} {id(self)} state={self.state}>'
