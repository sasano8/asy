import asyncio
import os
from pathlib import Path
from asy.exceptions import RestartAllException


class Reloader:
    def __init__(self, reload_dirs, exclude_dirs=[".venv", "__pypackages__"]):
        self.reload_dirs = reload_dirs

    async def __call__(self):
        reload_dirs = self.reload_dirs
        mtimes = {}
        interval = 1

        while True:
            mtimes = raise_restart_if_file_changed(mtimes, reload_dirs)
            await asyncio.sleep(interval)


def iter_py_files(reload_dirs):
    for reload_dir in reload_dirs:
        for subdir, dirs, files in os.walk(reload_dir):
            for file in files:
                if file.endswith(".py"):
                    name = subdir + os.sep + file
                    yield name


def raise_restart_if_file_changed(mtimes: dict, reload_dirs):
    for filename in iter_py_files(reload_dirs):
        try:
            mtime = os.path.getmtime(filename)
        except OSError:  # pragma: nocover
            continue

        old_time = mtimes.get(filename)
        if old_time is None:
            mtimes[filename] = mtime
            continue
        elif mtime > old_time:
            display_path = os.path.normpath(filename)
            if Path.cwd() in Path(filename).parents:
                display_path = os.path.normpath(os.path.relpath(filename))
            raise RestartAllException(f"Detected file change in '{display_path}'")

    return mtimes
