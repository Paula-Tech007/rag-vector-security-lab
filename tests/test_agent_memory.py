import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_DIR),
    )

import agente_soc
from memory import SessionMemory


def test_react_com_memoria_grava_usuario_e_resposta(
    monkeypatch,
):
    memory = SessionMemory()

    def fake_consultar(historico):
        return {
            "role": "assistant",
            "content": "Investigacao iniciada.",
        }

    monkeypatch.setattr(
        agente_soc,
        "consultar_agente_ollama",
        fake_consultar,
    )

    resultado = agente_soc.executar_react_com_memoria(
        "Estamos investigando phishing.",
        "SOC-001",
        memory,
    )

    assert resultado["status"] == "sem_acao"

    assert memory.obter_historico(
        "SOC-001"
    ) == [
        {
            "role": "user",
            "content": "Estamos investigando phishing.",
        },
        {
            "role": "assistant",
            "content": "Investigacao iniciada.",
        },
    ]

    assert resultado["memory_size"] == 2


def test_react_com_memoria_recupera_contexto_anterior(
    monkeypatch,
):
    memory = SessionMemory()

    memory.adicionar(
        "SOC-001",
        "user",
        "Estamos investigando phishing.",
    )

    memory.adicionar(
        "SOC-001",
        "assistant",
        "Investigacao iniciada.",
    )

    historico_recebido = []

    def fake_consultar(historico):
        historico_recebido.extend(
            historico
        )

        return {
            "role": "assistant",
            "content": "Continuando a investigacao.",
        }

    monkeypatch.setattr(
        agente_soc,
        "consultar_agente_ollama",
        fake_consultar,
    )

    resultado = agente_soc.executar_react_com_memoria(
        "Continue a investigacao.",
        "SOC-001",
        memory,
    )

    assert historico_recebido[0] == {
        "role": "user",
        "content": "Estamos investigando phishing.",
    }

    assert historico_recebido[1] == {
        "role": "assistant",
        "content": "Investigacao iniciada.",
    }

    assert historico_recebido[2] == {
        "role": "user",
        "content": "Continue a investigacao.",
    }

    assert resultado["memory_size"] == 4


def test_react_com_memoria_isola_sessoes(
    monkeypatch,
):
    memory = SessionMemory()

    memory.adicionar(
        "SOC-001",
        "user",
        "Incidente de phishing.",
    )

    memory.adicionar(
        "SOC-002",
        "user",
        "Incidente de ransomware.",
    )

    historico_recebido = []

    def fake_consultar(historico):
        historico_recebido.extend(
            historico
        )

        return {
            "role": "assistant",
            "content": "Analise concluida.",
        }

    monkeypatch.setattr(
        agente_soc,
        "consultar_agente_ollama",
        fake_consultar,
    )

    agente_soc.executar_react_com_memoria(
        "Continue.",
        "SOC-001",
        memory,
    )

    conteudos = [
        mensagem["content"]
        for mensagem in historico_recebido
    ]

    assert "Incidente de phishing." in conteudos

    assert (
        "Incidente de ransomware."
        not in conteudos
    )


def test_react_com_memoria_executa_tool(
    monkeypatch,
):
    memory = SessionMemory()

    chamadas = {"total": 0}

    def fake_consultar(historico):
        chamadas["total"] += 1

        if chamadas["total"] == 1:
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "consultar_rag",
                            "arguments": {
                                "pergunta": (
                                    "Como analisar phishing?"
                                )
                            },
                        }
                    }
                ],
            }

        return {
            "role": "assistant",
            "content": (
                "O contexto recuperado foi analisado."
            ),
        }

    def fake_tool(nome, argumentos):
        return {
            "status": "ok",
            "resposta": (
                "Foi detectada tentativa de phishing."
            ),
            "contextos": [
                (
                    "Tentativa de phishing "
                    "contra funcionarios."
                )
            ],
        }

    monkeypatch.setattr(
        agente_soc,
        "consultar_agente_ollama",
        fake_consultar,
    )

    monkeypatch.setattr(
        agente_soc,
        "executar_tool",
        fake_tool,
    )

    resultado = agente_soc.executar_react_com_memoria(
        "Consulte a base sobre phishing.",
        "SOC-001",
        memory,
    )

    assert resultado["status"] == "ok"

    assert resultado["trace"] == [
        {
            "passo": 1,
            "ferramenta": "consultar_rag",
            "argumentos": {
                "pergunta": (
                    "Como analisar phishing?"
                )
            },
            "status": "ok",
        }
    ]

    assert (
        resultado["resposta"]
        == "O contexto recuperado foi analisado."
    )

    assert memory.tamanho(
        "SOC-001"
    ) == 2


def test_react_com_memoria_rejeita_session_id_vazio():
    memory = SessionMemory()

    resultado = agente_soc.executar_react_com_memoria(
        "Teste",
        "",
        memory,
    )

    assert resultado["status"] == "erro"
    assert resultado["resposta"] == (
        "session_id invalido."
    )


def test_react_com_memoria_respeita_limite(
    monkeypatch,
):
    memory = SessionMemory()

    def fake_consultar(historico):
        return {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "function": {
                        "name": "consultar_rag",
                        "arguments": {
                            "pergunta": "Teste"
                        },
                    }
                }
            ],
        }

    def fake_tool(nome, argumentos):
        return {
            "status": "ok",
            "resposta": "resultado",
            "contextos": [],
        }

    monkeypatch.setattr(
        agente_soc,
        "consultar_agente_ollama",
        fake_consultar,
    )

    monkeypatch.setattr(
        agente_soc,
        "executar_tool",
        fake_tool,
    )

    resultado = agente_soc.executar_react_com_memoria(
        "Investigue.",
        "SOC-001",
        memory,
        max_steps=2,
    )

    assert resultado["status"] == "limite"
    assert len(resultado["trace"]) == 2

    assert resultado["memory_size"] == 2
