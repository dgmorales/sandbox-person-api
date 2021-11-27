#!/usr/bin/env python

import typer
from bradocs4py import GeradorCpf


def main(
    count: int = typer.Option(1, "--count", "-c", help="How many CPFs to generate")
):
    for i in range(count):
        cpf = GeradorCpf.gerar()
        typer.echo(cpf)


if __name__ == "__main__":
    typer.run(main)
