import sys
from pathlib import Path

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_DIR),
    )

from memory import SessionMemory


def test_memory_inicia_vazia():
    memory = SessionMemory()

    assert memory.obter_historico("soc-1") == []
    assert memory.tamanho("soc-1") == 0


def test_memory_armazena_mensagens_em_ordem():
    memory = SessionMemory()

    memory.adicionar(
        "soc-1",
        "user",
        "Estamos investigando phishing.",
    )

    memory.adicionar(
        "soc-1",
        "assistant",
        "Investigacao iniciada.",
    )

    assert memory.obter_historico(
        "soc-1"
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


def test_memory_isola_sessoes():
    memory = SessionMemory()

    memory.adicionar(
        "incidente-1",
        "user",
        "Analise phishing.",
    )

    memory.adicionar(
        "incidente-2",
        "user",
        "Analise ransomware.",
    )

    assert memory.tamanho(
        "incidente-1"
    ) == 1

    assert memory.tamanho(
        "incidente-2"
    ) == 1

    assert (
        memory.obter_historico(
            "incidente-1"
        )[0]["content"]
        == "Analise phishing."
    )

    assert (
        memory.obter_historico(
            "incidente-2"
        )[0]["content"]
        == "Analise ransomware."
    )


def test_memory_limpa_somente_sessao_escolhida():
    memory = SessionMemory()

    memory.adicionar(
        "soc-1",
        "user",
        "Phishing",
    )

    memory.adicionar(
        "soc-2",
        "user",
        "Firewall",
    )

    memory.limpar("soc-1")

    assert memory.obter_historico(
        "soc-1"
    ) == []

    assert memory.tamanho(
        "soc-2"
    ) == 1


def test_memory_rejeita_session_id_vazio():
    memory = SessionMemory()

    with pytest.raises(
        ValueError,
        match="session_id",
    ):
        memory.adicionar(
            "",
            "user",
            "teste",
        )


def test_memory_rejeita_role_desconhecida():
    memory = SessionMemory()

    with pytest.raises(
        ValueError,
        match="Role invalida",
    ):
        memory.adicionar(
            "soc-1",
            "admin",
            "teste",
        )


def test_memory_rejeita_content_vazio():
    memory = SessionMemory()

    with pytest.raises(
        ValueError,
        match="Content",
    ):
        memory.adicionar(
            "soc-1",
            "user",
            "   ",
        )


def test_historico_retornado_nao_altera_memoria_original():
    memory = SessionMemory()

    memory.adicionar(
        "soc-1",
        "user",
        "Incidente de phishing.",
    )

    historico = memory.obter_historico(
        "soc-1"
    )

    historico[0]["content"] = "ALTERADO"

    assert (
        memory.obter_historico(
            "soc-1"
        )[0]["content"]
        == "Incidente de phishing."
    )
