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


def executar_agente(entrada: str) -> dict:
    """Executa uma decisao simples de agente e chama a ferramenta adequada."""
    entrada = entrada.strip()

    if not entrada:
        return {
            "status": "erro",
            "ferramenta": "nenhuma",
            "resposta": "Entrada vazia.",
        }

    ferramenta = decidir_ferramenta(entrada)

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
