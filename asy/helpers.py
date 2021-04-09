from .supervisor import Supervisor as supervise
from typing import Union, Callable, Any
from .protocols import PCancelToken
from .components.timeout import Timeout


def run(*args: Union[Callable[[], Any], Callable[[PCancelToken], Any]]):
    return supervise(*args).run()


def timeout(timeout):
    return Timeout(timeout)