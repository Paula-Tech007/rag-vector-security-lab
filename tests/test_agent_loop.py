import sys
from pathlib import Path
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

import agente_soc


@patch("agente_soc.consultar_agente_ollama")
@patch("agente_soc.executar_tool")
def test_agent_loop_tool_e_resposta_final(
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
                            "pergunta": "Analise o phishing"
                        },
                    }
                }
            ],
        },
        {
            "role": "assistant",
            "content": (
                "O contexto recuperado indica uma tentativa "
                "de phishing contra funcionarios."
            ),
        },
    ]

    mock_executar_tool.return_value = {
        "status": "ok",
        "resposta": "Contexto encontrado.",
        "contextos": [
            "Foi detectada uma tentativa de phishing "
            "contra funcionarios."
        ],
    }

    resultado = agente_soc.executar_agent_loop(
        "Analise o phishing"
    )

    assert mock_consultar.call_count == 2

    mock_executar_tool.assert_called_once_with(
        "consultar_rag",
        {"pergunta": "Analise o phishing"},
    )

    assert resultado["status"] == "ok"
    assert resultado["ferramenta"] == "consultar_rag"
    assert resultado["resposta"] == (
        "O contexto recuperado indica uma tentativa "
        "de phishing contra funcionarios."
    )


@patch("agente_soc.consultar_agente_ollama")
def test_agent_loop_sem_tool(mock_consultar):
    mock_consultar.return_value = {
        "role": "assistant",
        "content": "Ola!",
        "tool_calls": [],
    }

    resultado = agente_soc.executar_agent_loop(
        "Ola"
    )

    assert mock_consultar.call_count == 1
    assert resultado["status"] == "sem_acao"
    assert resultado["ferramenta"] == "nenhuma"
    assert resultado["resposta"] == "Ola!"


@patch("agente_soc.consultar_agente_ollama")
@patch("agente_soc.executar_tool")
def test_agent_loop_nao_executa_segunda_tool(
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
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "consultar_rag",
                        "arguments": {
                            "pergunta": "Outra consulta"
                        },
                    }
                }
            ],
        },
    ]

    mock_executar_tool.return_value = {
        "status": "ok",
        "resposta": "Resultado da ferramenta.",
        "contextos": ["Contexto recuperado."],
    }

    resultado = agente_soc.executar_agent_loop(
        "Analise phishing"
    )

    assert mock_executar_tool.call_count == 1
    assert resultado["status"] == "limite"
    assert resultado["ferramenta"] == "consultar_rag"
