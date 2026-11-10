"""Testes unitários do motor de cálculo analítico e determinístico NBR 11682 / NBR 6118."""

import unittest
from fractions import Fraction

from muros_arrimo_nbr11682.calculator import (
    calcular_componentes_estabilidade,
    calcular_empuxos_terra,
    dimensionar_estrutural_paramento,
    dimensionar_projeto_muro_arrimo,
    obter_coeficientes_empuxo,
    obter_peso_especifico_muro,
    verificar_estabilidade_geotecnica,
)
from muros_arrimo_nbr11682.constants import (
    FATOR_SEGURANCA_DESLIZAMENTO_MINIMO,
    FATOR_SEGURANCA_TOMBAMENTO_MINIMO,
    PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3,
    PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3,
    PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3,
    PESO_ESPECIFICO_GABIAO_KN_M3,
)
from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    PropriedadesSolo,
    TipoMuro,
)


class TestCalculator(unittest.TestCase):
    """Testa os equilíbrios e formulações analíticas em frações exatas."""

    def setUp(self):
        self.geo_padrao = GeometriaMuro(
            altura_total_h_m=Fraction(4, 1),
            largura_base_b_m=Fraction(25, 10),
            espessura_crista_m=Fraction(3, 10),
            espessura_base_paramento_m=Fraction(5, 10),
            espessura_sapata_m=Fraction(4, 10),
            comprimento_ponta_m=Fraction(6, 10),
            profundidade_embutimento_d_m=Fraction(5, 10),
            fck_concreto_mpa=Fraction(25, 1),
        )
        self.solo_reaterro = PropriedadesSolo(
            tipo_solo="AREIA_MEDIA",
            peso_especifico_kn_m3=Fraction(18, 1),
            angulo_atrito_graus=30,
        )
        self.solo_fundacao = PropriedadesSolo(
            tipo_solo="AREIA_COMPACTA",
            peso_especifico_kn_m3=Fraction(19, 1),
            angulo_atrito_graus=35,
            coef_atrito_base_mu=Fraction(55, 100),
            tensao_admissivel_solo_fundacao_kpa=Fraction(300, 1),
        )
        self.carregamentos = CarregamentosExternos(
            sobrecarga_uniforme_reaterro_kpa=Fraction(5, 1),
            altura_nivel_freatico_m=Fraction(0, 1),
        )

    def test_pesos_especificos_muro(self):
        self.assertEqual(obter_peso_especifico_muro(TipoMuro.CONCRETO_ARMADO_BALANCO), PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3)
        self.assertEqual(obter_peso_especifico_muro(TipoMuro.GRAVIDADE_CONCRETO_CICLOPICO), PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3)
        self.assertEqual(obter_peso_especifico_muro(TipoMuro.GRAVIDADE_ALVENARIA_PEDRA), PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3)
        self.assertEqual(obter_peso_especifico_muro(TipoMuro.GRAVIDADE_GABIAO), PESO_ESPECIFICO_GABIAO_KN_M3)

    def test_coeficientes_empuxo_rankine(self):
        ka, kp = obter_coeficientes_empuxo(self.solo_reaterro)
        # phi = 30° -> Ka = 1/3, Kp = 3
        self.assertEqual(ka, Fraction(1, 3))
        self.assertEqual(kp, Fraction(3, 1))

    def test_calcular_empuxos_terra(self):
        res = calcular_empuxos_terra(self.geo_padrao, self.solo_reaterro, self.carregamentos)
        # H = 4m, gamma = 18 kN/m³, Ka = 1/3
        # Ea_solo = 0.5 * 18 * 16 * (1/3) = 48 kN/m
        self.assertEqual(res.empuxo_solo_horizontal_kn, Fraction(48, 1))
        # Ea_q = 5 * (1/3) * 4 = 20/3 kN/m
        self.assertEqual(res.empuxo_sobrecarga_horizontal_kn, Fraction(20, 3))
        # Sem água
        self.assertEqual(res.empuxo_hidrostatico_horizontal_kn, Fraction(0, 1))
        # Ea_tot = 48 + 20/3 = 164/3 kN/m
        self.assertEqual(res.empuxo_total_horizontal_kn, Fraction(164, 3))
        self.assertGreater(res.ponto_aplicacao_empuxo_y_m, Fraction(0, 1))

    def test_calcular_componentes_estabilidade_balanco(self):
        empuxo = calcular_empuxos_terra(self.geo_padrao, self.solo_reaterro, self.carregamentos)
        componentes, n_tot, m_estab, m_tomb = calcular_componentes_estabilidade(
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=self.geo_padrao,
            solo=self.solo_reaterro,
            carregamentos=self.carregamentos,
            empuxo=empuxo,
        )
        self.assertGreater(len(componentes), 3)
        self.assertGreater(n_tot, Fraction(0, 1))
        self.assertGreater(m_estab, Fraction(0, 1))
        self.assertGreater(m_tomb, Fraction(0, 1))

    def test_verificar_estabilidade_geotecnica(self):
        empuxo = calcular_empuxos_terra(self.geo_padrao, self.solo_reaterro, self.carregamentos)
        componentes, n_tot, m_estab, m_tomb = calcular_componentes_estabilidade(
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=self.geo_padrao,
            solo=self.solo_reaterro,
            carregamentos=self.carregamentos,
            empuxo=empuxo,
        )
        est = verificar_estabilidade_geotecnica(
            geometria=self.geo_padrao,
            solo_fundacao=self.solo_fundacao,
            empuxo=empuxo,
            normal_total=n_tot,
            momento_estab_total=m_estab,
            momento_tomb_total=m_tomb,
        )
        self.assertGreaterEqual(est.fator_seguranca_tombamento, FATOR_SEGURANCA_TOMBAMENTO_MINIMO)
        self.assertGreater(est.tensao_maxima_base_kpa, Fraction(0, 1))
        self.assertLessEqual(est.excentricidade_base_e_m, est.limite_terco_medio_m)
        self.assertTrue(est.dentro_do_terco_medio)

    def test_dimensionar_estrutural_paramento(self):
        res = dimensionar_estrutural_paramento(self.geo_padrao, self.solo_reaterro, self.carregamentos)
        self.assertGreater(res.momento_fletor_calculo_base_md_knm, Fraction(0, 1))
        self.assertGreater(res.area_armadura_adotada_cm2_m, Fraction(0, 1))
        self.assertTrue(res.aprovado_cisalhamento)
        self.assertTrue(res.aprovado_estruturalmente)

    def test_dimensionar_projeto_completo_e_validacoes(self):
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Teste Unitário",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=self.geo_padrao,
            solo_reaterro=self.solo_reaterro,
            solo_fundacao=self.solo_fundacao,
            carregamentos=self.carregamentos,
        )
        res = dimensionar_projeto_muro_arrimo(dados)
        self.assertEqual(res.identificacao_projeto, "Muro Teste Unitário")
        self.assertTrue(res.aprovado_globalmente)
        self.assertTrue(res.conformidade_geral)

    def test_validacao_dimensoes_invalidas(self):
        geo_invalida = GeometriaMuro(
            altura_total_h_m=Fraction(0, 1),
            largura_base_b_m=Fraction(2, 1),
            espessura_crista_m=Fraction(3, 10),
            espessura_base_paramento_m=Fraction(5, 10),
        )
        dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Inválido",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=geo_invalida,
            solo_reaterro=self.solo_reaterro,
            solo_fundacao=self.solo_fundacao,
            carregamentos=self.carregamentos,
        )
        with self.assertRaises(ValueError):
            dimensionar_projeto_muro_arrimo(dados)

    def test_muro_com_dente_de_cisalhamento_geometria(self):
        geo_dente = GeometriaMuro(
            altura_total_h_m=Fraction(4, 1),
            largura_base_b_m=Fraction(25, 10),
            espessura_crista_m=Fraction(3, 10),
            espessura_base_paramento_m=Fraction(5, 10),
            espessura_sapata_m=Fraction(4, 10),
            comprimento_ponta_m=Fraction(6, 10),
            altura_dente_cisalhamento_m=Fraction(4, 10),
            largura_dente_cisalhamento_m=Fraction(4, 10),
        )
        empuxo = calcular_empuxos_terra(geo_dente, self.solo_reaterro, self.carregamentos)
        componentes, n_tot, m_estab, _ = calcular_componentes_estabilidade(
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=geo_dente,
            solo=self.solo_reaterro,
            carregamentos=self.carregamentos,
            empuxo=empuxo,
        )
        self.assertTrue(any("Dente de Cisalhamento" in c.descricao for c in componentes))
        self.assertGreater(n_tot, Fraction(0, 1))

    def test_solo_com_angulos_arbitrarios(self):
        solo_alto = PropriedadesSolo("SOLO_ESPECIAL_38", Fraction(20, 1), 38)
        ka_alto, kp_alto = obter_coeficientes_empuxo(solo_alto)
        self.assertEqual(ka_alto, Fraction(271, 1000))

        solo_baixo = PropriedadesSolo("SOLO_ESPECIAL_22", Fraction(16, 1), 22)
        ka_baixo, kp_baixo = obter_coeficientes_empuxo(solo_baixo)
        self.assertEqual(ka_baixo, Fraction(490, 1000))

    def test_empuxo_passivo_embutimento_zero(self):
        geo_sem_emb = GeometriaMuro(
            altura_total_h_m=Fraction(4, 1),
            largura_base_b_m=Fraction(25, 10),
            espessura_crista_m=Fraction(3, 10),
            espessura_base_paramento_m=Fraction(5, 10),
            profundidade_embutimento_d_m=Fraction(0, 1),
        )
        empuxo = calcular_empuxos_terra(geo_sem_emb, self.solo_reaterro, self.carregamentos)
        self.assertEqual(empuxo.empuxo_passivo_disponivel_kn, Fraction(0, 1))


if __name__ == "__main__":
    unittest.main()
