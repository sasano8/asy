import typer
from typing import List

app = typer.Typer()


@app.command()
def run(attrs: List[str], reload: bool = False):
    typer.echo(attrs)