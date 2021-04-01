from .supervisor import SupervisorAsync
from asyncio import sleep


def run(*args):
    return SupervisorAsync(*args).to_executor().run()


def schedule(*args):
    """
    Schedule the execution of a coroutine object in a spawn task.

    Return: Task object.
    """
    raise NotImplementedError()


def supervise(*args):
    return SupervisorAsync(*args).to_executor()
