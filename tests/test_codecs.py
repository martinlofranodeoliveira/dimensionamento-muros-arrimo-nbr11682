"""Testes unitários dos codecs JSON RFC 8259 estritos (Zero-Float, Anti-BOM, Profundidade)."""

import json
import unittest
from fractions import Fraction

from muros_arrimo_nbr11682.calculator import dimensionar_projeto_muro_arrimo
from muros_arrimo_nbr11682.codecs import (
    carregar_projeto_muro_json,
    codificar_json_projeto,
    decodificar_json_projeto,
    exportar_resultado_json,
)
from muros_arrimo_nbr11682.models import TipoMuro


class TestCodecs(unittest.TestCase):
    """Garante integridade com RFC 8259 e regras LOFRANO TECNOLOGIA."""

    def setUp(self):
        self.json_valido = """{
  "identificacao_projeto": "Contenção de Encosta Residencial",
  "tipo_muro": "CONCRETO_ARMADO_BALANCO",
  "responsavel_tecnico": "Eng. Martin Lofrano",
  "geometria": {
    "altura_total_h_m": 4,
    "largura_base_b_m": "5/2",
    "espessura_crista_m": "3/10",
    "espessura_base_paramento_m": "1/2",
    "espessura_sapata_m": "2/5",
    "comprimento_ponta_m": "3/5",
    "profundidade_embutimento_d_m": "1/2",
    "fck_concreto_mpa": 25
  },
  "solo_reaterro": {
    "tipo_solo": "AREIA_MEDIA",
    "peso_especifico_kn_m3": 18,
    "angulo_atrito_graus": 30,
    "coesao_kpa": 0
  },
  "solo_fundacao": {
    "tipo_solo": "AREIA_COMPACTA",
    "peso_especifico_kn_m3": 19,
    "angulo_atrito_graus": 35,
    "coesao_kpa": 0,
    "coef_atrito_base_mu": "11/20",
    "tensao_admissivel_solo_fundacao_kpa": 300
  },
  "carregamentos": {
    "sobrecarga_uniforme_reaterro_kpa": 5,
    "altura_nivel_freatico_m": 0,
    "inclinacao_terrapleno_graus": 0
  }
}"""

    def test_carregar_json_valido(self):
        dados = carregar_projeto_muro_json(self.json_valido)
        self.assertEqual(dados.identificacao_projeto, "Contenção de Encosta Residencial")
        self.assertEqual(dados.tipo_muro, TipoMuro.CONCRETO_ARMADO_BALANCO)
        self.assertEqual(dados.geometria.altura_total_h_m, Fraction(4, 1))
        self.assertEqual(dados.geometria.largura_base_b_m, Fraction(5, 2))
        self.assertEqual(dados.solo_reaterro.angulo_atrito_graus, 30)

    def test_rejeitar_ponto_flutuante_float(self):
        json_com_float = self.json_valido.replace('"altura_total_h_m": 4', '"altura_total_h_m": 4.50')
        with self.assertRaises(ValueError) as ctx:
            carregar_projeto_muro_json(json_com_float)
        self.assertIn("Ponto flutuante IEEE-754", str(ctx.exception))

    def test_rejeitar_bom(self):
        json_bom = "\ufeff" + self.json_valido
        with self.assertRaises(ValueError) as ctx:
            carregar_projeto_muro_json(json_bom)
        self.assertIn("Byte Order Mark (BOM)", str(ctx.exception))

        json_bom_bytes = "\xef\xbb\xbf" + self.json_valido
        with self.assertRaises(ValueError) as ctx:
            carregar_projeto_muro_json(json_bom_bytes)
        self.assertIn("Byte Order Mark (BOM)", str(ctx.exception))

    def test_rejeitar_chaves_duplicadas(self):
        json_duplicado = """{
  "identificacao_projeto": "Projeto A",
  "identificacao_projeto": "Projeto B",
  "tipo_muro": "CONCRETO_ARMADO_BALANCO",
  "geometria": {"altura_total_h_m": 4, "largura_base_b_m": 2},
  "solo_reaterro": {"tipo_solo": "AREIA_MEDIA"},
  "solo_fundacao": {"tipo_solo": "AREIA_COMPACTA"},
  "carregamentos": {}
}"""
        with self.assertRaises(ValueError) as ctx:
            carregar_projeto_muro_json(json_duplicado)
        self.assertIn("Chave duplicada encontrada", str(ctx.exception))

    def test_rejeitar_profundidade_excessiva(self):
        d = {"nivel": 1}
        for _ in range(35):
            d = {"sub": d}
        json_profundo = json.dumps(d)
        with self.assertRaises(ValueError) as ctx:
            carregar_projeto_muro_json(json_profundo)
        self.assertIn("limite máximo permitido de 32", str(ctx.exception))

    def test_exportar_e_roundtrip_resultado(self):
        dados = carregar_projeto_muro_json(self.json_valido)
        res = dimensionar_projeto_muro_arrimo(dados)
        saida_json = exportar_resultado_json(res)
        self.assertIsInstance(saida_json, str)
        parsed = json.loads(saida_json)
        self.assertIn("normas_referencia", parsed)
        self.assertIn("empuxo_terra", parsed)
        self.assertIn("estabilidade_geotecnica", parsed)
        self.assertIn("verificacao_estrutural_paramento", parsed)

    def test_aliases_decodificar_codificar(self):
        dados = decodificar_json_projeto(self.json_valido)
        res = dimensionar_projeto_muro_arrimo(dados)
        txt1 = codificar_json_projeto(res)
        txt2 = codificar_json_projeto(dados, res)
        self.assertEqual(txt1, txt2)
        with self.assertRaises(ValueError):
            codificar_json_projeto("invalido")

    def test_rejeicao_json_nao_objeto(self):
        with self.assertRaises(ValueError):
            carregar_projeto_muro_json("[]")

    def test_rejeicao_campo_geometria_nao_objeto(self):
        json_sem_geo = '{"geometria": "invalido", "solo_reaterro": {}, "solo_fundacao": {}}'
        with self.assertRaises(ValueError):
            carregar_projeto_muro_json(json_sem_geo)


if __name__ == "__main__":
    unittest.main()
