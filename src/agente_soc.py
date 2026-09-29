"""Agente SOC inicial para demonstrar decisao e uso de ferramentas."""

import json
import urllib.request

from rag import executar_rag


OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen3:4b-instruct"


FERRAMENTAS_OLLAMA = [
    {
        "type": "function",
        "function": {
            "name": "consultar_rag",
            "description": (
                "Consulta a base vetorial de conhecimento de "
                "seguranca cibernetica quando for necessario "
                "contexto tecnico."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "pergunta": {
                        "type": "string",
                        "description": (
                            "Pergunta de seguranca a consultar no RAG."
                        ),
                    }
                },
                "required": ["pergunta"],
            },
        },
    }
]

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

def consultar_agente_ollama(entrada) -> dict:
    """Envia entrada ou historico de mensagens ao Ollama."""
    mensagem_sistema = {
        "role": "system",
        "content": (
            "Voce e um agente SOC. "
            "Use consultar_rag quando precisar consultar "
            "a base de conhecimento de seguranca cibernetica. "
            "Caso receba o resultado de uma ferramenta, use esse "
            "resultado para produzir a resposta final. "
            "Nao invente informacoes que nao estejam no resultado."
        ),
    }

    if isinstance(entrada, list):
        messages = [
            mensagem_sistema,
            *entrada,
        ]
    else:
        messages = [
            mensagem_sistema,
            {
                "role": "user",
                "content": entrada,
            },
        ]

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": FERRAMENTAS_OLLAMA,
        "stream": False,
    }

    dados = json.dumps(payload).encode("utf-8")

    requisicao = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=dados,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        requisicao,
        timeout=120,
    ) as resposta_http:
        resposta_json = json.loads(
            resposta_http.read().decode("utf-8")
        )

    return resposta_json.get("message", {})

def extrair_tool_call(mensagem: dict):
    """Extrai a primeira chamada de ferramenta solicitada pelo modelo."""
    tool_calls = mensagem.get("tool_calls") or []

    if not tool_calls:
        return None

    chamada = tool_calls[0]
    funcao = chamada.get("function") or {}

    nome = funcao.get("name")
    argumentos = funcao.get("arguments") or {}

    if not nome:
        return None

    if isinstance(argumentos, str):
        try:
            import json
            argumentos = json.loads(argumentos)
        except json.JSONDecodeError:
            argumentos = {}

    if not isinstance(argumentos, dict):
        argumentos = {}

    return nome, argumentos


def executar_tool(nome: str, argumentos: dict) -> dict:
    """Executa somente ferramentas explicitamente permitidas pelo agente."""
    if nome != "consultar_rag":
        return {
            "status": "erro",
            "ferramenta": "nao_permitida",
            "resposta": f"Ferramenta nao permitida: {nome}",
        }

    pergunta = argumentos.get("pergunta", "")

    if not isinstance(pergunta, str) or not pergunta.strip():
        return {
            "status": "erro",
            "ferramenta": "consultar_rag",
            "resposta": "Pergunta invalida para consultar_rag.",
        }

    return executar_rag(pergunta.strip())

MAX_REACT_STEPS = 3


def executar_react(
    entrada: str,
    max_steps: int = MAX_REACT_STEPS,
) -> dict:
    """Executa ciclo ReAct controlado com trace operacional."""
    entrada = entrada.strip()

    if not entrada:
        return {
            "status": "erro",
            "resposta": "Entrada vazia.",
            "trace": [],
        }

    if max_steps < 1:
        return {
            "status": "erro",
            "resposta": "max_steps deve ser maior que zero.",
            "trace": [],
        }

    historico = [
        {
            "role": "user",
            "content": entrada,
        }
    ]

    trace = []

    for passo in range(1, max_steps + 1):
        mensagem = consultar_agente_ollama(
            historico
        )

        chamada = extrair_tool_call(
            mensagem
        )

        if chamada is None:
            resposta = (
                mensagem.get("content", "").strip()
                or "Nenhuma ferramenta foi necessaria."
            )

            return {
                "status": (
                    "sem_acao"
                    if not trace
                    else "ok"
                ),
                "resposta": resposta,
                "trace": trace,
            }

        nome, argumentos = chamada

        resultado_tool = executar_tool(
            nome,
            argumentos,
        )

        trace.append(
            {
                "passo": passo,
                "ferramenta": nome,
                "argumentos": argumentos,
                "status": resultado_tool.get(
                    "status",
                    "desconhecido",
                ),
            }
        )

        observacao = {
            "status": resultado_tool.get(
                "status",
            ),
            "resposta": resultado_tool.get(
                "resposta",
            ),
            "contextos": resultado_tool.get(
                "contextos",
                [],
            ),
        }

        historico.append(
            mensagem
        )

        historico.append(
            {
                "role": "tool",
                "content": json.dumps(
                    observacao,
                    ensure_ascii=False,
                ),
            }
        )

    return {
        "status": "limite",
        "resposta": (
            "Limite de passos ReAct atingido."
        ),
        "trace": trace,
    }

def executar_agent_loop(entrada: str) -> dict:
    """Executa um ciclo controlado: decisao, tool, observacao e resposta."""
    entrada = entrada.strip()

    if not entrada:
        return {
            "status": "erro",
            "ferramenta": "nenhuma",
            "resposta": "Entrada vazia.",
        }

    primeira_mensagem = consultar_agente_ollama(entrada)
    chamada = extrair_tool_call(primeira_mensagem)

    if chamada is None:
        return {
            "status": "sem_acao",
            "ferramenta": "nenhuma",
            "resposta": (
                primeira_mensagem.get("content", "").strip()
                or "Nenhuma ferramenta foi necessaria."
            ),
        }

    nome, argumentos = chamada

    resultado_tool = executar_tool(
        nome,
        argumentos,
    )

    observacao = {
        "status": resultado_tool.get("status"),
        "resposta": resultado_tool.get("resposta"),
        "contextos": resultado_tool.get("contextos", []),
    }

    historico = [
        {
            "role": "user",
            "content": entrada,
        },
        primeira_mensagem,
        {
            "role": "tool",
            "content": json.dumps(
                observacao,
                ensure_ascii=False,
            ),
        },
    ]

    mensagem_final = consultar_agente_ollama(
        historico
    )

    segunda_chamada = extrair_tool_call(
        mensagem_final
    )

    if segunda_chamada is not None:
        return {
            "status": "limite",
            "ferramenta": nome,
            "resposta": (
                "Limite de chamadas de ferramenta atingido."
            ),
            "contextos": resultado_tool.get(
                "contextos",
                [],
            ),
        }

    return {
        "status": resultado_tool.get(
            "status",
            "ok",
        ),
        "ferramenta": nome,
        "resposta": (
            mensagem_final.get("content", "").strip()
            or resultado_tool.get("resposta", "")
        ),
        "contextos": resultado_tool.get(
            "contextos",
            [],
        ),
    }

def executar_agente_nativo(entrada: str) -> dict:
    """Executa o agente usando Tool Calling nativo do Ollama."""
    entrada = entrada.strip()

    if not entrada:
        return {
            "status": "erro",
            "ferramenta": "nenhuma",
            "resposta": "Entrada vazia.",
        }

    mensagem = consultar_agente_ollama(entrada)
    chamada = extrair_tool_call(mensagem)

    if chamada is None:
        return {
            "status": "sem_acao",
            "ferramenta": "nenhuma",
            "resposta": (
                mensagem.get("content", "").strip()
                or "Nenhuma ferramenta foi necessaria."
            ),
        }

    nome, argumentos = chamada

    resultado = executar_tool(
        nome,
        argumentos,
    )

    return {
        "status": resultado["status"],
        "ferramenta": nome,
        "resposta": resultado["resposta"],
        "contextos": resultado.get("contextos", []),
    }

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
