import typer
from typing import List
import logging
from asy.components import FileWatcher

app = typer.Typer()


class Reloader:
    def __init__(self, attrs):
        # 指定内容が正しいか一度検証する
        package_modules = {get_package_and_module(x) for x in attrs}
        packages = {x[0] for x in package_modules}
        modules = {x[1] for x in package_modules}

        tmp = set()

        # キャッシュをクリアするためのモジュールリストを構築する
        # TODO: ネストしたモジュールのリロードにも対応したが、おそらく１ネストしかリロードされないと思う
        for module in modules:
            for package, module in enumrate_members(module):
                packages.add(package)
                tmp.add(module)

        for module in tmp:
            modules.add(module)

        packages = {x for x in packages if x}
        modules = {x for x in modules if x}

        excludes = {"asyncio", "asy"}
        packages = {x for x in packages if x not in excludes}

        self.attrs = attrs
        self.packages = packages
        self.modules = modules

    def clear_import(self):
        [clear_cache(x) for x in self.packages]
        [clear_cache(x) for x in self.modules]

    async def __call__(self, token):
        import asy

        callables = [get_module_attr_from_str(x) for x in self.attrs]
        supervisor = asy.supervise(*callables)
        await supervisor(token)
        self.clear_import()

    @classmethod
    def from_functions(cls, *attrs):
        return cls(attrs=attrs)

    @classmethod
    def from_class(cls, target, **kwargs):
        raise NotImplementedError()


@app.command()
def run(attrs: List[str], reload: bool = False, log: str = "INFO"):
    import asy

    logging.basicConfig(level=log)

    sub = []

    if reload:
        sub.append(FileWatcher(["."]))

    reloader = Reloader.from_functions(*attrs)
    asy.supervise(reloader, *sub).run()


def get_module(attr_path: str):
    from importlib import import_module

    module, attr = attr_path.split(":")
    imported_module = import_module(module)
    return imported_module


def clear_cache(package):
    import sys
    import importlib

    # モジュールのリロード
    if package in sys.modules:
        sys.modules.pop(package)


def enumrate_members(module_name):
    import sys

    module = sys.modules[module_name]
    attrs = [getattr(module, attribute) for attribute in dir(module)]
    for attr in attrs:
        package = getattr(attr, "__package__", "")
        module = getattr(attr, "__module__", "")

        if module:
            package = module.split(".")[0]

        yield package, module


def get_package_and_module(attr_path: str):
    module = get_module(attr_path)
    return module.__package__, module.__name__


def get_module_attr_from_str(attr_path: str):
    import sys
    from importlib import import_module

    module, attr = attr_path.split(":")
    imported_module = import_module(module)
    instance = getattr(imported_module, attr)
    return instance
