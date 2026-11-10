"""Testes unitários do gerador vetorial SVG para muros de arrimo NBR 11682."""

import unittest
import xml.etree.ElementTree as ET
from fractions import Fraction

from muros_arrimo_nbr11682.calculator import dimensionar_projeto_muro_arrimo
from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    PropriedadesSolo,
    TipoMuro,
)
from muros_arrimo_nbr11682.svg_generator import gerar_painel_svg


class TestSVGGenerator(unittest.TestCase):
    """Valida o layout vetorial 1440x900 e integridade XML."""

    def setUp(self):
        self.dados_conforme = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Teste SVG",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(4, 1),
                largura_base_b_m=Fraction(25, 10),
                espessura_crista_m=Fraction(3, 10),
                espessura_base_paramento_m=Fraction(5, 10),
                espessura_sapata_m=Fraction(4, 10),
                comprimento_ponta_m=Fraction(6, 10),
                profundidade_embutimento_d_m=Fraction(5, 10),
                fck_concreto_mpa=Fraction(25, 1),
            ),
            solo_reaterro=PropriedadesSolo(
                tipo_solo="AREIA_MEDIA",
                peso_especifico_kn_m3=Fraction(18, 1),
                angulo_atrito_graus=30,
            ),
            solo_fundacao=PropriedadesSolo(
                tipo_solo="AREIA_COMPACTA",
                peso_especifico_kn_m3=Fraction(19, 1),
                angulo_atrito_graus=35,
                coef_atrito_base_mu=Fraction(55, 100),
                tensao_admissivel_solo_fundacao_kpa=Fraction(300, 1),
            ),
            carregamentos=CarregamentosExternos(
                sobrecarga_uniforme_reaterro_kpa=Fraction(5, 1),
                altura_nivel_freatico_m=Fraction(0, 1),
            ),
        )
        self.resultado_conforme = dimensionar_projeto_muro_arrimo(self.dados_conforme)

    def test_gerar_svg_dimensoes_e_xml(self):
        svg_txt = gerar_painel_svg(self.resultado_conforme)
        self.assertIn('<svg xmlns="http://www.w3.org/2000/svg"', svg_txt)
        self.assertIn('viewBox="0 0 1440 900"', svg_txt)
        self.assertIn('width="1440"', svg_txt)
        self.assertIn('height="900"', svg_txt)
        self.assertIn("Muro Teste SVG", svg_txt)
        self.assertIn("ABNT NBR 11682:2009", svg_txt)
        self.assertIn("CONFORME NBR 11682", svg_txt)

        # Validação do XML
        root = ET.fromstring(svg_txt)
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")

    def test_gerar_svg_projeto_com_pendencias(self):
        # Muro instável (base extremamente estreita: B=1m para H=5m)
        dados_instavel = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Crítico Instável",
            tipo_muro=TipoMuro.CONCRETO_ARMADO_BALANCO,
            geometria=GeometriaMuro(
                altura_total_h_m=Fraction(5, 1),
                largura_base_b_m=Fraction(1, 1), # B = 1.0 m para H = 5.0 m
                espessura_crista_m=Fraction(2, 10),
                espessura_base_paramento_m=Fraction(3, 10),
            ),
            solo_reaterro=self.dados_conforme.solo_reaterro,
            solo_fundacao=self.dados_conforme.solo_fundacao,
            carregamentos=CarregamentosExternos(sobrecarga_uniforme_reaterro_kpa=Fraction(20, 1)),
        )
        res_instavel = dimensionar_projeto_muro_arrimo(dados_instavel)
        svg_txt = gerar_painel_svg(res_instavel)
        self.assertIn("PENDÊNCIAS TÉCNICAS", svg_txt)
        self.assertFalse(res_instavel.conformidade_geral)


if __name__ == "__main__":
    unittest.main()
