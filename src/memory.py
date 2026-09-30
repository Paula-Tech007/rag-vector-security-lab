"""Backends de memoria para o agente SOC."""

from abc import ABC, abstractmethod
from copy import deepcopy

import psycopg


ROLES_VALIDAS = {
    "user",
    "assistant",
    "tool",
}


class MemoryBackend(ABC):
    """Contrato comum para backends de memoria do agente."""

    @abstractmethod
    def adicionar(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Adiciona uma mensagem ao historico."""

    @abstractmethod
    def obter_historico(
        self,
        session_id: str,
    ) -> list:
        """Retorna o historico de uma sessao."""

    @abstractmethod
    def limpar(
        self,
        session_id: str,
    ) -> None:
        """Remove o historico de uma sessao."""

    @abstractmethod
    def tamanho(
        self,
        session_id: str,
    ) -> int:
        """Retorna a quantidade de mensagens da sessao."""

    @staticmethod
    def _validar_session_id(
        session_id: str,
    ) -> None:
        """Valida o identificador da sessao."""
        if (
            not isinstance(session_id, str)
            or not session_id.strip()
        ):
            raise ValueError(
                "session_id deve ser texto nao vazio."
            )

    @staticmethod
    def _validar_mensagem(
        role: str,
        content: str,
    ) -> None:
        """Valida role e conteudo da mensagem."""
        if role not in ROLES_VALIDAS:
            raise ValueError(
                "Role invalida."
            )

        if (
            not isinstance(content, str)
            or not content.strip()
        ):
            raise ValueError(
                "Content deve ser texto nao vazio."
            )


class SessionMemory(MemoryBackend):
    """Mantem historicos em memoria RAM por session_id."""

    def __init__(self):
        self._sessions = {}

    def adicionar(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Adiciona uma mensagem ao historico da sessao."""
        self._validar_session_id(
            session_id
        )

        self._validar_mensagem(
            role,
            content,
        )

        session_id = session_id.strip()

        mensagem = {
            "role": role,
            "content": content.strip(),
        }

        self._sessions.setdefault(
            session_id,
            [],
        ).append(
            mensagem
        )

    def obter_historico(
        self,
        session_id: str,
    ) -> list:
        """Retorna uma copia do historico da sessao."""
        self._validar_session_id(
            session_id
        )

        session_id = session_id.strip()

        return deepcopy(
            self._sessions.get(
                session_id,
                [],
            )
        )

    def limpar(
        self,
        session_id: str,
    ) -> None:
        """Remove toda a memoria de uma sessao."""
        self._validar_session_id(
            session_id
        )

        session_id = session_id.strip()

        self._sessions.pop(
            session_id,
            None,
        )

    def tamanho(
        self,
        session_id: str,
    ) -> int:
        """Retorna a quantidade de mensagens da sessao."""
        return len(
            self.obter_historico(
                session_id
            )
        )


class PostgresMemory(MemoryBackend):
    """Persiste historicos do agente no PostgreSQL."""

    def __init__(
        self,
        db_config: dict,
    ):
        if not isinstance(
            db_config,
            dict,
        ):
            raise ValueError(
                "db_config deve ser um dicionario."
            )

        self.db_config = dict(
            db_config
        )

        self._criar_tabela()

    def _conectar(self):
        """Cria uma conexao com PostgreSQL."""
        return psycopg.connect(
            **self.db_config
        )

    def _criar_tabela(
        self,
    ) -> None:
        """Cria tabela e indice caso ainda nao existam."""
        with self._conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS agent_memory (
                        id BIGSERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        role TEXT NOT NULL
                            CHECK (
                                role IN (
                                    'user',
                                    'assistant',
                                    'tool'
                                )
                            ),
                        content TEXT NOT NULL,
                        created_at TIMESTAMPTZ
                            NOT NULL
                            DEFAULT CURRENT_TIMESTAMP
                    );
                    """
                )

                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                        idx_agent_memory_session_id_id
                    ON agent_memory (
                        session_id,
                        id
                    );
                    """
                )

    def adicionar(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Persiste uma mensagem no PostgreSQL."""
        self._validar_session_id(
            session_id
        )

        self._validar_mensagem(
            role,
            content,
        )

        session_id = session_id.strip()
        content = content.strip()

        with self._conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO agent_memory (
                        session_id,
                        role,
                        content
                    )
                    VALUES (
                        %s,
                        %s,
                        %s
                    );
                    """,
                    (
                        session_id,
                        role,
                        content,
                    ),
                )

    def obter_historico(
        self,
        session_id: str,
    ) -> list:
        """Recupera o historico persistido da sessao."""
        self._validar_session_id(
            session_id
        )

        session_id = session_id.strip()

        with self._conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        role,
                        content
                    FROM agent_memory
                    WHERE session_id = %s
                    ORDER BY id ASC;
                    """,
                    (
                        session_id,
                    ),
                )

                registros = (
                    cursor.fetchall()
                )

        return [
            {
                "role": role,
                "content": content,
            }
            for role, content in registros
        ]

    def limpar(
        self,
        session_id: str,
    ) -> None:
        """Remove o historico persistido de uma sessao."""
        self._validar_session_id(
            session_id
        )

        session_id = session_id.strip()

        with self._conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    DELETE FROM agent_memory
                    WHERE session_id = %s;
                    """,
                    (
                        session_id,
                    ),
                )

    def tamanho(
        self,
        session_id: str,
    ) -> int:
        """Conta as mensagens persistidas da sessao."""
        self._validar_session_id(
            session_id
        )

        session_id = session_id.strip()

        with self._conectar() as conexao:
            with conexao.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT COUNT(*)
                    FROM agent_memory
                    WHERE session_id = %s;
                    """,
                    (
                        session_id,
                    ),
                )

                resultado = (
                    cursor.fetchone()
                )

        return int(
            resultado[0]
        )