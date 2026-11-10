"""Testes unitários das constantes normativas geotécnicas e estruturais."""

import unittest
from fractions import Fraction

from muros_arrimo_nbr11682.constants import (
    FATOR_SEGURANCA_CAPACIDADE_CARGA_MINIMO,
    FATOR_SEGURANCA_DESLIZAMENTO_MINIMO,
    FATOR_SEGURANCA_TOMBAMENTO_MINIMO,
    FYK_ACO_CA50_MPA,
    GAMMA_ACO,
    GAMMA_ACOES_DESFAVORAVEIS,
    GAMMA_CONCRETO,
    PESO_ESPECIFICO_AGUA_KN_M3,
    PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3,
    PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3,
    PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3,
    PESO_ESPECIFICO_GABIAO_KN_M3,
    TABELA_SOLOS_PADRAO,
    TAXA_ARMADURA_FLEXAO_MINIMA,
)


class TestConstants(unittest.TestCase):
    """Garante exatidão das grandezas e ausência de ponto flutuante."""

    def test_fatores_seguranca_geotecnicos(self):
        self.assertEqual(FATOR_SEGURANCA_TOMBAMENTO_MINIMO, Fraction(3, 2))      # 1.50
        self.assertEqual(FATOR_SEGURANCA_DESLIZAMENTO_MINIMO, Fraction(3, 2))    # 1.50
        self.assertEqual(FATOR_SEGURANCA_CAPACIDADE_CARGA_MINIMO, Fraction(2, 1))# 2.00

    def test_fatores_estruturais_concreto_aco(self):
        self.assertEqual(GAMMA_CONCRETO, Fraction(14, 10))
        self.assertEqual(GAMMA_ACO, Fraction(115, 100))
        self.assertEqual(GAMMA_ACOES_DESFAVORAVEIS, Fraction(14, 10))
        self.assertEqual(FYK_ACO_CA50_MPA, Fraction(500, 1))
        self.assertEqual(TAXA_ARMADURA_FLEXAO_MINIMA, Fraction(15, 10000))

    def test_pesos_especificos(self):
        self.assertEqual(PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3, Fraction(25, 1))
        self.assertEqual(PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3, Fraction(22, 1))
        self.assertEqual(PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3, Fraction(23, 1))
        self.assertEqual(PESO_ESPECIFICO_GABIAO_KN_M3, Fraction(19, 1))
        self.assertEqual(PESO_ESPECIFICO_AGUA_KN_M3, Fraction(10, 1))

    def test_tabela_solos_padrao(self):
        self.assertIn("AREIA_MEDIA", TABELA_SOLOS_PADRAO)
        self.assertIn("AREIA_COMPACTA", TABELA_SOLOS_PADRAO)
        self.assertIn("SILTE_ARGILOSO", TABELA_SOLOS_PADRAO)

        areia_media = TABELA_SOLOS_PADRAO["AREIA_MEDIA"]
        # phi = 30° -> Ka = 1/3, Kp = 3
        self.assertEqual(areia_media.angulo_atrito_graus, 30)
        self.assertEqual(areia_media.ka_rankine, Fraction(1, 3))
        self.assertEqual(areia_media.kp_rankine, Fraction(3, 1))
        self.assertEqual(areia_media.seno_phi, Fraction(1, 2))


if __name__ == "__main__":
    unittest.main()
