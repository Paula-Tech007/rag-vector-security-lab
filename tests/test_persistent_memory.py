"""Testes da memoria persistente PostgreSQL."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


SRC_DIR = Path(__file__).resolve().parents[1] / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(SRC_DIR),
    )


from memory import (
    MemoryBackend,
    PostgresMemory,
)


DB_CONFIG_TESTE = {
    "host": "localhost",
    "port": 5432,
    "dbname": "rag_security",
    "user": "rag_user",
    "password": "teste",
}


def criar_memory_mock():
    """Cria PostgresMemory usando conexao PostgreSQL simulada."""
    patcher = patch(
        "memory.psycopg.connect"
    )

    connect = patcher.start()

    conexao = MagicMock()
    cursor = MagicMock()

    connect.return_value.__enter__.return_value = (
        conexao
    )

    conexao.cursor.return_value.__enter__.return_value = (
        cursor
    )

    memory = PostgresMemory(
        DB_CONFIG_TESTE
    )

    return (
        memory,
        connect,
        cursor,
        patcher,
    )


def test_postgres_memory_implementa_backend():
    memory, _, _, patcher = (
        criar_memory_mock()
    )

    try:
        assert isinstance(
            memory,
            MemoryBackend,
        )

        assert isinstance(
            memory,
            PostgresMemory,
        )
    finally:
        patcher.stop()


def test_postgres_memory_cria_tabela():
    memory, connect, cursor, patcher = (
        criar_memory_mock()
    )

    try:
        assert isinstance(
            memory,
            PostgresMemory,
        )

        assert connect.called

        assert (
            cursor.execute.call_count
            >= 2
        )
    finally:
        patcher.stop()


def test_postgres_memory_adiciona_mensagem():
    memory, _, cursor, patcher = (
        criar_memory_mock()
    )

    try:
        cursor.reset_mock()

        memory.adicionar(
            "SOC-001",
            "user",
            "Incidente de phishing.",
        )

        cursor.execute.assert_called_once()

        argumentos = (
            cursor.execute.call_args.args[1]
        )

        assert argumentos == (
            "SOC-001",
            "user",
            "Incidente de phishing.",
        )
    finally:
        patcher.stop()


def test_postgres_memory_recupera_historico():
    memory, _, cursor, patcher = (
        criar_memory_mock()
    )

    try:
        cursor.reset_mock()

        cursor.fetchall.return_value = [
            (
                "user",
                "Incidente de phishing.",
            ),
            (
                "assistant",
                "Contexto registrado.",
            ),
        ]

        historico = (
            memory.obter_historico(
                "SOC-001"
            )
        )

        assert historico == [
            {
                "role": "user",
                "content": (
                    "Incidente de phishing."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Contexto registrado."
                ),
            },
        ]
    finally:
        patcher.stop()


def test_postgres_memory_preserva_ordem():
    memory, _, cursor, patcher = (
        criar_memory_mock()
    )

    try:
        cursor.reset_mock()

        cursor.fetchall.return_value = [
            (
                "user",
                "Primeira mensagem.",
            ),
            (
                "assistant",
                "Segunda mensagem.",
            ),
            (
                "user",
                "Terceira mensagem.",
            ),
        ]

        historico = (
            memory.obter_historico(
                "SOC-ORDEM"
            )
        )

        assert historico == [
            {
                "role": "user",
                "content": (
                    "Primeira mensagem."
                ),
            },
            {
                "role": "assistant",
                "content": (
                    "Segunda mensagem."
                ),
            },
            {
                "role": "user",
                "content": (
                    "Terceira mensagem."
                ),
            },
        ]
    finally:
        patcher.stop()


def test_postgres_memory_limpa_sessao():
    memory, _, cursor, patcher = (
        criar_memory_mock()
    )

    try:
        cursor.reset_mock()

        memory.limpar(
            "SOC-001"
        )

        cursor.execute.assert_called_once()

        argumentos = (
            cursor.execute.call_args.args[1]
        )

        assert argumentos == (
            "SOC-001",
        )
    finally:
        patcher.stop()


def test_postgres_memory_conta_mensagens():
    memory, _, cursor, patcher = (
        criar_memory_mock()
    )

    try:
        cursor.reset_mock()

        cursor.fetchone.return_value = (
            4,
        )

        tamanho = memory.tamanho(
            "SOC-001"
        )

        assert tamanho == 4
    finally:
        patcher.stop()


def test_postgres_memory_rejeita_session_id_vazio():
    memory, _, _, patcher = (
        criar_memory_mock()
    )

    try:
        with pytest.raises(
            ValueError,
            match="session_id",
        ):
            memory.obter_historico(
                ""
            )
    finally:
        patcher.stop()


def test_postgres_memory_rejeita_role_invalida():
    memory, _, _, patcher = (
        criar_memory_mock()
    )

    try:
        with pytest.raises(
            ValueError,
            match="Role invalida",
        ):
            memory.adicionar(
                "SOC-001",
                "admin",
                "Mensagem",
            )
    finally:
        patcher.stop()


def test_postgres_memory_rejeita_content_vazio():
    memory, _, _, patcher = (
        criar_memory_mock()
    )

    try:
        with pytest.raises(
            ValueError,
            match="Content",
        ):
            memory.adicionar(
                "SOC-001",
                "user",
                "",
            )
    finally:
        patcher.stop()
        



