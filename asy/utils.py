import inspect


def is_coroutine_callable(target):
    if inspect.iscoroutinefunction(target):
        return True

    if func := getattr(target, "__call__", None):
        return inspect.iscoroutinefunction(func)
    else:
        return False
