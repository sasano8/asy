from .supervisor import Supervisor
from typing import Union, Callable, Any
from .protocols import PCancelToken


def run(*args: Union[Callable[[], Any], Callable[[PCancelToken], Any]]):
    return supervise(*args).run()


def supervise(*args: Union[Callable[[], Any], Callable[[PCancelToken], Any]]):
    return Supervisor(*args)
