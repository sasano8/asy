from __future__ import annotations
from asy.protocols import PCancelToken
from multiprocessing import Process

import asyncio
import logging
import signal
from typing import Any, List, Set, Tuple, Callable, Union
import logging
from .tokens import CancelToken
from .normalizer import normalize_to_schedulable

logger = logging.getLogger(__name__)


class SupervisorBase:
    def __init__(
        self, *schedulables: Union[Callable[[], Any], Callable[[PCancelToken], Any]]
    ):
        tmp = [normalize_to_schedulable(x) for x in schedulables]
        self.schedulables = tmp
        self.set_config()
        self.__post_init__()

    def __post_init__(self):
        pass

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

    def to_process(self, handle_signals: Set[str] = {"SIGINT", "SIGTERM"}):
        return Process(target=self.run, kwargs={"handle_signals": handle_signals})

    def run(self, handle_signals: Set[str] = {"SIGINT", "SIGTERM"}):
        """新たなイベントループ上に、管理している関数群をスケジューリングし、完了まで監督する。このメソッドは自身の状態を変更しない。"""
        loop = asyncio.new_event_loop()
        token = CancelToken()

        def handle_cancel():
            print("cancel requested.")
            token.is_cancelled = True

        for sig_name in handle_signals:
            sig = getattr(signal, sig_name)
            loop.add_signal_handler(sig, handle_cancel)

        # result = loop.run_until_complete(self(token))
        try:
            result = loop.run_until_complete(self(token))
        except Exception as e:
            raise
        finally:
            loop.close()

        return result

    async def __call__(self, token: PCancelToken):
        """管理している関数群をスケジューリングし、完了まで監督する。このメソッドは自身の状態を変更しない。"""
        tokens, tasks, future, sub_futures = self._start()

        async def observe_cancel(token):
            while not future.done():
                await asyncio.sleep(0.1)
                if token.is_cancelled:
                    for token in tokens:
                        token.is_cancelled = True

        task = asyncio.create_task(observe_cancel(token))
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
        schedulables = self.schedulables
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

        for index, schedulable in enumerate(schedulables):
            token, task = schedulable.schedule()
            tokens.append(token)
            tasks.append(task)
            task.add_done_callback(on_done)

        future = asyncio.create_task(
            asyncio.wait(tasks, return_when=asyncio.ALL_COMPLETED)
        )
        return tokens, tasks, future, sub_futures


class Supervisor(SupervisorBase):
    def __post_init__(self):
        self.clear()

    def clear(self):
        self.task: asyncio.Future = None
        self.token: PCancelToken = None
        assert not self.is_running

    async def start(self):
        if self.is_running:
            raise Exception("already running.")

        token, task = self.schedule()
        self.task = task
        self.token = token
        await asyncio.sleep(0)

    @property
    def is_running(self):
        is_ready = self.task is None and self.token is None
        return not is_ready

    @property
    def is_completed(self):
        if not self.is_running:
            return False
        return self.task.done()

    async def cancel(self):
        if not self.is_running:
            raise Exception("The coroutine has not been executed yet")

        self.token.is_cancelled = True
        await asyncio.sleep(0)

    async def stop(self, timeout=10000):
        self.cancel()
        await self.task
