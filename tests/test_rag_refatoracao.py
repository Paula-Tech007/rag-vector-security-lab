from pathlib import Path


def test_rag_possui_funcao_gerar_embedding():
    conteudo = Path("src/rag.py").read_text(encoding="utf-8")

    assert "def gerar_embedding(" in conteudo

def test_rag_possui_funcao_buscar_contexto():
    conteudo = Path("src/rag.py").read_text(encoding="utf-8")

    assert "def buscar_contexto(" in conteudo

def test_rag_possui_funcao_filtrar_contexto():
    conteudo = Path("src/rag.py").read_text(encoding="utf-8")

    assert "def filtrar_contexto(" in conteudo

def test_rag_possui_protecao_main():
    conteudo = Path("src/rag.py").read_text(encoding="utf-8")

    assert 'if __name__ == "__main__":' in conteudo
    assert "def main(" in conteudo

def test_rag_possui_funcao_construir_prompt():
    conteudo = Path("src/rag.py").read_text(encoding="utf-8")

    assert "def construir_prompt(" in conteudo