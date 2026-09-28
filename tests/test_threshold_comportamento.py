import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from config import contexto_confiavel


def test_contexto_abaixo_do_threshold_e_descartado():
    assert contexto_confiavel(0.59) is False


def test_contexto_no_threshold_e_aceito():
    assert contexto_confiavel(0.60) is True


def test_contexto_acima_do_threshold_e_aceito():
    assert contexto_confiavel(0.85) is True