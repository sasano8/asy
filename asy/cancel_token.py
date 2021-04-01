from typing import  Protocol

class PCancelToken(Protocol):
    is_canceled: bool


class CancelToken(PCancelToken):
    is_canceled: bool

    def __init__(self):
        self.is_canceled = False



