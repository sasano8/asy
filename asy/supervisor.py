from __future__ import annotations

import asyncio
import logging
import signal
from functools import partial
from typing import (
    Any,
    Callable,
    Coroutine,
    Iterable,
    Iterator,
    List,
    Set,
    TypeVar,
)

from .cancel_token import CancelToken
from .utils import is_coroutine_callable

T = TypeVar("T", bound=Callable)


class Task:
    def __init__(self, coroutine_callable: Callable[..., Coroutine]) -> None:
        if not is_coroutine_callable(coroutine_callable):
            raise TypeError(f"{coroutine_callable} is not coroutine_callable")
        self._coroutine_function = coroutine_callable
        self._task: asyncio.Task = None

        self.__name__ = self.get_name_from(coroutine_callable)
        self._result = None
        self._exception = None
        self._cancelled = False
        self._done = False

    @staticmethod
    def get_name_from(obj):
        if isinstance(obj, partial):
            target = obj.func
        else:
            target = obj

        if hasattr(obj, "__name__"):
            return target.__name__
        else:
            return target.__class__.__name__

    def get_name(self):
        if self._task:
            return self._task.get_name()
        return self.__name__

    def result(self):
        if self._task is None:
            raise asyncio.exceptions.InvalidStateError("Result is not set.")
        else:
            return self._task.result()

    def exception(self):
        if self._task is None:
            raise asyncio.exceptions.InvalidStateError("Exception is not set.")
        else:
            return self._task.exception()

    def cancel(self):
        if self._task is None:
            raise asyncio.exceptions.InvalidStateError(
                "Can not cancel. Task is not scheduled."
            )
        self._task.cancel()

    def cancelled(self):
        if self._task is None:
            return False
        else:
            return self._task.cancelled()

    def done(self):
        if self._task is None:
            return False
        else:
            return self._task.done()

    def add_done_callback(self, fn: Callable) -> None:
        return self._task.add_done_callback(fn)

    def remove_done_callback(self, fn: Callable) -> int:
        return self._task.remove_done_callback(fn)

    def schedule(self, *args: Any, **kwargs: Any) -> asyncio.Task:
        if self._task is not None:
            raise RuntimeError("Task already run.")
        co = self._coroutine_function(*args, **kwargs)
        self._task = asyncio.create_task(co)
        return self._task

    async def __call__(self, *args: Any, **kwargs: Any):
        return await self.schedule(*args, **kwargs)


class SupervisorAsync(Iterable[Task]):
    """実行するコルーチン関数を管理する"""

    def __init__(
        self, coroutine_functions: Iterable[Callable[..., Coroutine]] = []
    ) -> None:
        self.__root__ = coroutine_functions

    def __iter__(self) -> Iterator[Task]:
        return self.__root__.__iter__()

    def to_executor(self, logger=None) -> LinqAsyncExecutor:
        # コルーチンファンクションからコルーチンを生成し、一度のみ実行可能なエクゼキュータを生成する
        # tasks = self.covert_coroutines_to_tasks(self.__root__)
        executor = LinqAsyncExecutor(self.__root__, logger)
        return executor

    def __enter__(self):
        raise NotImplementedError()
        # 実装したい
        # enterとexitは自身に対して呼び出される
        # __enter__で別のオブジェクトをリターンしても、exitが呼ばれるのはこのオブジェクト

    def __exit__(self, ex_type, ex_value, trace):
        raise NotImplementedError()

    def __await__(self):
        raise NotImplementedError()


class LinqAsyncExecutor(SupervisorAsync):
    """
    管理しているコルーチン関数からコルーチンを生成し、その実行管理を行う。

    実行可能な関数のインターフェースは次のとおり。

    async def func(token: PCancelToken):
        ...
    """

    def __init__(
        self, coroutine_functions: Iterable[Callable[..., Coroutine]], logger
    ) -> None:
        self.__root__: List[Task] = []
        for cf in coroutine_functions:
            if is_coroutine_callable(cf):
                self.__root__.append(Task(cf))
            else:
                raise TypeError(f"{cf} is not coroutine function.")

        self.cancel_tokens = [CancelToken() for x in self.__root__]

        # self.on_each_complete = None
        self.current_tasks = None
        self.logger = logging.getLogger() if logger is None else logger

    async def __call__(self):
        self.start()

        try:
            while self.completed() == False:
                await asyncio.sleep(1)

        except asyncio.exceptions.TimeoutError as e:
            print("timeout!!!")
        except Exception as e:
            print("exception!!!!")
            raise

    def run(self, handle_signals: Set[str] = {"SIGINT", "SIGTERM"}):
        """タスクを実行し、完了まで待機します。"""
        try:
            loop = asyncio.get_running_loop()

        except RuntimeError as e:
            loop = None

        if loop:
            # asyncioはネストしたイベントループを許可していない。それをハックするのも難しい
            raise RuntimeError(
                "This event loop is already running. use `run_async` insted of"
            )

        loop = asyncio.new_event_loop()
        cancel_tokens = self.cancel_tokens

        def handle_cancel():
            print("cancel requested.")
            for token in cancel_tokens:
                token.is_canceled = True

        for sig_name in handle_signals:
            sig = getattr(signal, sig_name)
            loop.add_signal_handler(sig, handle_cancel)

        loop.run_until_complete(self.run_async())

    async def run_async(self):
        """タスクを実行し、完了まで待機します。"""
        self.start()
        await self.join()

    async def schedule(self):
        pass

    def start(self):
        """タスクをスケジューリングします。完了まで待機されません。"""
        if self.current_tasks is not None:
            raise RuntimeError("cannot reuse already awaited coroutine")

        loop = asyncio.get_event_loop()
        self.current_tasks = []
        monitor_tasks = self.current_tasks

        # add_done_callbackのコールバックは即時実行される。実行中タスクが完了する前にメッセージが出力されてしまう。
        def lazy_notify(task):
            async def callback(task):
                await asyncio.sleep(1)
                self.log(task)

            asyncio.create_task(callback(task))

        for index, task in enumerate(self):
            token = self.cancel_tokens[index]
            future = task.schedule(token)
            monitor_tasks.append(future)
            future.add_done_callback(monitor_tasks.remove)
            future.add_done_callback(lazy_notify)

    async def stop(self, timeout=10000):
        """タスクをストップし、全てのタスクが完了もしくはキャンセルされるまで待ちます。"""
        if self.current_tasks is None:
            raise Exception("The coroutine has not been executed yet")

        # キャンセルトークンにキャンセルを通知する
        for token in self.cancel_tokens:
            token.is_canceled = True

        for task in self.current_tasks:
            if not task.done():
                task.cancel()

        await self.join()

    async def join(self):
        """全てのタスクが終了するまで待機します。サーバプログラム等の無限ループ処理は、代わりにstopを利用してください。"""
        while self.is_completed_or_raise() == False:
            await asyncio.sleep(1)

    def is_completed_or_raise(self):
        if self.current_tasks is None:
            raise Exception("The coroutine has not been executed yet")

        return self.completed()

    def completed(self):
        if self.current_tasks is None:
            return False
        else:
            return len(self.current_tasks) == 0

    def log(self, task: asyncio.Task) -> None:
        logger = self.logger
        try:
            task.result()
            logger.info(f"[COMPLETE]{task}")
            # print(f"{task}[COMPLETE]")
        except asyncio.CancelledError:
            logger.info(f"[CANCEL]{task}")
        except Exception:  # pylint: disable=broad-except
            # logger.exception(message, *message_args)
            import traceback

            logger.warning(traceback.format_exc())
            logger.warning(f"[FAILED]{task}")

    def __enter__(self):
        raise NotImplementedError()

    def __exit__(self, ex_type, ex_value, trace):
        raise NotImplementedError()

    async def __aenter__(self):
        raise NotImplementedError()
        await self.start()

    async def __aexit__(self, ex_type, ex_value, trace):
        raise NotImplementedError()
        await self.stop()
