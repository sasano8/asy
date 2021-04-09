# dont inherit asyncio.CancelledError
class RestartAllException(Exception):
    pass
