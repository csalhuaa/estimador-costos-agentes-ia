"""Structured input-error transport for the future M0 loader."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Problema:
    codigo: str
    hoja: str
    celda: str
    mensaje: str


class ErrorDeEntrada(Exception):
    """Preserve every input problem and expose a readable, located message."""

    def __init__(self, problemas: list[Problema]) -> None:
        self.problemas = tuple(problemas)
        super().__init__(
            "\n".join(
                f"[{p.codigo}] Hoja {p.hoja}, celda {p.celda}: {p.mensaje}"
                for p in self.problemas
            )
        )
