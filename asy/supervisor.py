from __future__ import annotations
from asy.protocols import PCancelToken, PSchedulable

import asyncio
import logging
import signal
from typing import (
    Any,
    List,
    Set,
    Tuple,
)
import logging
from .cancel_token import CancelToken, CallbackCancelToken

logger = logging.getLogger(__name__)


class Supervisor:
    def __init__(self, *schedulables: PSchedulable):
        self.schedulables = schedulables
        self.cancel_tokens: List[PCancelToken] = None  # type: ignore
        self.tasks = None
        self.future: asyncio.Future = None  # type: ignore
        self.sub_futures = None

        self.set_config()
        # self.set_config_print_log()

    def set_config(
        self, on_succeed=None, on_error=None, on_cancel=None, on_completed=None
    ):
        self.on_succeed = on_succeed or (
            lambda task: logger.info(f"[SUCCESS]{task.result()}")
        )
        self.on_error = on_error or (lambda task: logger.info(f"[FAIL]{task}"))
        self.on_cancel = on_cancel or (lambda task: logger.info(f"[CANCEL]{task}"))
        self.on_completed = on_completed or (
            lambda task: logger.info(f"[COMPLETE]{task}")
        )

    def set_config_print_log(self):
        self.on_succeed = lambda task: print(task)
        self.on_error = lambda task: print(task)
        self.on_cancel = lambda task: print(task)
        self.on_completed = lambda task: print(task)

    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        token = CancelToken()
        task = asyncio.create_task(self.__call__(token))
        return token, task

    def run(self, handle_signals: Set[str] = {"SIGINT", "SIGTERM"}):
        loop = asyncio.new_event_loop()

        def handle_cancel():
            print("cancel requested.")
            asyncio.create_task(self.stop())

        for sig_name in handle_signals:
            sig = getattr(signal, sig_name)
            loop.add_signal_handler(sig, handle_cancel)

        token = CallbackCancelToken(handle_cancel)

        async def main():
            tokens, tasks, future, sub_futures = self._start()
            result = await future
            return await self.finalize(result, sub_futures)

        result = loop.run_until_complete(main())
        loop.close()
        self.clear()
        return result

    async def __call__(self, token: PCancelToken):
        tokens, tasks, future, sub_futures = self._start()

        async def observe_cancel():
            while future.done() == False:
                await asyncio.sleep(0.1)
                if token.is_cancelled:
                    await self.stop()

        task = asyncio.create_task(observe_cancel())
        sub_futures.append(task)
        result = await future
        return await self.finalize(result, sub_futures)

    @classmethod
    async def finalize(cls, wait_result, sub_futures):
        for sub in sub_futures:
            sub.cancel()

        result = cls.get_result_from_wait(wait_result)
        await asyncio.sleep(0)
        return result

    @staticmethod
    def get_result_from_wait(wait_result):
        return wait_result[0]

    def _start(self):
        if not self.is_ready:
            raise Exception("already running.")

        on_succeed = self.on_succeed
        on_error = self.on_error
        on_cancel = self.on_cancel
        on_completed = self.on_completed

        def on_done(task):
            try:
                result = task.result()
                on_succeed(task)
            except asyncio.CancelledError:
                # logger.info(f"[CANCEL]{task}")
                on_cancel(task)
            except Exception:  # pylint: disable=broad-except
                # logger.exception(message, *message_args)
                # import traceback

                # logger.warning(traceback.format_exc())
                # logger.warning(f"[FAILED]{task}")
                on_error(task)
            on_completed(task)

        tasks = []
        tokens = []
        sub_futures = []

        for index, schedulable in enumerate(self.schedulables):
            token, task = schedulable.schedule()
            tokens.append(token)
            tasks.append(task)
            task.add_done_callback(on_done)

        future = asyncio.create_task(
            asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        )
        self.future = future
        self.cancel_tokens = tokens
        self.tasks = tasks
        self.sub_futures = sub_futures
        return tokens, tasks, future, sub_futures

    async def start(self):
        tokens, tasks, future, sub_futures = self._start()

    def cancel(self):
        if self.is_ready:
            raise Exception("The coroutine has not been executed yet")

        for token in self.cancel_tokens:
            token.is_cancelled = True

    async def stop(self, timeout=10000):
        self.cancel()
        await self.future

    def is_completed(self):
        return self.future.done()

    @property
    def is_ready(self):
        return all(
            [
                self.future is None,
                self.cancel_tokens is None,
                self.tasks is None,
                self.sub_futures is None,
            ]
        )

    def clear(self):
        self.future = None
        self.cancel_tokens = None
        self.tasks = None
        self.sub_futures = None
        assert self.is_ready
