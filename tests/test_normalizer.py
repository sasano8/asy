import pytest
from asy.normalizer import normalize_to_schedulable
from typing import Any
from asy import PCancelToken, CancelToken
from asy.schedulable import ForceCancelAsyncTask, CancelableAsyncTask
import asyncio


class MYCancelToken1:
    is_cancelled: bool = False


class MYCancelToken2:
    is_cancelled: bool


class MYCancelToken3:
    def __init__(self):
        self.is_cancelled = False


class OtherClass:
    pass


async def two_args(args1, args2):
    return 1


async def no_args():
    return 1


def no_args_normal():
    return 1


async def one_args(token):
    return 1


def one_args_normal(token):
    return 1


async def one_args_any(token: Any):
    return 1


async def one_args_pcancel_token(token: PCancelToken):
    return 1


async def one_args_cancel_token(token: CancelToken):
    return 1


async def one_args_my_cancel_token1(token: MYCancelToken1):
    return 1


async def one_args_my_cancel_token2(token: MYCancelToken2):
    return 1


async def one_args_my_cancel_token3(token: MYCancelToken3):
    return 1


async def one_args_other_class(token: OtherClass):
    return 1


class CallableNoArg:
    async def __call__(self):
        return 1


class CallableOneArg:
    async def __call__(self, token):
        return 1


class CallableNoArgNormal:
    def __call__(self):
        return 1


class CallableOneArgNormal:
    def __call__(self, token):
        return 1


async def one_args_pcancel_token_lazy(token: "PCancelToken"):
    return 1


class CallableLazy:
    async def __call__(self, token: "PCancelToken"):
        return 1


@pytest.mark.parametrize(
    "expect_type, value",
    [
        (None, two_args),
        (ForceCancelAsyncTask, no_args),
        (ForceCancelAsyncTask, no_args_normal),
        (CancelableAsyncTask, one_args),
        (None, one_args_normal),
        (CancelableAsyncTask, one_args_any),
        (CancelableAsyncTask, one_args_pcancel_token),
        (CancelableAsyncTask, one_args_cancel_token),
        (CancelableAsyncTask, one_args_my_cancel_token1),
        (CancelableAsyncTask, one_args_my_cancel_token2),
        (None, one_args_my_cancel_token3),
        (None, one_args_other_class),
        (ForceCancelAsyncTask, CallableNoArg()),
        (CancelableAsyncTask, CallableOneArg()),
        (ForceCancelAsyncTask, CallableNoArgNormal()),
        (None, CallableOneArgNormal()),
        (CancelableAsyncTask, one_args_pcancel_token_lazy),
        (CancelableAsyncTask, CallableLazy()),
    ],
)
def test_normalize_to_task(expect_type, value):
    if expect_type:
        result = normalize_to_schedulable(value)
        assert result
        assert isinstance(result, expect_type)
    else:
        with pytest.raises(Exception):
            result = normalize_to_schedulable(value)


@pytest.mark.parametrize(
    "func",
    [
        no_args,
        no_args_normal,
        one_args,
        CallableNoArg(),
        CallableOneArg(),
        CallableNoArgNormal(),
    ],
)
def test_task(func):
    async def main():
        task = normalize_to_schedulable(func)
        token, task = task.schedule()
        assert isinstance(token, PCancelToken)
        assert isinstance(task, asyncio.Task)
        assert await asyncio.wait_for(task, timeout=10) == 1

    asyncio.run(main())
