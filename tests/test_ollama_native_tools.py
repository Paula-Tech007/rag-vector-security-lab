import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import agente_soc


def test_schema_registra_consultar_rag():
    ferramentas = agente_soc.FERRAMENTAS_OLLAMA

    assert len(ferramentas) == 1
    assert ferramentas[0]["type"] == "function"
    assert ferramentas[0]["function"]["name"] == "consultar_rag"

    parametros = ferramentas[0]["function"]["parameters"]

    assert parametros["type"] == "object"
    assert "pergunta" in parametros["properties"]
    assert parametros["required"] == ["pergunta"]


@patch("agente_soc.urllib.request.urlopen")
def test_consultar_agente_ollama_envia_tools(mock_urlopen):
    resposta_http = MagicMock()

    resposta_http.read.return_value = json.dumps(
        {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [],
            }
        }
    ).encode("utf-8")

    mock_urlopen.return_value.__enter__.return_value = resposta_http

    mensagem = agente_soc.consultar_agente_ollama(
        "Analise este incidente de phishing"
    )

    requisicao = mock_urlopen.call_args.args[0]

    payload = json.loads(
        requisicao.data.decode("utf-8")
    )

    assert payload["model"] == agente_soc.OLLAMA_MODEL
    assert payload["stream"] is False
    assert payload["tools"] == agente_soc.FERRAMENTAS_OLLAMA

    assert payload["messages"][-1] == {
        "role": "user",
        "content": "Analise este incidente de phishing",
    }

    assert mensagem["role"] == "assistant"


@patch("agente_soc.executar_tool")
@patch("agente_soc.consultar_agente_ollama")
def test_agente_nativo_executa_tool_call(
    mock_consultar,
    mock_executar_tool,
):
    mock_consultar.return_value = {
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

    mock_executar_tool.return_value = {
        "status": "ok",
        "resposta": "Contexto encontrado.",
        "contextos": ["Documento de teste"],
    }

    resultado = agente_soc.executar_agente_nativo(
        "Analise este incidente de phishing"
    )

    mock_executar_tool.assert_called_once_with(
        "consultar_rag",
        {
            "pergunta": "Analise este incidente de phishing",
        },
    )

    assert resultado["status"] == "ok"
    assert resultado["ferramenta"] == "consultar_rag"
    assert resultado["resposta"] == "Contexto encontrado."


@patch("agente_soc.consultar_agente_ollama")
def test_agente_nativo_sem_tool_call(mock_consultar):
    mock_consultar.return_value = {
        "role": "assistant",
        "content": "Nenhuma ferramenta foi necessaria.",
        "tool_calls": [],
    }

    resultado = agente_soc.executar_agente_nativo(
        "Ola, tudo bem?"
    )

    assert resultado["status"] == "sem_acao"
    assert resultado["ferramenta"] == "nenhuma"
    assert resultado["resposta"] == (
        "Nenhuma ferramenta foi necessaria."
    )
