from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

print("\n=== BUSCA SEMANTICA - SECURITY LAB ===\n")

modelo = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

documentos = [
    "Um ransomware criptografou os arquivos da empresa.",
    "O usuario esqueceu a senha do e-mail corporativo.",
    "Foi detectada uma tentativa de phishing contra funcionarios.",
    "O firewall bloqueou uma tentativa de acesso externo.",
    "Uma vulnerabilidade critica foi identificada em um servidor Linux."
]

pergunta = "Houve algum ataque envolvendo sequestro de arquivos?"

print(f"Pergunta: {pergunta}\n")

# Transforma documentos e pergunta em vetores
vetores_documentos = modelo.encode(documentos)
vetor_pergunta = modelo.encode(pergunta)

resultados = []

# Compara a pergunta com cada documento
for indice, vetor_documento in enumerate(vetores_documentos):

    similaridade = cos_sim(
        vetor_pergunta,
        vetor_documento
    ).item()

    resultados.append(
        (similaridade, documentos[indice])
    )

# Ordena do mais semelhante para o menos semelhante
resultados.sort(reverse=True, key=lambda item: item[0])

print("=== RESULTADOS ===\n")

for posicao, (similaridade, documento) in enumerate(resultados, start=1):

    print(f"{posicao}. Similaridade: {similaridade:.4f}")
    print(f"   Documento: {documento}\n")

print("=== DOCUMENTO MAIS RELEVANTE ===\n")
print(resultados[0][1])
