import sys
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import agente_soc


@patch("agente_soc.consultar_agente_ollama")
@patch("agente_soc.executar_tool")
def test_react_executa_tool_e_finaliza(
    mock_executar_tool,
    mock_consultar,
):
    mock_consultar.side_effect = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "consultar_rag",
                        "arguments": {
                            "pergunta": "Analise phishing"
                        },
                    }
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Analise concluida com o contexto recuperado.",
            "tool_calls": [],
        },
    ]

    mock_executar_tool.return_value = {
        "status": "ok",
        "resposta": "Contexto encontrado.",
        "contextos": ["Tentativa de phishing detectada."],
    }

    resultado = agente_soc.executar_react(
        "Analise phishing"
    )

    assert mock_executar_tool.call_count == 1
    assert mock_consultar.call_count == 2

    assert resultado["status"] == "ok"
    assert resultado["resposta"] == (
        "Analise concluida com o contexto recuperado."
    )

    assert len(resultado["trace"]) == 1
    assert resultado["trace"][0]["passo"] == 1
    assert resultado["trace"][0]["ferramenta"] == "consultar_rag"
    assert resultado["trace"][0]["status"] == "ok"


@patch("agente_soc.consultar_agente_ollama")
@patch("agente_soc.executar_tool")
def test_react_permite_multiplos_passos(
    mock_executar_tool,
    mock_consultar,
):
    mock_consultar.side_effect = [
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "consultar_rag",
                        "arguments": {
                            "pergunta": "Primeira consulta"
                        },
                    }
                }
            ],
        },
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "consultar_rag",
                        "arguments": {
                            "pergunta": "Segunda consulta"
                        },
                    }
                }
            ],
        },
        {
            "role": "assistant",
            "content": "Resposta final.",
            "tool_calls": [],
        },
    ]

    mock_executar_tool.side_effect = [
        {
            "status": "ok",
            "resposta": "Resultado 1",
            "contextos": ["Contexto 1"],
        },
        {
            "status": "ok",
            "resposta": "Resultado 2",
            "contextos": ["Contexto 2"],
        },
    ]

    resultado = agente_soc.executar_react(
        "Investigue o incidente"
    )

    assert mock_executar_tool.call_count == 2
    assert mock_consultar.call_count == 3

    assert resultado["status"] == "ok"
    assert resultado["resposta"] == "Resposta final."

    assert len(resultado["trace"]) == 2
    assert resultado["trace"][0]["passo"] == 1
    assert resultado["trace"][1]["passo"] == 2


@patch("agente_soc.consultar_agente_ollama")
@patch("agente_soc.executar_tool")
def test_react_respeita_limite_de_passos(
    mock_executar_tool,
    mock_consultar,
):
    mensagem_tool = {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "function": {
                    "name": "consultar_rag",
                    "arguments": {
                        "pergunta": "Continuar investigacao"
                    },
                }
            }
        ],
    }

    mock_consultar.return_value = mensagem_tool

    mock_executar_tool.return_value = {
        "status": "ok",
        "resposta": "Contexto parcial.",
        "contextos": ["Contexto parcial."],
    }

    resultado = agente_soc.executar_react(
        "Investigue o incidente",
        max_steps=3,
    )

    assert mock_executar_tool.call_count == 3
    assert resultado["status"] == "limite"
    assert len(resultado["trace"]) == 3


@patch("agente_soc.consultar_agente_ollama")
def test_react_sem_tool_responde_diretamente(
    mock_consultar,
):
    mock_consultar.return_value = {
        "role": "assistant",
        "content": "Nenhuma ferramenta foi necessaria.",
        "tool_calls": [],
    }

    resultado = agente_soc.executar_react(
        "Ola"
    )

    assert resultado["status"] == "sem_acao"
    assert resultado["resposta"] == (
        "Nenhuma ferramenta foi necessaria."
    )
    assert resultado["trace"] == []
