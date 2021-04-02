import asyncio
import inspect
from functools import wraps
from typing import Any, get_type_hints

from .protocols import PCancelToken
from .task import CancelableAsyncTask, ForceCancelAsyncTask, TaskBase


def normalize_to_schedulable(value):
    if isinstance(value, TaskBase):
        return value

    if not callable(value):
        raise Exception()

    if isinstance(value, asyncio.Task):
        raise Exception()
    elif isinstance(value, asyncio.Future):
        raise Exception()
    elif inspect.iscoroutine(value):
        raise Exception()

    if inspect.isfunction(value):
        target = value
    else:
        target = value.__call__

    sig = inspect.signature(target)
    param_size = len(sig.parameters)

    if param_size == 0:
        if inspect.iscoroutinefunction(target):
            return ForceCancelAsyncTask(target)
        else:

            @wraps(target)
            async def wrapped():
                return target()

        return ForceCancelAsyncTask(wrapped)

    elif param_size == 1:

        annotation = list(sig.parameters.values())[0].annotation
        if isinstance(annotation, str):
            dic = get_type_hints(target)  # 型ヒント無しは何も返さない。Any返せや！！！
            annotations = list(dic.values())
            if not annotations:
                annotation = Any
            else:
                annotation = annotations[0]

        if (
            annotation == inspect._empty  # type: ignore
            or annotation == Any
            or hasattr(annotation, "is_cancelled")
            or getattr(annotation, "__annotations__", {}).get("is_cancelled")
        ):
            if inspect.iscoroutinefunction(target):
                return CancelableAsyncTask(target)
            else:
                raise RuntimeError("同期関数はキャンセルトークンを受け入れられません")

        else:
            raise RuntimeError(
                f"{target} {annotation} has not attribute 'is_cancelled'."
            )
    else:
        raise RuntimeError(f"タスク化可能な関数は引数なしか単一の引数のみ許容されます。")

    return value


def is_schedulable(value):
    try:
        result = normalize_to_schedulable(value)
        return True
    except:
        return False
