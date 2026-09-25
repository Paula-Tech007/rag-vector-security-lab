SIMILARIDADE_MINIMA = 0.60


def contexto_confiavel(similaridade: float) -> bool:
    """Retorna True quando a similaridade atinge o threshold minimo."""
    return float(similaridade) >= SIMILARIDADE_MINIMA
