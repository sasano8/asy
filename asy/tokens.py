from .protocols import PCancelToken
import asyncio


class CancelToken(PCancelToken):
    is_cancelled: bool = False

    def __init__(self):
        self.is_cancelled = False


class ForceCancelToken(PCancelToken):
    def __init__(self, task: asyncio.Task):
        self.task = task

    @property
    def is_cancelled(self) -> bool:
        return self.task.cancelled()

    @is_cancelled.setter
    def is_cancelled(self, value: bool):
        if value:
            self.task.cancel()


class CallbackCancelToken(PCancelToken):
    def __init__(self, callback):
        self.callback = callback
        self._is_cancelled = False

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @is_cancelled.setter
    def is_cancelled(self, value: bool):
        self._is_cancelled = value
        if not value:
            self.callback()