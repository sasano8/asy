import asy
from asy.components import Reloader
from asy.components.reloader import iter_py_files
import asyncio


def test_iter_py_files(tmp_path):
    d = tmp_path / "reload"
    d.mkdir()
    p = d / "hello.py"
    p.write_text("1")

    result = list(iter_py_files([str(d)]))
    assert result
    assert result[0] == str(d) + "/hello.py"


def test_reloader(tmp_path):
    d = tmp_path / "reload"
    d.mkdir()

    async def update_file():
        p = d / "hello.py"
        p.write_text("1")
        await asyncio.sleep(1)
        p.write_text("2")

    count = 0

    def countup():
        nonlocal count
        count += 1
        if count == 2:
            raise asy.AllCancelException()

    result = asy.supervise(
        asy.timeout(3), update_file, countup, Reloader([str(d)])
    ).run()

    assert result
    assert count == 2
