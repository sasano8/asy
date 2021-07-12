from __future__ import annotations

import asyncio
import logging
import signal
from functools import partial
from multiprocessing import Process
from typing import Any, Callable, List, Set, Tuple, Union

from asy.protocols import PCancelToken
from asy.exceptions import RestartAllException, AllCancelException

from .normalizer import normalize_to_schedulable
from .tokens import CancelToken

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

    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        token = CancelToken()
        task = asyncio.create_task(self(token))
        return token, task

    def run(self, handle_signals: Set[str] = {"SIGINT", "SIGTERM"}):
        """新たなイベントループ上に、管理している関数群をスケジューリングし、完了まで監督する。このメソッドは自身の状態を変更しない。"""
        loop = asyncio.new_event_loop()
        token = CancelToken()

        def handle_cancel(token):
            print("cancel requested.")
            token.is_cancelled = True

        for sig_name in handle_signals:
            sig = getattr(signal, sig_name)
            loop.add_signal_handler(sig, partial(handle_cancel, token))

        try:
            result = loop.run_until_complete(self(token))
        except Exception as e:
            raise
        finally:
            loop.close()

        return result

    async def __call__(self, token: PCancelToken):
        """管理している関数群をスケジューリングし、完了まで監督する。このメソッドは自身の状態を変更しない。"""
        is_restart = True
        finalized_result = None

        def restart_callback(e):
            nonlocal token
            nonlocal is_restart

            if isinstance(e, AllCancelException):
                token.is_cancelled = True
                is_restart = False
            elif isinstance(e, RestartAllException):
                token.is_cancelled = True
                is_restart = True
            else:
                raise Exception(f"Unkown exception: {e}")
            return e

        while not token.is_cancelled:
            is_restart = False
            tokens, tasks, future, sub_futures = self._start(restart_callback)

            async def observe_cancel(future, token, tokens):
                while not future.done():
                    await asyncio.sleep(0.1)
                    if token.is_cancelled:
                        for t in tokens:
                            t.is_cancelled = True

            task = asyncio.create_task(observe_cancel(future, token, tokens))
            sub_futures.append(task)

            result = await future
            self.cancel_sub_futures(sub_futures)
            finalized_result = await self.finalize_result(result)

            if is_restart:
                token.is_cancelled = False
            else:
                token.is_cancelled = True

        return finalized_result

    @classmethod
    def cancel_sub_futures(cls, sub_futures):
        for sub in sub_futures:
            sub.cancel()

    @classmethod
    async def finalize_result(cls, wait_result):
        result = cls.get_result_from_wait(wait_result)
        await asyncio.sleep(0)
        return result

    @staticmethod
    def get_result_from_wait(wait_result):
        return wait_result[0]

    def _start(self, restart_callback):
        schedulables = self.schedulables
        on_succeed = self.on_succeed
        on_error = self.on_error
        on_cancel = self.on_cancel
        on_completed = self.on_completed

        def on_done(task):
            try:
                result = task.result()
                on_succeed(task)

            except RestartAllException as e:
                restart_callback(e)
                on_cancel(task)

            except AllCancelException as e:
                restart_callback(e)
                on_cancel(task)

            except asyncio.CancelledError as e:
                on_cancel(task)

            except Exception:  # pylint: disable=broad-except
                on_error(task)

            on_completed(task)

        tasks = []
        tokens = []
        sub_futures = []  # type: ignore

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
        self.task: asyncio.Future = None  # type: ignore
        self.token: PCancelToken = None  # type: ignore
        assert self.is_ready

    @property
    def is_ready(self):
        return self.task is None and self.token is None

    @property
    def is_running(self):
        if self.is_ready:
            return False
        return not self.task.done()

    @property
    def is_completed(self):
        if self.is_ready:
            return False
        return self.task.done()

    async def start(self):
        if self.is_running:
            raise Exception("already running.")

        token, task = self.schedule()
        self.task = task
        self.token = token
        await asyncio.sleep(0)

    async def stop(self, timeout=10000):
        if self.is_ready:
            raise Exception("The coroutine has not been executed yet")

        self.token.is_cancelled = True
        await asyncio.wait([self.task], return_when=asyncio.ALL_COMPLETED)
