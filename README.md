# asy
[![Version](https://img.shields.io/pypi/v/asy)](https://pypi.org/project/asy)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`asy` is easy and powerful supervisor for `asyncio`.

# Motivation for development

- Simple cancellation
- Improve the coordination of async functions between libraries
- No more programs for execution management
- Develop specifications like ASGI

# Requirement

- Python 3.8+

# Installation

``` shell
pip install asy
```

# Getting started

Create functions in `example.py`:

All you have to do is say the magic word `token`, and you can handle the function's lifetime at will.

``` python
import asyncio

# cancelable infinity loop
async def func1(token):
    while not token.is_cancelled:
        await asyncio.sleep(1)
    return "complete func1."


# uncancelable limited loop
async def func2(token):
    for i in range(10):
        await asyncio.sleep(1)
    return f"complete func2.  result: {i}"


# force cancel infinity loop
async def func3():
    while True:
        await asyncio.sleep(1)
    return "complete func3. unreachable code."


# uncancelable limited loop
def func4():
    for i in range(1000):
        ...
    return f"complete func4.  result: {i}"


# Control cancellation by asyncio.CancelledError instead of cancel token.
async def func5():
    try:
        while True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print("occured asyncio.CancelledError.")


# from callable
class YourDeamon:
    def __init__(self, value):
        self.value = value

    async def __call__(self, token):
        value = self.value

        while not token.is_cancelled:
            await asyncio.sleep(1)
        return f"complete func5.  result: {value}"

func6 = YourDeamon(1)

# Do not run
# infinity loop
# async def func7():
#     while True:
#         print("waiting")
```

Run in shell.

``` shell
python3 -m asy example:func1 example:func2 example:func3 example:func4 example:func5 example:func6
```

Run in Python script.

``` python
import asy
from example import func1, func2, func3, func4, func5, func6

supervisor = asy.supervise(func1, func2, func3, func4, func5, func6)
supervisor.run()

# or
asy.run(func1, func2, func3, func4, func5, func6)
```

Run in event loop.

``` python
import asyncio
import asy
from example import func1, func2, func3, func4, func5, func6

async def main():
    supervisor = asy.supervise(func1, func2, func3, func4, func5, func6)
    await supervisor.start()
    await asyncio.sleep(10)
    await supervisor.stop()

asyncio.run(main())
```


Let's end the daemon with `Ctrl-C` and enjoy `asy`!

# What is token?

By defining token in the argument of the function, the function is `async.shield` and `asyncio.CancelledError` is suppressed.

The supervisor sets `True` to `token.is_cancelled` when it detects a cancellation.

# Caution
`asy` is a beta version. Please do not use it in production.

