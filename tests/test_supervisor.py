import asy
import pytest
import asyncio
import os
import signal
from multiprocessing import Queue, Process
from multiprocessing.queues import Empty as GetTimeout  # type: ignore
import time


def simple_func():
    return 1


async def async_simple_func():
    return 1


async def async_force_cancel_infinity_loop():
    while True:
        await asyncio.sleep(0.01)
    return 1


async def async_token_infinity_loop(token):
    while True:
        await asyncio.sleep(0.01)
    return 1


def normal_infinity_loop():
    while True:
        ...


def test_supervisor():
    supervisor = asy.supervise(simple_func)
    result = supervisor.run()
    assert result


SUCCEED = 1  # プログラムが正常終了し、値がキューに格納される
CANCELLED = 2  # プログラムがキャンセルされ、値がキューに格納される
TERMINATED = 3  # プログラムが強制終了するため値が返らない
INFINITY = 4  # プログラムが終了しないため値が返らない


def exist_value(queue):
    try:
        result = queue.get(timeout=0.1)
        return True
    except GetTimeout:
        return False


@pytest.mark.parametrize(
    "func, handle_signal, send_signal, exit_type",
    [
        # すぐに終了し結果が得られる
        (simple_func, None, "SIGTERM", SUCCEED),
        # シグナルをハンドルしない場合は強制終了
        (async_force_cancel_infinity_loop, None, "SIGTERM", TERMINATED),
        # SIGTERMは補足対象でないので強制終了
        (
            async_force_cancel_infinity_loop,
            "SIGINT",
            "SIGTERM",
            TERMINATED,
        ),
        # シグナルは捕捉される。トークンを取らない非同期関数は強制キャンセルされる
        (
            async_force_cancel_infinity_loop,
            "SIGTERM",
            "SIGTERM",
            CANCELLED,
        ),
        # シグナルは捕捉される。トークンでキャンセルをコントロールするが、キャンセル処理がないので無限ループ
        (
            async_token_infinity_loop,
            "SIGTERM",
            "SIGTERM",
            INFINITY,
        ),
        # シグナルは捕捉される。同期関数はキャンセルできないので無限ループ
        (
            normal_infinity_loop,
            "SIGTERM",
            "SIGTERM",
            INFINITY,
        ),
        # シグナルを捕捉せず強制終了
        (
            normal_infinity_loop,
            None,
            "SIGTERM",
            TERMINATED,
        ),
    ],
)
def test_supervisor_cancel_control(func, handle_signal, send_signal, exit_type):

    if "linux":
        sig = getattr(signal, send_signal)
    elif "windows":
        dic = {"SIGINT": signal.CTRL_C_EVENT, "SIGTERM": signal.CTRL_BREAK_EVENT}  # type: ignore
        sig = dic[send_signal]

    sig: int = int(sig)  # type: ignore
    handle_signals = {handle_signal} if handle_signal else set()
    queue = Queue()  # type: ignore

    def main(queue, handle_signals=set()):
        supervisor = asy.supervise(func)
        result = supervisor.run(handle_signals=handle_signals)
        queue.put(1)  # ピッケル化可能なオブジェクトしかキューに追加できない

    process = Process(
        target=main, kwargs=dict(queue=queue, handle_signals=handle_signals)
    )

    try:
        process.start()
        time.sleep(0.1)
        result = queue.get(timeout=0.1)
        process.join(timeout=0.1)
        assert isinstance(process.exitcode, int)
        assert exit_type == SUCCEED

    except GetTimeout as e:
        os.kill(process.pid, sig)  # type: ignore
        time.sleep(0.1)

        if exit_type == INFINITY:
            # infinity loop
            time.sleep(1)
            assert not exist_value(queue)
            assert process.exitcode is None
            assert process.is_alive()
        else:
            if exit_type == CANCELLED:
                assert exist_value(queue)
                assert isinstance(process.exitcode, int)
            elif exit_type == TERMINATED:
                assert not exist_value(queue)
                assert isinstance(process.exitcode, int)
            else:
                raise Exception()

    except:
        raise
    finally:
        process.kill()


def test_restart():

    count1 = 0
    count2 = 0

    def restart():
        nonlocal count1
        count1 += 1
        if count1 == 2:
            return
        raise asy.RestartAllException()

    def countup():
        nonlocal count2
        count2 += 1

    supervisor = asy.supervise(restart, countup)
    supervisor.run()

    assert count1 == 2
    assert count2 == 2


def test_start_stop():
    result = 0

    def func1():
        nonlocal result
        result = 1

    async def func2(token):
        nonlocal result
        result = 2
        await asyncio.sleep(0.1)
        result = 3

    async def main(*funcs):
        supervisor = asy.supervise(*funcs)
        await supervisor.start()
        await supervisor.stop()

    asyncio.run(main(func1))
    assert result == 1

    asyncio.run(main(func2))
    assert result == 3


def test_start_duplicate():
    async def main():
        async def dummy():
            await asyncio.sleep(5)

        supervisor = asy.supervise(dummy)
        await supervisor.start()
        with pytest.raises(Exception, match="already running"):
            await supervisor.start()

    asyncio.run(main())


def test_start_after_stop():
    result = 0

    async def main():
        async def dummy(token):
            nonlocal result
            result = 1
            await asyncio.sleep(0.1)
            result = 2

        supervisor = asy.supervise(dummy)
        await supervisor.start()
        await asyncio.sleep(0.2)
        await supervisor.stop()
        assert result == 2
        await supervisor.start()

    asyncio.run(main())
    assert result == 1
    # TODO: stopを実行しない場合、正しくキャンセルコントロールされない
    # キャンセルを抑制しているにも関わらず、強制キャンセルされ、ディスポーズ処理がされない
    # このテストの場合、最終的なresultは2になるべきである


def test_stop_before_start():
    async def main():
        async def dummy():
            await asyncio.sleep(0.1)

        supervisor = asy.supervise(dummy)
        with pytest.raises(Exception, match="The coroutine has not been executed yet"):
            await supervisor.stop()

    asyncio.run(main())


def test_stop_twice():
    async def main():
        async def dummy():
            await asyncio.sleep(0.1)

        supervisor = asy.supervise(dummy)
        await supervisor.start()
        await supervisor.stop()
        await supervisor.stop()

    asyncio.run(main())
