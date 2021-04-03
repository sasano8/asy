from .supervisor import Supervisor as supervise
from typing import Union, Callable, Any
from .protocols import PCancelToken


def run(*args: Union[Callable[[], Any], Callable[[PCancelToken], Any]]):
    return supervise(*args).run()
