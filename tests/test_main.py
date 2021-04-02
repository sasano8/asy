import asyncio

import pytest

import asy


def test_if_success():
    async def func(token):
        return 1

    supervisor = asy.supervise(func)
    result = supervisor.run()
    assert result


# def test_if_raise():
#     async def func(token):
#         raise Exception("test")

#     supervisor = asy.supervise(func)
#     supervisor.run()
#     with pytest.raises(Exception, match="test"):
#         tasks = list(supervisor)
#         tasks[0].result()


def test_run():
    result = None

    async def func1(token):
        nonlocal result
        result = 1

    async def func2(token):
        nonlocal result
        result = 2

    # メインスレッド上で動作
    supervisor = asy.supervise(func1)
    supervisor.run()
    assert result == 1

    # イベントループ中で動作
    async def main():
        supervisor = asy.supervise(func2)
        supervisor.schedule()
        await asyncio.sleep(0)  # 待たないと実行されない

    asyncio.run(main())
    assert result == 2
