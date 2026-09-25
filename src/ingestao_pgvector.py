import os
import psycopg
from pgvector.psycopg import register_vector
from sentence_transformers import SentenceTransformer

print("\n=== INGESTAO NO BANCO VETORIAL ===\n")

documentos = [
    "Um ransomware criptografou os arquivos da empresa.",
    "O usuario esqueceu a senha do e-mail corporativo.",
    "Foi detectada uma tentativa de phishing contra funcionarios.",
    "O firewall bloqueou uma tentativa de acesso externo.",
    "Uma vulnerabilidade critica foi identificada em um servidor Linux."
]

print("Carregando modelo de embeddings...")

modelo = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("Gerando embeddings...")

embeddings = modelo.encode(documentos)

print(f"Documentos: {len(documentos)}")
print(f"Dimensoes: {embeddings.shape[1]}")

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

        # Mantemos o teste repetivel:
        # cada execucao limpa os documentos do laboratorio.
        cursor.execute("TRUNCATE TABLE documentos RESTART IDENTITY;")

        for documento, embedding in zip(documentos, embeddings):

            cursor.execute(
                """
                INSERT INTO documentos (conteudo, embedding)
                VALUES (%s, %s)
                """,
                (documento, embedding)
            )

            print(f"Inserido: {documento}")

    conexao.commit()

print("\n=== INGESTAO CONCLUIDA ===")
print(f"{len(documentos)} documentos armazenados no pgvector.")
