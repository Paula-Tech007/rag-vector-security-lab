from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

print("\n=== LABORATORIO DE EMBEDDINGS ===\n")

# Modelo multilingue para transformar textos em vetores
modelo = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

frases = [
    "Um ransomware criptografou os arquivos da empresa.",
    "Um malware bloqueou documentos corporativos e exigiu resgate.",
    "O usuario esqueceu a senha do e-mail.",
    "Foi detectada uma tentativa de phishing contra funcionarios.",
]

print("Gerando embeddings...\n")

embeddings = modelo.encode(frases)

print(f"Quantidade de frases: {len(frases)}")
print(f"Dimensoes de cada vetor: {embeddings.shape[1]}")

print("\nPrimeiros 10 numeros do vetor da frase A:")
print(embeddings[0][:10])

print("\n=== SIMILARIDADE COM A FRASE A ===\n")

for indice in range(1, len(frases)):
    similaridade = cos_sim(
        embeddings[0],
        embeddings[indice]
    ).item()

    letra = chr(65 + indice)

    print(f"A x {letra} = {similaridade:.4f}")
    print(f"Frase: {frases[indice]}\n")
