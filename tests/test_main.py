import asyncio

import pytest

from asy import SupervisorAsync


def test_if_success():
    async def func(token):
        return 1

    supervisor = SupervisorAsync([func]).to_executor()
    supervisor.run()
    assert supervisor.completed()


def test_if_raise():
    async def func(token):
        raise Exception("test")

    supervisor = SupervisorAsync([func]).to_executor()
    supervisor.run()
    with pytest.raises(Exception, match="test"):
        tasks = list(supervisor)
        tasks[0].result()


def test_executor():
    async def func(token):
        raise Exception("test")

    supervisor = SupervisorAsync([func])
    executor = supervisor.to_executor()
    asyncio.run(asyncio.wait_for(executor(), timeout=5))


def test_run():
    result = None

    async def func1(token):
        nonlocal result
        result = 1

    async def func2(token):
        nonlocal result
        result = 2

    # メインスレッド上で動作
    supervisor = SupervisorAsync([func1])
    executor = supervisor.to_executor()
    executor.run()
    assert result == 1

    # イベントループ中で動作
    async def main():
        supervisor = SupervisorAsync([func2])
        executor = supervisor.to_executor()
        await executor.run_async()

    asyncio.run(main())
    assert result == 2
