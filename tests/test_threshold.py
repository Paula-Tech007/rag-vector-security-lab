from src.config import SIMILARIDADE_MINIMA, contexto_confiavel


def test_threshold_configurado():
    assert SIMILARIDADE_MINIMA == 0.60


def test_phishing_deve_ser_aceito():
    assert contexto_confiavel(0.8217) is True


def test_firewall_deve_ser_aceito():
    assert contexto_confiavel(0.8897) is True


def test_resultado_fraco_deve_ser_descartado():
    assert contexto_confiavel(0.5786) is False


def test_kubernetes_deve_ser_descartado():
    assert contexto_confiavel(0.2987) is False


def test_valor_exatamente_no_threshold_deve_ser_aceito():
    assert contexto_confiavel(0.60) is True


def test_valor_logo_abaixo_do_threshold_deve_ser_descartado():
    assert contexto_confiavel(0.5999) is False
