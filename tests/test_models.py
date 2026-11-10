"""Testes unitários dos modelos e enums de contenção e arrimo."""

import unittest
from fractions import Fraction

from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    ComponenteForca,
    GeometriaMuro,
    MetodoEmpuxo,
    PropriedadesSolo,
    ResultadoEmpuxo,
    ResultadoEstabilidadeGeotecnica,
    ResultadoEstruturalMuro,
    TipoCondicaoDrenagem,
    TipoMuro,
)


class TestModels(unittest.TestCase):
    """Testa enums e estruturas de dados."""

    def test_enums(self):
        self.assertEqual(TipoMuro.CONCRETO_ARMADO_BALANCO.value, "CONCRETO_ARMADO_BALANCO")
        self.assertEqual(TipoMuro.GRAVIDADE_CONCRETO_CICLOPICO.value, "GRAVIDADE_CONCRETO_CICLOPICO")
        self.assertEqual(TipoMuro.GRAVIDADE_ALVENARIA_PEDRA.value, "GRAVIDADE_ALVENARIA_PEDRA")
        self.assertEqual(TipoMuro.GRAVIDADE_GABIAO.value, "GRAVIDADE_GABIAO")
        self.assertEqual(MetodoEmpuxo.RANKINE.value, "RANKINE")
        self.assertEqual(TipoCondicaoDrenagem.DRENAGEM_EFICIENTE_SEM_AGUA.value, "DRENAGEM_EFICIENTE_SEM_AGUA")

    def test_geometria_muro(self):
        geo = GeometriaMuro(
            altura_total_h_m=Fraction(4, 1),
            largura_base_b_m=Fraction(25, 10),
            espessura_crista_m=Fraction(3, 10),
            espessura_base_paramento_m=Fraction(5, 10),
        )
        self.assertEqual(geo.altura_total_h_m, Fraction(4, 1))
        self.assertEqual(geo.largura_base_b_m, Fraction(5, 2))
        self.assertEqual(geo.espessura_sapata_m, Fraction(0, 1))

    def test_propriedades_solo(self):
        solo = PropriedadesSolo(
            tipo_solo="AREIA_MEDIA",
            peso_especifico_kn_m3=Fraction(18, 1),
            angulo_atrito_graus=30,
            coesao_kpa=Fraction(0, 1),
            coef_atrito_base_mu=Fraction(5, 10),
            tensao_admissivel_solo_fundacao_kpa=Fraction(250, 1),
        )
        self.assertEqual(solo.tipo_solo, "AREIA_MEDIA")
        self.assertEqual(solo.peso_especifico_kn_m3, Fraction(18, 1))

    def test_carregamentos_externos(self):
        carreg = CarregamentosExternos(
            sobrecarga_uniforme_reaterro_kpa=Fraction(10, 1),
            altura_nivel_freatico_m=Fraction(0, 1),
        )
        self.assertEqual(carreg.sobrecarga_uniforme_reaterro_kpa, Fraction(10, 1))
        self.assertEqual(carreg.altura_nivel_freatico_m, Fraction(0, 1))

    def test_componente_forca(self):
        comp = ComponenteForca(
            descricao="Sapata",
            forca_vertical_kn=Fraction(100, 1),
            forca_horizontal_kn=Fraction(0, 1),
            braco_x_m=Fraction(12, 10),
            braco_y_m=Fraction(2, 10),
            momento_estabilizante_knm=Fraction(120, 1),
            momento_tombante_knm=Fraction(0, 1),
        )
        self.assertEqual(comp.momento_estabilizante_knm, Fraction(120, 1))


if __name__ == "__main__":
    unittest.main()
