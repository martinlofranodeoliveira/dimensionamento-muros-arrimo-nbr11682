"""Testes unitários dos exportadores técnicos (Memorial, CSV, ZIP)."""

import os
import tempfile
import unittest
import zipfile
from fractions import Fraction

from muros_arrimo_nbr11682.calculator import dimensionar_projeto_muro_arrimo
from muros_arrimo_nbr11682.exporters import (
    _sanitizar_campo_csv,
    exportar_csv_resumo,
    exportar_memorial_descritivo,
    gerar_csv_resumo_muro,
    gerar_memorial_muro_texto,
    gerar_pacote_completo_zip,
    gerar_pacote_zip_muro,
)
from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    PropriedadesSolo,
    TipoMuro,
)


class TestExporters(unittest.TestCase):
    """Testa os formatos de exportação e proteção contra sobrescrita e injeção."""

    def setUp(self):
        self.dados = DadosProjetoMuroArrimo(
            identificacao_projeto="Muro Teste Exportadores",
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
        self.resultado = dimensionar_projeto_muro_arrimo(self.dados)

    def test_memorial_descritivo(self):
        txt = gerar_memorial_muro_texto(self.resultado)
        self.assertIn("LOFRANO TECNOLOGIA", txt)
        self.assertIn("ABNT NBR 11682:2009", txt)
        self.assertIn("Muro Teste Exportadores", txt)
        self.assertIn("CONCRETO_ARMADO_BALANCO", txt)
        self.assertIn("EMPUXOS DE TERRA ATUANTES (MÉTODO DE RANKINE)", txt)
        self.assertIn("ESTABILIDADE GEOTÉCNICA GLOBAL", txt)

        # Teste alias
        txt_alias = exportar_memorial_descritivo(self.resultado)
        self.assertEqual(txt, txt_alias)

    def test_csv_resumo_e_sanitizacao(self):
        csv_txt = gerar_csv_resumo_muro(self.resultado)
        self.assertIn("modulo;parametro;valor;unidade;observacao", csv_txt)
        self.assertIn("DADOS_PROJETO", csv_txt)
        self.assertIn("GEOMETRIA", csv_txt)
        self.assertIn("EMPUXOS", csv_txt)
        self.assertIn("ESTABILIDADE", csv_txt)

        # Teste sanitização anti-fórmula
        self.assertEqual(_sanitizar_campo_csv("=SOMA(1+2)"), "'=SOMA(1+2)")
        self.assertEqual(_sanitizar_campo_csv("+10"), "'+10")
        self.assertEqual(_sanitizar_campo_csv("-5"), "'-5")
        self.assertEqual(_sanitizar_campo_csv("@call"), "'@call")
        self.assertEqual(_sanitizar_campo_csv("\tdata"), "'\tdata")
        self.assertEqual(_sanitizar_campo_csv("Texto Limpo"), "Texto Limpo")

        # Teste alias
        csv_alias = exportar_csv_resumo(self.resultado)
        self.assertEqual(csv_txt, csv_alias)

    def test_pacote_zip_determinista(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "pacote_muro.zip")
            svg_dummy = "<svg><circle r='10'/></svg>"
            gerar_pacote_zip_muro(self.resultado, zip_path, svg_conteudo=svg_dummy)

            self.assertTrue(os.path.exists(zip_path))
            with zipfile.ZipFile(zip_path, "r") as zf:
                nomes = zf.namelist()
                self.assertIn("memorial_muro_arrimo.txt", nomes)
                self.assertIn("dados_muro_arrimo.json", nomes)
                self.assertIn("resumo_muro_arrimo.csv", nomes)
                self.assertIn("painel_muro_arrimo.svg", nomes)

                # Verifica data determinística (2026, 1, 1, 0, 0, 0)
                for info in zf.infolist():
                    self.assertEqual(info.date_time, (2026, 1, 1, 0, 0, 0))

            # Verifica proteção O_EXCL contra sobrescrita acidental
            with self.assertRaises(FileExistsError):
                gerar_pacote_zip_muro(self.resultado, zip_path)

    def test_pacote_zip_alias(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os.path.join(tmpdir, "pacote_alias.zip")
            gerar_pacote_completo_zip(self.resultado, zip_path)
            self.assertTrue(os.path.exists(zip_path))


if __name__ == "__main__":
    unittest.main()
