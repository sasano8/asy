import asyncio
from .task import TaskBase
from functools import wraps
import inspect
from typing import Any
from .task import ForceCancelAsyncTask, CancelableAsyncTask


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
        key = list(sig.parameters.keys())[0]
        param = sig.parameters[key]
        if (
            param.annotation == inspect._empty
            or param.annotation == Any
            or hasattr(param.annotation, "is_cancelled")
            or getattr(param.annotation, "__annotations__", {}).get("is_cancelled")
        ):
            if inspect.iscoroutinefunction(target):
                return CancelableAsyncTask(target)
            else:
                raise RuntimeError("同期関数はキャンセルトークンを受け入れられません")

        else:
            raise RuntimeError(f"{param.annotation} has not attribute 'is_cancelled'.")
    else:
        raise RuntimeError(f"タスク化可能な関数は引数なしか単一の引数のみ許容されます。")

    return value


def is_schedulable(value):
    try:
        result = normalize_to_schedulable(value)
        return True
    except:
        return False