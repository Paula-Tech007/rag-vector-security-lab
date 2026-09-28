"""Agente SOC inicial para demonstrar decisao e uso de ferramentas."""

from rag import executar_rag


PALAVRAS_RAG = {
    "phishing",
    "firewall",
    "ransomware",
    "malware",
    "incidente",
    "vulnerabilidade",
    "ataque",
    "ameaca",
    "ameaça",
    "ioc",
}


def decidir_ferramenta(entrada: str) -> str:
    """Decide qual ferramenta o agente deve utilizar."""
    texto = entrada.lower()

    if any(palavra in texto for palavra in PALAVRAS_RAG):
        return "rag"

    return "nenhuma"


def decidir_ferramenta_com_modelo(
    entrada: str,
    consultar_modelo=None,
) -> str:
    """Usa o LLM para escolher a ferramenta, com fallback deterministico."""
    import json

    if consultar_modelo is None:
        from rag import consultar_ollama
        consultar_modelo = consultar_ollama

    prompt = f"""
Voce e um roteador de ferramentas de um agente SOC.

Ferramentas disponiveis:
- rag: consultar a base de conhecimento de seguranca cibernetica.
- nenhuma: quando a entrada nao precisa consultar essa base.

Responda SOMENTE com JSON valido, sem explicacoes.

Formato:
{{"ferramenta": "rag"}}
ou
{{"ferramenta": "nenhuma"}}

Entrada:
{entrada}
""".strip()

    try:
        resposta = consultar_modelo(prompt)
        dados = json.loads(resposta)
        ferramenta = dados.get("ferramenta")

        if ferramenta in {"rag", "nenhuma"}:
            return ferramenta

    except (json.JSONDecodeError, TypeError, AttributeError):
        pass

    return decidir_ferramenta(entrada)

def executar_agente(entrada: str) -> dict:
    """Executa uma decisao simples de agente e chama a ferramenta adequada."""
    entrada = entrada.strip()

    if not entrada:
        return {
            "status": "erro",
            "ferramenta": "nenhuma",
            "resposta": "Entrada vazia.",
        }

    ferramenta = decidir_ferramenta_com_modelo(entrada)

    if ferramenta == "rag":
        resultado = executar_rag(entrada)

        return {
            "status": resultado["status"],
            "ferramenta": "rag",
            "resposta": resultado["resposta"],
            "contextos": resultado["contextos"],
        }

    return {
        "status": "sem_acao",
        "ferramenta": "nenhuma",
        "resposta": "Nenhuma ferramenta foi necessaria.",
    }


def main():
    entrada = input("Evento ou pergunta para o agente SOC: ").strip()

    resultado = executar_agente(entrada)

    print("\n=== DECISAO DO AGENTE ===")
    print(f"Ferramenta: {resultado['ferramenta']}")
    print(f"Status: {resultado['status']}")
    print(f"Resposta: {resultado['resposta']}")


if __name__ == "__main__":
    main()
