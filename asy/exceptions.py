# dont inherit asyncio.CancelledError
class RestartAllException(Exception):
    pass


class AllCancelException(Exception):
    pass
