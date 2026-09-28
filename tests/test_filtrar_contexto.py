import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from rag import filtrar_contexto


def test_filtrar_contexto_mantem_apenas_resultados_confiaveis():
    resultados = [
        (101, "Documento abaixo do threshold", 0.59),
        (102, "Documento exatamente no threshold", 0.60),
        (103, "Documento acima do threshold", 0.85),
    ]

    resultado = filtrar_contexto(resultados)

    assert resultado == [
        (102, "Documento exatamente no threshold", 0.60),
        (103, "Documento acima do threshold", 0.85),
    ]


def test_filtrar_contexto_retorna_lista_vazia_sem_contexto_confiavel():
    resultados = [
        (201, "Documento A", 0.10),
        (202, "Documento B", 0.59),
    ]

    resultado = filtrar_contexto(resultados)

    assert resultado == []