import typer
from typing import List
import logging
from asy.components import Reloader
import os

app = typer.Typer()


@app.command()
def run(attrs: List[str], reload: bool = False, log: str = "INFO"):
    import asy

    logging.basicConfig(level=log)

    sub = []

    if reload:
        sub.append(Reloader(["."]))

    async def reloader(token):
        callables = [get_module_attr_from_str(x) for x in attrs]
        supervisor = asy.supervise(*callables)
        await supervisor(token)

    asy.supervise(reloader, *sub).run()


def get_module_attr_from_str(attr_path: str):
    import sys
    from importlib import import_module

    module, attr = attr_path.split(":")

    # モジュールのリロード
    if module in sys.modules:
        sys.modules.pop(module)

    imported_module = import_module(module)
    instance = getattr(imported_module, attr)
    return instance
