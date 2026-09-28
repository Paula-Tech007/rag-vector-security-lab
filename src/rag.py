import os
import json
import sys
import urllib.request

import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer
from config import SIMILARIDADE_MINIMA, contexto_confiavel


# ============================================================
# CONFIGURACAO
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "rag_security",
    "user": "rag_user",
    "password": os.getenv("POSTGRES_PASSWORD", ""),
}

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen3:4b-instruct"

EMBEDDING_MODEL = (
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

TOP_K = 3

def gerar_embedding(texto: str):
    """Gera o embedding vetorial de um texto."""
    modelo = SentenceTransformer(EMBEDDING_MODEL)
    return modelo.encode(texto)


def buscar_contexto(vetor_pergunta, top_k: int = TOP_K):
    """Busca os documentos mais similares no PostgreSQL + pgvector."""
    with psycopg.connect(**DB_CONFIG) as conexao:
        register_vector(conexao)

        with conexao.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    conteudo,
                    1 - (embedding <=> %s) AS similaridade
                FROM documentos
                ORDER BY embedding <=> %s
                LIMIT %s;
                """,
                (
                    vetor_pergunta,
                    vetor_pergunta,
                    top_k,
                ),
            )

            return cursor.fetchall()


def filtrar_contexto(resultados):
    """Retorna somente resultados que atingem o threshold de confianca."""
    resultados_validos = []

    for doc_id, conteudo, similaridade in resultados:
        similaridade = float(similaridade)

        if contexto_confiavel(similaridade):
            resultados_validos.append(
                (doc_id, conteudo, similaridade)
            )

    return resultados_validos




def construir_prompt(pergunta: str, contextos):
    """Constroi o prompt aumentado usando apenas o contexto aprovado."""
    contexto_final = "\n".join(
        f"- {documento}"
        for documento in contextos
    )

    prompt = f"""
    Voce e um assistente de analise de seguranca cibernetica.

    Responda utilizando SOMENTE as informacoes presentes
    no CONTEXTO.

    Nao invente fatos.

    Caso o contexto nao possua informacao suficiente,
    responda exatamente:

    "Nao ha informacao suficiente no contexto."

    CONTEXTO:

    {contexto_final}

    PERGUNTA:

    {pergunta}

    RESPOSTA:
    """.strip()

    return prompt

def consultar_ollama(prompt: str) -> str:
    """Envia o prompt ao Ollama e retorna somente a resposta gerada."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }

    dados = json.dumps(payload).encode("utf-8")

    requisicao = urllib.request.Request(
        OLLAMA_URL,
        data=dados,
        headers={
            "Content-Type": "application/json"
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

    return resposta_json.get(
        "response",
        "",
    ).strip()


def executar_rag(pergunta: str) -> dict:
    """Executa o pipeline RAG e retorna um resultado estruturado."""
    pergunta = pergunta.strip()

    if not pergunta:
        return {
            "status": "erro",
            "resposta": "Pergunta vazia.",
            "contextos": [],
        }

    vetor_pergunta = gerar_embedding(pergunta)
    resultados = buscar_contexto(vetor_pergunta)
    resultados_validos = filtrar_contexto(resultados)

    if not resultados_validos:
        return {
            "status": "sem_contexto",
            "resposta": "Nao ha informacao suficiente no contexto.",
            "contextos": [],
        }

    contextos = [
        conteudo
        for _, conteudo, _ in resultados_validos
    ]

    prompt = construir_prompt(pergunta, contextos)
    resposta = consultar_ollama(prompt)

    return {
        "status": "ok",
        "resposta": resposta,
        "contextos": contextos,
    }


def main():
    # ============================================================
    # 1. RECEBER PERGUNTA
    # ============================================================

    if len(sys.argv) > 1:
        pergunta = " ".join(sys.argv[1:])
    else:
        pergunta = input("Digite sua pergunta: ").strip()

    if not pergunta:
        raise SystemExit("Nenhuma pergunta foi informada.")

    print("\n=== RAG SECURITY LAB ===\n")
    print(f"Pergunta: {pergunta}")
    print(f"Top-K: {TOP_K}")
    print(f"Similaridade minima: {SIMILARIDADE_MINIMA:.2f}")


    # ============================================================
    # 2. EMBEDDING DA PERGUNTA
    # ============================================================

    print("\n[1/4] Gerando embedding da pergunta...")

    vetor_pergunta = gerar_embedding(pergunta)

    print(f"Dimensoes: {len(vetor_pergunta)}")


    # ============================================================
    # 3. RETRIEVAL
    # ============================================================

    print("\n[2/4] Buscando contexto no PostgreSQL + pgvector...")

    resultados = buscar_contexto(vetor_pergunta)

    if not resultados:
        raise RuntimeError(
            "Nenhum documento foi recuperado do banco."
        )


    # ============================================================
    # 4. FILTRO POR SIMILARIDADE
    # ============================================================

    print("\n=== RESULTADOS BRUTOS DO PGVECTOR ===\n")

    resultados_validos = filtrar_contexto(resultados)

    for posicao, (doc_id, conteudo, similaridade) in enumerate(
        resultados,
        start=1,
    ):
        similaridade = float(similaridade)

        status = (
            "ACEITO"
            if contexto_confiavel(similaridade)
            else "DESCARTADO"
        )

        print(
            f"{posicao}. ID {doc_id} | "
            f"similaridade {similaridade:.4f} | {status}"
        )

        print(f"   {conteudo}")

    # ============================================================
    # VERIFICAR SE EXISTE CONTEXTO CONFIAVEL
    # ============================================================

    if not resultados_validos:

        print("\n" + "=" * 60)
        print("RESPOSTA FINAL DO RAG")
        print("=" * 60)

        print("Nao ha informacao suficiente no contexto.")

        print("\n" + "=" * 60)
        print("PIPELINE CONCLUIDO SEM CHAMAR O OLLAMA")
        print("=" * 60)

        print(
            "Pergunta -> Embedding -> pgvector -> "
            "Threshold -> Sem contexto confiavel"
        )

        raise SystemExit(0)


    # ============================================================
    # MOSTRAR CONTEXTO APROVADO
    # ============================================================

    print("\n=== CONTEXTO APROVADO PELO THRESHOLD ===\n")

    contextos = []

    for posicao, (doc_id, conteudo, similaridade) in enumerate(
        resultados_validos,
        start=1,
    ):

        print(
            f"{posicao}. ID {doc_id} | "
            f"similaridade {similaridade:.4f}"
        )

        print(f"   {conteudo}")

        contextos.append(conteudo)


    # ============================================================
    # 5. AUGMENTATION
    # ============================================================

    print("\n[3/4] Construindo prompt aumentado...")

    prompt = construir_prompt(pergunta, contextos)


    # ============================================================
    # 6. GENERATION
    # ============================================================

    print("\n[4/4] Enviando contexto + pergunta para o Ollama...")

    resposta_final = consultar_ollama(prompt)


    # ============================================================
    # RESULTADO FINAL
    # ============================================================

    print("\n" + "=" * 60)

    print("RESPOSTA FINAL DO RAG")

    print("=" * 60)

    print(resposta_final)

    print("\n" + "=" * 60)

    print("PIPELINE CONCLUIDO")

    print("=" * 60)

    print(
        "Pergunta -> Embedding -> pgvector -> Threshold -> "
        "Contexto -> Ollama -> Resposta"
    )


if __name__ == "__main__":
    main()
