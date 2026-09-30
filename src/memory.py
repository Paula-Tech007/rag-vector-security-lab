"""Memoria de sessao para o agente SOC."""

from copy import deepcopy


class SessionMemory:
    """Mantem historicos independentes por session_id."""

    def __init__(self):
        self._sessions = {}

    def adicionar(
        self,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        """Adiciona uma mensagem ao historico da sessao."""
        self._validar_session_id(session_id)

        if role not in {"user", "assistant", "tool"}:
            raise ValueError("Role invalida.")

        if not isinstance(content, str) or not content.strip():
            raise ValueError("Content deve ser texto nao vazio.")

        mensagem = {
            "role": role,
            "content": content.strip(),
        }

        self._sessions.setdefault(
            session_id,
            [],
        ).append(mensagem)

    def obter_historico(
        self,
        session_id: str,
    ) -> list:
        """Retorna uma copia do historico da sessao."""
        self._validar_session_id(session_id)

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
        self._validar_session_id(session_id)

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
            self.obter_historico(session_id)
        )

    @staticmethod
    def _validar_session_id(
        session_id: str,
    ) -> None:
        if (
            not isinstance(session_id, str)
            or not session_id.strip()
        ):
            raise ValueError(
                "session_id deve ser texto nao vazio."
            )
