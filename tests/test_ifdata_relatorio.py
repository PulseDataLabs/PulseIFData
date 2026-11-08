from scrapers.utils.ifdata_relatorio import tipos_validos_para_relatorio


def test_tipos_validos_relatorios_basicos():
    # Relatórios 1 a 4 devem ter sempre os tipos 1, 2 e 3 em qualquer ano
    for rel_id in ("1", "2", "3", "4"):
        res_antigo = tipos_validos_para_relatorio(rel_id, 201803)
        res_recente = tipos_validos_para_relatorio(rel_id, 202503)
        assert [c for c, _ in res_antigo] == [1, 2, 3]
        assert [c for c, _ in res_recente] == [1, 2, 3]


def test_tipos_validos_relatorio_5_capital():
    # Em 2014 era tipo 2 (conglomerados financeiros); a partir de 201503 virou tipo 1 (prudencial)
    res_2014 = tipos_validos_para_relatorio("5", 201412)
    res_2015 = tipos_validos_para_relatorio("5", 201503)
    res_2025 = tipos_validos_para_relatorio("5", 202503)
    assert [c for c, _ in res_2014] == [2]
    assert [c for c, _ in res_2015] == [1]
    assert [c for c, _ in res_2025] == [1]


def test_tipos_validos_relatorio_6_segmentacao():
    # Segmentação só foi criada a partir de 201703 (Resolução 4.553)
    assert tipos_validos_para_relatorio("6", 201612) == []
    res_2017 = tipos_validos_para_relatorio("6", 201703)
    assert [c for c, _ in res_2017] == [1]


def test_tipos_validos_relatorios_credito_migracao_2025():
    # Relatórios 7, 9, 10, 11, 12, 13, 14 eram tipo 2 até 202412 e viraram tipo 1 a partir de 202503
    for rel_id in ("7", "9", "10", "11", "12", "13", "14"):
        res_pre = tipos_validos_para_relatorio(rel_id, 202412)
        res_pos = tipos_validos_para_relatorio(rel_id, 202503)
        assert [c for c, _ in res_pre] == [2], f"Falha pré-2025 no relatório {rel_id}"
        assert [c for c, _ in res_pos] == [1], f"Falha pós-2025 no relatório {rel_id}"


def test_tipos_validos_relatorio_8_nivel_de_risco():
    # Relatório 8 (Res. 2.682) vigorou até 202412. A partir de 202503 (Res. 4.966) foi descontinuado
    res_pre = tipos_validos_para_relatorio("8", 202412)
    res_pos = tipos_validos_para_relatorio("8", 202503)
    assert [c for c, _ in res_pre] == [2]
    assert res_pos == []


def test_tipos_validos_relatorio_15_cambio():
    # Câmbio publicou tipo 4 até 202306
    res_pre = tipos_validos_para_relatorio("15", 202306)
    res_pos = tipos_validos_para_relatorio("15", 202309)
    assert [c for c, _ in res_pre] == [4]
    assert res_pos == []


def test_tipos_validos_relatorio_16_res4966():
    # Relatório 16 substitui o 8 e nasce em 202503 como tipo 1
    assert tipos_validos_para_relatorio("16", 202412) == []
    res_2025 = tipos_validos_para_relatorio("16", 202503)
    assert [c for c, _ in res_2025] == [1]

