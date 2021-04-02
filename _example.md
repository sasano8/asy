# example

``` python
import asyncio
import asy

async def func1(token: asy.PCancelToken):
    while True:
        if token.is_canceled:
            break
        await asyncio.sleep(1)


async def func2(token: asy.PCancelToken):
    ...


asy.run(func1, func2)
```

``` python
import asyncio
import asy


class CountTask:
    def __init__(self, count: int = 0):
        self.count = count

    async def __call__(self, token: asy.PCancelToken):
        count = self.count

        while True:
            if token.is_canceled:
                break

            print(count)
            await asyncio.sleep(1)
            count += 1


asy.run(CountTask(1))
```

``` python
@asy.Task
class CountTask:
    def __init__(self, count: int = 0):
        self.count = count

    async def __call__(self, token: asy.PCancelToken):
        count = self.count

        while True:
            if token.is_canceled:
                break

            print(count)
            await asyncio.sleep(1)
            count += 1

CountTask.run(1)
```

``` python
import asyncio
import asy
from fastapi import Fastapi


async def func1(token: asy.PCancelToken):
    while True:
        if token.is_canceled:
            break
        await asyncio.sleep(1)

superviser = asy.supervise(func1)

@app.on_event("startup")
async def startup_worker():
    await superviser.start()

@app.on_event("shutdown")
async def shutdown_worker():
    await superviser.stop()
```

``` python
import asyncio
import asy
from fastapi import Fastapi


async def func1(token: asy.PCancelToken):
    while True:
        if token.is_canceled:
            break
        await asyncio.sleep(1)


@app.on_event("startup")
async def startup_worker():
    await asy.schedule(func1)
```

``` shell
# execute func1
python3 -m asy sample:func1

# execute func1 and observe src and reload
python3 -m asy --reload sample:func1

# multipule execute
python3 -m asy sample:func1 sample:func2

# execute task
python3 -m asy --task sample:CountTask -count=1
```

``` python
import typer
import asy


@asy.Task
class CountTask:
    def __init__(self, count: int = 0):
        self.count = count

    async def __call__(self, token: asy.PCancelToken):
        count = self.count

        while True:
            if token.is_canceled:
                break

            print(count)
            await asyncio.sleep(1)
            count += 1


app = typer.Typer()
app.command()(CountTask.run)
```

``` python
import asy

superviser = asy.supervise(func1, func2)

# 処理を逐次的に実行する
for result in superviser:
    print(result)


# 非同期に処理を逐次的に実行する
async for result in superviser:
    print(result)
```

``` python
async def main():
    # trioを参考
    async with asy.scoped() as scoped:
        future1 = scoped.schedule(func1)
        await scoped.run(func2)
        future2 =scoped.schedule(func3)
```

``` python
asy.supervise(func1, func2).sub(fun3, func4)
```
