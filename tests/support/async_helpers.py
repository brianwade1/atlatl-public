"""Bounded waits; ownership is explicit so unrelated pytest tasks are untouched."""

import asyncio
from contextlib import asynccontextmanager, contextmanager


@asynccontextmanager
async def owned_tasks(timeout=2):
    tasks = []

    def start(coroutine):
        task = asyncio.create_task(coroutine)
        tasks.append(task)  # Register before any later setup can fail.
        return task

    try:
        yield start
    finally:
        for task in tasks:
            if not task.done():
                task.cancel()
        if tasks:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), timeout)
            for result in results:
                if isinstance(result, BaseException) and not isinstance(result, asyncio.CancelledError):
                    raise result


@contextmanager
def installed_loop(previous=None):
    """Synchronous-only owned loop; caller supplies prior loop (or explicit None).

    Python 3.14 get_event_loop raises when unset. Avoid implicit loop creation
    and use subprocesses for constructors that install additional loops.
    """
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        yield loop
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.wait_for(
                    asyncio.gather(*pending, return_exceptions=True), 2))
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor(timeout=2))
        finally:
            loop.close()
            asyncio.set_event_loop(previous)
