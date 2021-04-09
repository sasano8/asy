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


async def one_args(t):
    return 1


def one_args_normal(t):
    return 1


async def one_args_any(t: Any):
    return 1


async def one_args_pcancel_token(t: PCancelToken):
    return 1


async def one_args_cancel_token(t: CancelToken):
    return 1


async def one_args_my_cancel_token1(t: MYCancelToken1):
    return 1


async def one_args_my_cancel_token2(t: MYCancelToken2):
    return 1


async def one_args_my_cancel_token3(t: MYCancelToken3):
    return 1


async def one_args_other_class(t: OtherClass):
    return 1


async def one_args_other_class_named_token(token: OtherClass):
    return 1


class CallableNoArg:
    async def __call__(self):
        return 1


class CallableOneArg:
    async def __call__(self, t):
        return 1


class CallableNoArgNormal:
    def __call__(self):
        return 1


class CallableOneArgNormal:
    def __call__(self, t):
        return 1


async def one_args_pcancel_token_lazy(t: "PCancelToken"):
    return 1


class CallableLazy:
    async def __call__(self, t: "PCancelToken"):
        return 1


CANCELABLE = CancelableAsyncTask
FORCE_CANCEL = ForceCancelAsyncTask
ERROR = None


@pytest.mark.parametrize(
    "expect_type, value",
    [
        (ERROR, two_args),
        (FORCE_CANCEL, no_args),
        (FORCE_CANCEL, no_args_normal),
        (CANCELABLE, one_args),
        (ERROR, one_args_normal),
        (CANCELABLE, one_args_any),
        (CANCELABLE, one_args_pcancel_token),
        (CANCELABLE, one_args_cancel_token),
        (CANCELABLE, one_args_my_cancel_token1),
        (CANCELABLE, one_args_my_cancel_token2),
        (ERROR, one_args_my_cancel_token3),
        (ERROR, one_args_other_class),
        # # If the argument name contains token, skip type validation
        (CANCELABLE, one_args_other_class_named_token),
        (FORCE_CANCEL, CallableNoArg()),
        (CANCELABLE, CallableOneArg()),
        (FORCE_CANCEL, CallableNoArgNormal()),
        (ERROR, CallableOneArgNormal()),
        (CANCELABLE, one_args_pcancel_token_lazy),
        (CANCELABLE, CallableLazy()),
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
