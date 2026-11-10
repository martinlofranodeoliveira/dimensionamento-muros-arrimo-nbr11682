"""Testes de casos geotécnicos avançados: nível freático, gabiões, dente de cisalhamento e excentricidade."""

import unittest
from fractions import Fraction

from muros_arrimo_nbr11682.calculator import dimensionar_projeto_muro_arrimo
from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    PropriedadesSolo,
    TipoMuro,
)


class TestCasosAvancados(unittest.TestCase):
    """Casos especiais e envoltórias complexas da ABNT NBR 11682:2009."""

    def test_muro_com_nivel_freatico_e_alerta(self):
        # Muro com nível d'água a 2m da base
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro com Lençol Freático",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(4, 1),
                largura_base_b_m=Fraction(28, 10),
                espessura_crista_m=Fraction(3, 10),
                espessura_base_paramento_m=Fraction(5, 10),
                espessura_sapata_m=Fraction(45, 100),
                comprimento_ponta_m=Fraction(7, 10),
            ),
            solo_reaterro=PropriedadesSolo("AREIA_MEDIA", Fraction(18, 1), 30),
            solo_fundacao=PropriedadesSolo("AREIA_COMPACTA", Fraction(19, 1), 35, coef_atrito_base_mu=Fraction(55, 100)),
            carregamentos=CarregamentosExternos(
                sobrecarga_uniforme_reaterro_kpa=Fraction(5, 1),
                altura_nivel_freatico_m=Fraction(2, 1), # Hw = 2.0m
            ),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertGreater(res.empuxo.empuxo_hidrostatico_horizontal_kn, Fraction(0, 1))
        # Ew = 0.5 * 10 * 4 = 20 kN/m
        self.assertEqual(res.empuxo.empuxo_hidrostatico_horizontal_kn, Fraction(20, 1))
        self.assertTrue(any("Presença de nível freático" in a for a in res.alertas_tecnicos))

    def test_muro_gravidade_ciclopico(self):
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Ciclópico de Gravidade",
            tipo_muro=TipoMuro.GRAVIDADE_CONCRETO_CICLOPICO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(3, 1),
                largura_base_b_m=Fraction(18, 10),
                espessura_crista_m=Fraction(5, 10),
                espessura_base_paramento_m=Fraction(18, 10),
            ),
            solo_reaterro=PropriedadesSolo("AREIA_FOFA", Fraction(17, 1), 28),
            solo_fundacao=PropriedadesSolo("AREIA_MEDIA", Fraction(18, 1), 30, coef_atrito_base_mu=Fraction(50, 100)),
            carregamentos=CarregamentosExternos(),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertEqual(res.tipo_muro, TipoMuro.GRAVIDADE_CONCRETO_CICLOPICO)
        self.assertIsNone(res.estrutural) # Não dimensiona armadura de flexão
        self.assertTrue(res.aprovado_globalmente)

    def test_muro_gabiao_com_dente_de_cisalhamento(self):
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro de Gabião com Dente",
            tipo_muro=TipoMuro.GRAVIDADE_GABIAO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(4, 1),
                largura_base_b_m=Fraction(25, 10),
                espessura_crista_m=Fraction(1, 1),
                espessura_base_paramento_m=Fraction(25, 10),
                altura_dente_cisalhamento_m=Fraction(5, 10),
                largura_dente_cisalhamento_m=Fraction(5, 10),
            ),
            solo_reaterro=PropriedadesSolo("SILTE_ARGILOSO", Fraction(18, 1), 25),
            solo_fundacao=PropriedadesSolo("AREIA_COMPACTA", Fraction(19, 1), 34, coef_atrito_base_mu=Fraction(55, 100)),
            carregamentos=CarregamentosExternos(sobrecarga_uniforme_reaterro_kpa=Fraction(5, 1)),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertEqual(res.tipo_muro, TipoMuro.GRAVIDADE_GABIAO)
        self.assertTrue(res.estabilidade.aprovado_deslizamento)
        self.assertTrue(res.estabilidade.aprovado_tombamento)

    def test_muro_reprovado_por_excentricidade_fora_do_terco_medio(self):
        # Muro muito esbelto com base estreita B = 0.8m para H = 4.0m
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Muito Estreito",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(4, 1),
                largura_base_b_m=Fraction(8, 10), # B = 0.80 m
                espessura_crista_m=Fraction(2, 10),
                espessura_base_paramento_m=Fraction(3, 10),
            ),
            solo_reaterro=PropriedadesSolo("AREIA_MEDIA", Fraction(18, 1), 30),
            solo_fundacao=PropriedadesSolo("AREIA_MEDIA", Fraction(18, 1), 30),
            carregamentos=CarregamentosExternos(sobrecarga_uniforme_reaterro_kpa=Fraction(15, 1)),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertFalse(res.estabilidade.dentro_do_terco_medio)
        self.assertFalse(res.conformidade_geral)
        self.assertTrue(any("Resultante fora do terço médio" in a for a in res.alertas_tecnicos))

    def test_muro_alvenaria_pedra(self):
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro em Alvenaria de Pedra",
            tipo_muro=TipoMuro.GRAVIDADE_ALVENARIA_PEDRA,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(25, 10),
                largura_base_b_m=Fraction(18, 10),
                espessura_crista_m=Fraction(5, 10),
                espessura_base_paramento_m=Fraction(18, 10),
                profundidade_embutimento_d_m=Fraction(5, 10),
            ),
            solo_reaterro=PropriedadesSolo("AREIA_FOFA", Fraction(17, 1), 28),
            solo_fundacao=PropriedadesSolo("AREIA_COMPACTA", Fraction(19, 1), 35, coef_atrito_base_mu=Fraction(55, 100)),
            carregamentos=CarregamentosExternos(),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertEqual(res.tipo_muro, TipoMuro.GRAVIDADE_ALVENARIA_PEDRA)
        self.assertTrue(res.aprovado_globalmente)

    def test_muro_reprovado_por_capacidade_carga_solo(self):
        # Terreno com baixíssima capacidade de suporte (50 kPa)
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Solo Fraco",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(4, 1),
                largura_base_b_m=Fraction(25, 10),
                espessura_crista_m=Fraction(3, 10),
                espessura_base_paramento_m=Fraction(5, 10),
            ),
            solo_reaterro=PropriedadesSolo("AREIA_MEDIA", Fraction(18, 1), 30),
            solo_fundacao=PropriedadesSolo(
                "ARGILA_MOLE",
                Fraction(16, 1),
                20,
                tensao_admissivel_solo_fundacao_kpa=Fraction(50, 1), # Apenas 50 kPa
            ),
            carregamentos=CarregamentosExternos(),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertFalse(res.estabilidade.aprovado_capacidade_carga)
        self.assertTrue(any("excede a capacidade de carga admissível" in a for a in res.alertas_tecnicos))

    def test_muro_reprovado_por_deslizamento_atrito_baixo(self):
        # Interface extremamente lisa (mu = 0.15)
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Interface Lisa",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(4, 1),
                largura_base_b_m=Fraction(2, 1),
                espessura_crista_m=Fraction(3, 10),
                espessura_base_paramento_m=Fraction(4, 10),
            ),
            solo_reaterro=PropriedadesSolo("AREIA_MEDIA", Fraction(18, 1), 30),
            solo_fundacao=PropriedadesSolo(
                "ARGILA_LISA",
                Fraction(17, 1),
                20,
                coef_atrito_base_mu=Fraction(15, 100), # Atrito ínfimo
            ),
            carregamentos=CarregamentosExternos(sobrecarga_uniforme_reaterro_kpa=Fraction(10, 1)),
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertFalse(res.estabilidade.aprovado_deslizamento)
        self.assertTrue(any("Fator de segurança ao deslizamento insuficiente" in a for a in res.alertas_tecnicos))


if __name__ == "__main__":
    unittest.main()
