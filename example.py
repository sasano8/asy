import asyncio

# cancelable infinity loop
async def func1(token):
    while not token.is_cancelled:
        await asyncio.sleep(1)
    raise asyncio.CancelledError()
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


# from callable
class YourDeamon:
    def __init__(self, value):
        self.value = value

    async def __call__(self, token):
        value = self.value

        while not token.is_cancelled:
            await asyncio.sleep(1)
        return f"complete func5.  result: {value}"


func5 = YourDeamon(1)

# Do not run
# infinity loop
# async def func5():
#     while True:
#         print("waiting")