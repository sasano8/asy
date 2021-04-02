# asy
[![Version](https://img.shields.io/pypi/v/asy)](https://pypi.org/project/asy)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

`asy` is easy and powerful for `asyncio`.

# Motivation for development

- Simple cancellation
- Improve the coordination of async functions between libraries
- No more programs for execution management
- Develop specifications like ASGI


# Installation

``` shell
pip install asy
```

# Getting started

Create deamons, in `example.py`:

``` python
import asyncio

# cancelable limited loop
async def func1(token):
    for i in range(10):
        if token.is_cancelled:
            break
        print("waiting")
        await asyncio.sleep(1)
    print("complete func2.")

# cancelable infinity loop
async def func2():
    while True:
        print("waiting")
        await asyncio.sleep(1)

# uncancelable limited loop
def func3():
    for i in range(1000):
        print(i)

# from callable
class YourDeamon:
    async def __call__(self, token):
        while not token.is_cancelled:
            await asyncio.sleep(1)
        print("complete.")

func4 = YourDeamon()


# Do not run
# infinity loop
# async def func5()):
#     while True:
#         print("waiting")
```

Run in shell.

``` shell
python3 -m asy example:func1 example:func2 example:func3 example:func4
```

Run in Python script.

``` python
import asy
from example import func1, func2, func3, func4

supervisor = asy.supervise(func1, func2, func3, func4)
supervisor.run()

# or
asy.run(func1, func2, func3, func4)
```


Let's end the daemon with `Ctrl-C` and enjoy `asy`!

# Caution
`asy` is a beta version. Please do not use it in production.
