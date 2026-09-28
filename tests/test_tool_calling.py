import sys
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[1] / "src"),
)

import agente_soc


def test_decidir_ferramenta_com_modelo_escolhe_rag():
    consultar = Mock(return_value='{"ferramenta": "rag"}')

    resultado = agente_soc.decidir_ferramenta_com_modelo(
        "Analise este incidente de phishing",
        consultar_modelo=consultar,
    )

    assert resultado == "rag"
    consultar.assert_called_once()


def test_decidir_ferramenta_com_modelo_escolhe_nenhuma():
    consultar = Mock(return_value='{"ferramenta": "nenhuma"}')

    resultado = agente_soc.decidir_ferramenta_com_modelo(
        "Qual e a capital do Brasil?",
        consultar_modelo=consultar,
    )

    assert resultado == "nenhuma"


def test_decidir_ferramenta_com_modelo_fallback_resposta_invalida():
    consultar = Mock(return_value="resposta inesperada")

    resultado = agente_soc.decidir_ferramenta_com_modelo(
        "Analise um incidente de ransomware",
        consultar_modelo=consultar,
    )

    assert resultado == "rag"
