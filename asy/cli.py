import typer
from typing import List
import logging

app = typer.Typer()


@app.command()
def run(attrs: List[str], reload: bool = False, log: str = "INFO", pipe: bool = False):
    import asy

    logging.basicConfig(level=log)
    callables = [get_module_attr_from_str(x) for x in attrs]
    supervisor = asy.supervise(*callables)
    supervisor.run()


def get_module_attr_from_str(attr_path: str):
    import sys
    from importlib import import_module

    module, attr = attr_path.split(":")

    # モジュールのリロード
    # if module in sys.modules:
    #     sys.modules.pop(module)

    imported_module = import_module(module)
    instance = getattr(imported_module, attr)
    return instance
