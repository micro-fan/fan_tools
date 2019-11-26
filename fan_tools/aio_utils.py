import asyncio
import logging

from psycopg2.extras import DictCursor

import aiopg


class DbRecordsProcessorWorker:
    """
    Asyncio worker which wait for new records in pg db table and process them.
    """

    MAX_LOOP = 12

    def __init__(self, dsn, worker_class, max_loop=MAX_LOOP):
        self.name = worker_class.__name__
        self.log = logging.getLogger(f'processor.{self.name}')

        self.dsn = dsn
        self.worker = worker_class(self.log)
        self.max_loop = max_loop

        self.debug('init processor')
        self.loop = asyncio.get_event_loop()
        self.closed = self.loop.create_future()

    def debug(self, msg):
        self.log.debug(f'[{self.name}] {msg}')

    def info(self, msg):
        self.log.info(f'[{self.name}] {msg}')

    async def on_start(self):
        self.debug(f'Starting... {self.dsn}')
        self.pool = await aiopg.create_pool(self.dsn)
        self.loop_timer = self.loop.call_soon(self.main_loop)
        self.debug('Started')

    def handle_errors(self, fut):
        if fut.exception():
            self.closed.set_exception(fut.exception())

    def main_loop(self):
        self.debug('Main loop')
        self.loop.create_task(self._inner()).add_done_callback(self.handle_errors)

    async def _inner(self):
        async with self.pool.acquire() as conn:
            await self.worker.process_records(conn)
            try:
                await asyncio.wait_for(self.notify_wait(conn), self.max_loop)
            except asyncio.TimeoutError:
                pass
        self.loop.call_soon(self.main_loop)

    async def notify_wait(self, conn):
        async with conn.cursor() as cursor:
            try:
                await cursor.execute(f'LISTEN {self.worker.pg_channel}')
                await asyncio.wait_for(conn.notifies.get(), self.max_loop)
            except asyncio.TimeoutError:
                pass

    def run(self):
        def check_error(fut):
            e = fut.exception()
            if e:
                logging.exception('Terminate: {}'.format(e))
                loop = asyncio.get_event_loop()
                loop.stop()
                loop.close()

        self.info(f'Start {self.name}')
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.on_start())
        task.add_done_callback(check_error)
        self.debug('run loop')
        loop.run_until_complete(self.closed)


async def dict_query(conn, query, params):
    async with conn.cursor(cursor_factory=DictCursor) as cur:
        await cur.execute(query, params)
        return [dict(x) for x in await cur.fetchall()]


async def sql_update(conn, query, params):
    async with conn.cursor(cursor_factory=DictCursor) as cur:
        await cur.execute(query, params)
