"""MyCLI main entry point."""
import click
from .processor import process_data

@click.command()
@click.option("--name", default="World")
def cli(name: str) -> None:
    result = process_data(name)
    print(result)

if __name__ == "__main__":
    cli()
