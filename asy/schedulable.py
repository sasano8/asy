from typing import Type, TypeVar, Tuple
from .protocols import PAwaitable, PCancelToken, PSchedulable

from .tokens import CancelToken, ForceCancelToken
import asyncio

T = TypeVar("T", bound=PAwaitable)


class Schedulable(PSchedulable):
    def __init__(self, func):
        self.factory = func


class CancelableAsyncTask(Schedulable):
    """キャンセルトークンを受け入れることができるタスクとしてマークするためのクラス"""

    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        token = CancelToken()
        task = asyncio.create_task(self.factory(token))
        return token, task


class ForceCancelAsyncTask(Schedulable):
    """キャンセルトークンを受け入れできないタスクとしてマークするためのクラス。スーパーバイザーがキャンセルを検知した時、asyncioのcancel()が直接呼ばれる"""

    def schedule(self) -> Tuple[PCancelToken, asyncio.Task]:
        task = asyncio.create_task(self.factory())
        token = ForceCancelToken(task)
        return token, task
