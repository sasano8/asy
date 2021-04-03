async def hello():
    import asyncio

    while True:
        print("hello asy!")
        await asyncio.sleep(1)
