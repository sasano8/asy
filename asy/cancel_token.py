from .protocols import PCancelToken


class CancelToken(PCancelToken):
    is_canceled: bool = False

    def __init__(self):
        self.is_canceled = False


class CancelTokenForTask(PCancelToken):
    def __init__(self, task):
        self.task = task

    @property
    def is_canceled(self) -> bool:
        return self.task.canceled()

    @is_canceled.setter
    def is_canceled(self, value: bool):
        if not value:
            self.task.cancel()
