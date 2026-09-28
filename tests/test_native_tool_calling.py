import sys
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import agente_soc


def test_extrair_tool_call_consultar_rag():
    mensagem = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "consultar_rag",
                    "arguments": {
                        "pergunta": "Analise este incidente de phishing"
                    },
                }
            }
        ],
    }

    resultado = agente_soc.extrair_tool_call(mensagem)

    assert resultado == (
        "consultar_rag",
        {"pergunta": "Analise este incidente de phishing"},
    )


def test_extrair_tool_call_sem_ferramenta():
    mensagem = {
        "role": "assistant",
        "content": "Nenhuma ferramenta e necessaria.",
    }

    assert agente_soc.extrair_tool_call(mensagem) is None


@patch("agente_soc.executar_rag")
def test_executar_tool_consultar_rag(mock_rag):
    mock_rag.return_value = {
        "status": "ok",
        "resposta": "Contexto encontrado.",
        "contextos": ["Documento de teste"],
    }

    resultado = agente_soc.executar_tool(
        "consultar_rag",
        {
            "pergunta": "Analise este incidente de phishing",
        },
    )

    mock_rag.assert_called_once_with(
        "Analise este incidente de phishing"
    )

    assert resultado["status"] == "ok"
    assert resultado["resposta"] == "Contexto encontrado."


def test_executar_tool_bloqueia_ferramenta_desconhecida():
    resultado = agente_soc.executar_tool(
        "executar_comando",
        {"comando": "qualquer coisa"},
    )

    assert resultado["status"] == "erro"
    assert resultado["ferramenta"] == "nao_permitida"
