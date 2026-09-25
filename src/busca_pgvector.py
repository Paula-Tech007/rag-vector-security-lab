import os
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

print("\n=== BUSCA VETORIAL COM POSTGRESQL + PGVECTOR ===\n")

pergunta = "Houve algum ataque envolvendo sequestro de arquivos?"

print(f"Pergunta: {pergunta}\n")

print("Carregando modelo de embeddings...")

modelo = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("Gerando embedding da pergunta...")

vetor_pergunta = modelo.encode(pergunta)

print(f"Dimensoes do vetor da pergunta: {len(vetor_pergunta)}")

print("\nConectando ao PostgreSQL + pgvector...")

with psycopg.connect(
    host="localhost",
    port=5432,
    dbname="rag_security",
    user="rag_user",
    password=os.getenv("POSTGRES_PASSWORD", "")
) as conexao:

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
            LIMIT 3;
            """,
            (vetor_pergunta, vetor_pergunta)
        )

        resultados = cursor.fetchall()

print("\n=== TOP 3 RESULTADOS DO PGVECTOR ===\n")

for posicao, (id_documento, conteudo, similaridade) in enumerate(
    resultados,
    start=1
):
    print(f"{posicao}. ID: {id_documento}")
    print(f"   Similaridade: {float(similaridade):.4f}")
    print(f"   Documento: {conteudo}\n")

print("=== DOCUMENTO RECUPERADO ===\n")

if resultados:
    print(resultados[0][1])
else:
    print("Nenhum documento encontrado.")
