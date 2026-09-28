import sys
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import agente_soc


def test_decidir_ferramenta_para_phishing():
    assert agente_soc.decidir_ferramenta(
        "Analise um incidente de phishing"
    ) == "rag"


def test_decidir_ferramenta_para_conversa_comum():
    assert agente_soc.decidir_ferramenta(
        "Ola, tudo bem?"
    ) == "nenhuma"


def test_executar_agente_com_entrada_vazia():
    resultado = agente_soc.executar_agente("   ")

    assert resultado["status"] == "erro"
    assert resultado["ferramenta"] == "nenhuma"
    assert resultado["resposta"] == "Entrada vazia."


@patch("agente_soc.executar_rag")
def test_executar_agente_chama_rag(mock_executar_rag):
    mock_executar_rag.return_value = {
        "status": "ok",
        "resposta": "Contexto encontrado.",
        "contextos": ["Documento de teste"],
    }

    resultado = agente_soc.executar_agente(
        "Analise este ataque de phishing"
    )

    mock_executar_rag.assert_called_once_with(
        "Analise este ataque de phishing"
    )

    assert resultado["status"] == "ok"
    assert resultado["ferramenta"] == "rag"
    assert resultado["resposta"] == "Contexto encontrado."
    assert resultado["contextos"] == ["Documento de teste"]


def test_executar_agente_sem_ferramenta():
    resultado = agente_soc.executar_agente(
        "Ola, tudo bem?"
    )

    assert resultado["status"] == "sem_acao"
    assert resultado["ferramenta"] == "nenhuma"
