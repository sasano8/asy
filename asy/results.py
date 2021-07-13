import asyncio
from typing import Sequence, Iterator, Union, Coroutine, Literal, Any
from typing import TypedDict


class Result(TypedDict):
    name: str
    state: Literal["succeed", "failed", "cancelled", "pending"]
    coro: Coroutine
    exception: Union[Exception, None]
    result: Any

    @staticmethod
    def from_task(task: asyncio.Task):
        if task.done():
            if task.cancelled():
                state = "cancelled"
            else:
                if task.exception():
                    state = "failed"
                else:
                    state = "succeed"
        else:
            state = "pending"

        # TODO: エラー発生時にトレースバックを取得しないといけない
        if state == "failed":
            e = task.exception()
            exception = repr(e)
        else:
            exception = None

        return Result(
            name=task.get_name(),
            state=state,  # type: ignore
            coro=task.get_coro().__qualname__,
            exception=exception,
            result=task.result() if state == "succeed" else None,
        )


class Results(Sequence[Result]):
    def __init__(self, tasks):
        self.tasks = tasks
        groups = {
            "succeed": [],
            "failed": [],
            "cancelled": [],
            "pending": [],
        }
        for task in tasks:
            groups[task["state"]].append(task)

        self.groups = groups

    @staticmethod
    def from_tasks(tasks):
        tasks = tuple(Result.from_task(x) for x in tasks)
        return Results(tasks)

    def __str__(self):
        return str(self.groups)

    def __repr__(self):
        return repr(f"{self.__class__.__name__}({self.tasks!r})")

    def print(self):
        print("\n".join(self.format()))

    def format(self, formatter=None):
        formatter = formatter or self._format
        for task in self.tasks:
            yield formatter(task)

    @staticmethod
    def _format(task):
        map_state = {
            "succeed": "SUCCESS",
            "failed": "ERROR",
            "cancelled": "CANCEL",
            "pending": "PENDING",
        }
        state = map_state[task["state"]]
        name = task["name"]
        coro = task["coro"]
        exception = task["exception"]
        result = task["result"]
        return f"[{state}]{coro=} {result=} {exception=}"

    def __getitem__(self, index):
        return self.tasks[index]

    def __len__(self):
        return len(self.tasks)

    def __iter__(self) -> Iterator[Result]:
        yield from self.tasks

    def filter(
        self,
        *,
        pending: bool = True,
        succeed: bool = True,
        failed: bool = True,
        cancelled: bool = True,
    ) -> Iterator[asyncio.Task]:
        if pending:
            yield from self.groups["pending"]
        if succeed:
            yield from self.groups["succeed"]
        if failed:
            yield from self.groups["failed"]
        if cancelled:
            yield from self.groups["cancelled"]

    def group_by(
        self,
        *,
        pending: bool = True,
        succeed: bool = True,
        failed: bool = True,
        cancelled: bool = True,
    ):
        groups = {**self.groups}

        if not succeed:
            del groups["succeed"]

        if not failed:
            del groups["failed"]

        if not cancelled:
            del groups["cancelled"]

        if not pending:
            del groups["pending"]

        return groups
