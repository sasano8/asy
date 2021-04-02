import asy


async def func1():
    return 1


async def func2():
    return 2


def test_supervisor():
    supervisor = asy.supervise(func1, func2)
    result = supervisor.run()
    # assert result[0] == 1