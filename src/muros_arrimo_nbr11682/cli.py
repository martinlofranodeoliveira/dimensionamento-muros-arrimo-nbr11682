"""Interface de Linha de Comando (CLI) para dimensionamento de muros de arrimo NBR 11682:2009.

Desenvolvido por LOFRANO TECNOLOGIA.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from muros_arrimo_nbr11682 import __version__
from muros_arrimo_nbr11682.calculator import dimensionar_projeto_muro_arrimo
from muros_arrimo_nbr11682.codecs import codificar_json_projeto, decodificar_json_projeto
from muros_arrimo_nbr11682.constants import TABELA_SOLOS_PADRAO
from muros_arrimo_nbr11682.exporters import (
    exportar_csv_resumo,
    exportar_memorial_descritivo,
    gerar_pacote_completo_zip,
)
from muros_arrimo_nbr11682.svg_generator import gerar_painel_svg

EXEMPLO_CONCRETO_BALANCO = """{
  "identificacao_projeto": "Contenção Residencial Parque das Colinas",
  "tipo_muro": "CONCRETO_ARMADO_BALANCO",
  "responsavel_tecnico": "Eng. Martin Lofrano de Oliveira - CREA/SP",
  "geometria": {
    "altura_total_h_m": "4.50",
    "largura_base_b_m": "2.80",
    "espessura_crista_m": "0.30",
    "espessura_base_paramento_m": "0.50",
    "espessura_sapata_m": "0.45",
    "comprimento_ponta_m": "0.70",
    "profundidade_embutimento_d_m": "0.60",
    "altura_dente_cisalhamento_m": 0,
    "largura_dente_cisalhamento_m": 0,
    "fck_concreto_mpa": 30
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
    "coef_atrito_base_mu": "0.55",
    "tensao_admissivel_solo_fundacao_kpa": 300
  },
  "carregamentos": {
    "sobrecarga_uniforme_reaterro_kpa": "10.0",
    "altura_nivel_freatico_m": 0,
    "inclinacao_terrapleno_graus": 0
  }
}"""

EXEMPLO_GRAVIDADE_CICLOPE = """{
  "identificacao_projeto": "Muro de Gravidade Rodovia SP-330",
  "tipo_muro": "GRAVIDADE_CONCRETO_CICLOPICO",
  "responsavel_tecnico": "Eng. Martin Lofrano de Oliveira - CREA/SP",
  "geometria": {
    "altura_total_h_m": "3.20",
    "largura_base_b_m": "1.80",
    "espessura_crista_m": "0.50",
    "espessura_base_paramento_m": "1.80",
    "espessura_sapata_m": 0,
    "comprimento_ponta_m": 0,
    "profundidade_embutimento_d_m": "0.50",
    "fck_concreto_mpa": 20
  },
  "solo_reaterro": {
    "tipo_solo": "AREIA_FOFA",
    "peso_especifico_kn_m3": 17,
    "angulo_atrito_graus": 28,
    "coesao_kpa": 0
  },
  "solo_fundacao": {
    "tipo_solo": "AREIA_MEDIA",
    "peso_especifico_kn_m3": 18,
    "angulo_atrito_graus": 30,
    "coesao_kpa": 0,
    "coef_atrito_base_mu": "0.50",
    "tensao_admissivel_solo_fundacao_kpa": 250
  },
  "carregamentos": {
    "sobrecarga_uniforme_reaterro_kpa": "5.0",
    "altura_nivel_freatico_m": 0,
    "inclinacao_terrapleno_graus": 0
  }
}"""

EXEMPLO_GABIAO = """{
  "identificacao_projeto": "Contenção em Gabiões Córrego Verde",
  "tipo_muro": "GRAVIDADE_GABIAO",
  "responsavel_tecnico": "Eng. Martin Lofrano de Oliveira - CREA/SP",
  "geometria": {
    "altura_total_h_m": "4.00",
    "largura_base_b_m": "2.50",
    "espessura_crista_m": "1.00",
    "espessura_base_paramento_m": "2.50",
    "espessura_sapata_m": 0,
    "comprimento_ponta_m": 0,
    "profundidade_embutimento_d_m": "0.50",
    "fck_concreto_mpa": 0
  },
  "solo_reaterro": {
    "tipo_solo": "SILTE_ARGILOSO",
    "peso_especifico_kn_m3": 18,
    "angulo_atrito_graus": 25,
    "coesao_kpa": 0
  },
  "solo_fundacao": {
    "tipo_solo": "AREIA_COMPACTA",
    "peso_especifico_kn_m3": 19,
    "angulo_atrito_graus": 34,
    "coesao_kpa": 0,
    "coef_atrito_base_mu": "0.55",
    "tensao_admissivel_solo_fundacao_kpa": 280
  },
  "carregamentos": {
    "sobrecarga_uniforme_reaterro_kpa": "5.0",
    "altura_nivel_freatico_m": 0,
    "inclinacao_terrapleno_graus": 0
  }
}"""


def criar_parser() -> argparse.ArgumentParser:
    """Cria e configura o analisador de argumentos da CLI."""
    parser = argparse.ArgumentParser(
        prog="muros-arrimo-nbr11682",
        description="Dimensionamento analítico determinístico de muros de contenção e arrimo conforme ABNT NBR 11682:2009 e NBR 6118:2023.",
        add_help=False,
    )

    parser.add_argument(
        "-a",
        "--ajuda",
        action="help",
        help="Exibe esta mensagem de ajuda e encerra.",
    )
    parser.add_argument(
        "-v",
        "--versao",
        action="version",
        version=f"%(prog)s {__version__} (LOFRANO TECNOLOGIA)",
        help="Exibe a versão do programa e encerra.",
    )

    subparsers = parser.add_subparsers(dest="comando", help="Comando a ser executado")

    # Subcomando 'calcular'
    parser_calc = subparsers.add_parser(
        "calcular",
        help="Executa o dimensionamento da contenção a partir de arquivo JSON.",
        add_help=False,
    )
    parser_calc.add_argument(
        "-a",
        "--ajuda",
        action="help",
        help="Exibe a ajuda do subcomando calcular.",
    )
    parser_calc.add_argument(
        "entrada",
        nargs="?",
        type=str,
        help="Caminho do arquivo JSON de entrada (ou '-' para entrada padrão stdin).",
    )
    parser_calc.add_argument(
        "-o",
        "--saida",
        type=str,
        help="Caminho do arquivo JSON de saída dos resultados.",
    )
    parser_calc.add_argument(
        "--memorial",
        type=str,
        help="Gera memorial técnico descritivo em formato texto/markdown.",
    )
    parser_calc.add_argument(
        "--csv",
        type=str,
        help="Gera planilha técnica resumida em formato CSV sanitizado.",
    )
    parser_calc.add_argument(
        "--svg",
        type=str,
        help="Gera painel visual esquemático de engenharia em formato vetorial SVG.",
    )
    parser_calc.add_argument(
        "--pacote-zip",
        type=str,
        help="Gera arquivo compactado ZIP determinístico com todos os artefatos de saída.",
    )

    # Subcomando 'catalogo'
    subparsers.add_parser(
        "catalogo",
        help="Exibe catálogo geotécnico de solos e coeficientes de empuxo de terra.",
    )

    # Subcomando 'gerar-exemplo'
    parser_ex = subparsers.add_parser(
        "gerar-exemplo",
        help="Gera arquivo JSON de exemplo pronto para edição e cálculo.",
        add_help=False,
    )
    parser_ex.add_argument(
        "-a",
        "--ajuda",
        action="help",
        help="Exibe a ajuda do subcomando gerar-exemplo.",
    )
    parser_ex.add_argument(
        "-t",
        "--tipo",
        choices=["concreto-balanco", "gravidade-ciclope", "gabiao"],
        default="concreto-balanco",
        help="Tipo de contenção a gerar no exemplo (concreto-balanco, gravidade-ciclope ou gabiao).",
    )
    parser_ex.add_argument(
        "-o",
        "--saida",
        type=str,
        help="Caminho do arquivo para gravação do exemplo JSON.",
    )

    return parser


def comando_catalogo() -> int:
    """Exibe o catálogo geotécnico com parâmetros e coeficientes normativos de solos."""
    print("=" * 80)
    print("CATÁLOGO GEOTÉCNICO DE SOLOS E COEFICIENTES DE EMPUXO (ABNT NBR 11682:2009)")
    print("=" * 80)
    print("\n1. SOLOS PADRONIZADOS E COEFICIENTES DE EMPUXO DE RANKINE:")
    print(f"{'Tipo de Solo':<22} | {'gamma (kN/m³)':<14} | {'phi (°)':<8} | {'Ka Rankine':<12} | {'Kp Rankine':<12}")
    print("-" * 80)
    for k, p in TABELA_SOLOS_PADRAO.items():
        ka_str = f"{p.ka_rankine.numerator}/{p.ka_rankine.denominator}"
        kp_str = f"{p.kp_rankine.numerator}/{p.kp_rankine.denominator}"
        print(f"{k:<22} | {p.peso_especifico_kn_m3} kN/m³        | {p.angulo_atrito_graus}°     | {ka_str:<12} | {kp_str:<12}")

    print("\n2. FATORES DE SEGURANÇA MÍNIMOS OBRIGATÓRIOS (NBR 11682):")
    print(" - Segurança ao Tombamento:     FS_tomb >= 1,50")
    print(" - Segurança ao Deslizamento:   FS_desl >= 1,50")
    print(" - Terço Médio da Base:         e <= B/6 (evita tração na interface solo-muro)")
    print(" - Armadura Longitudinal Mín.:  0,15% da seção de concreto (NBR 6118:2023)")
    print("=" * 80)
    return 0


def comando_gerar_exemplo(tipo: str, saida: str | None) -> int:
    """Gera um arquivo JSON de exemplo pronto para simulação."""
    if tipo == "gravidade-ciclope":
        conteudo = EXEMPLO_GRAVIDADE_CICLOPE
    elif tipo == "gabiao":
        conteudo = EXEMPLO_GABIAO
    else:
        conteudo = EXEMPLO_CONCRETO_BALANCO

    if saida:
        path = Path(saida)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(conteudo, encoding="utf-8")
        print(f"Exemplo JSON gerado com sucesso em: {saida}")
    else:
        print(conteudo)
    return 0


def comando_calcular(
    entrada: str | None,
    saida: str | None,
    memorial: str | None,
    csv: str | None,
    svg: str | None,
    pacote_zip: str | None,
) -> int:
    """Executa o cálculo analítico de dimensionamento da contenção."""
    if not entrada or entrada == "-":
        texto = sys.stdin.read()
    else:
        path_in = Path(entrada)
        if not path_in.exists():
            print(f"Erro: Arquivo de entrada não encontrado: {entrada}", file=sys.stderr)
            return 1
        texto = path_in.read_text(encoding="utf-8")

    try:
        dados = decodificar_json_projeto(texto)
        resultado = dimensionar_projeto_muro_arrimo(dados)
    except Exception as exc:
        print(f"Erro durante o processamento do dimensionamento: {exc}", file=sys.stderr)
        return 1

    json_res = codificar_json_projeto(resultado)

    if saida:
        path_out = Path(saida)
        path_out.parent.mkdir(parents=True, exist_ok=True)
        path_out.write_text(json_res, encoding="utf-8")
        print(f"Resultados exportados em JSON: {saida}")
    else:
        if not memorial and not csv and not svg and not pacote_zip:
            print(json_res)

    if memorial:
        path_mem = Path(memorial)
        path_mem.parent.mkdir(parents=True, exist_ok=True)
        txt_mem = exportar_memorial_descritivo(resultado)
        path_mem.write_text(txt_mem, encoding="utf-8")
        print(f"Memorial descritivo gerado: {memorial}")

    if csv:
        path_csv = Path(csv)
        path_csv.parent.mkdir(parents=True, exist_ok=True)
        txt_csv = exportar_csv_resumo(resultado)
        path_csv.write_text(txt_csv, encoding="utf-8")
        print(f"Planilha CSV gerada: {csv}")

    if svg:
        path_svg = Path(svg)
        path_svg.parent.mkdir(parents=True, exist_ok=True)
        txt_svg = gerar_painel_svg(resultado)
        path_svg.write_text(txt_svg, encoding="utf-8")
        print(f"Painel vetorial SVG gerado: {svg}")

    if pacote_zip:
        path_zip = Path(pacote_zip)
        path_zip.parent.mkdir(parents=True, exist_ok=True)
        gerar_pacote_completo_zip(resultado, str(path_zip))
        print(f"Pacote ZIP determinístico gerado: {pacote_zip}")

    return 0


def main(args: list[str] | None = None) -> int:
    """Ponto de entrada principal da CLI."""
    parser = criar_parser()
    parsed = parser.parse_args(args)

    if not parsed.comando:
        parser.print_help()
        return 0

    if parsed.comando == "catalogo":
        return comando_catalogo()

    if parsed.comando == "gerar-exemplo":
        return comando_gerar_exemplo(parsed.tipo, parsed.saida)

    if parsed.comando == "calcular":
        return comando_calcular(
            entrada=parsed.entrada,
            saida=parsed.saida,
            memorial=parsed.memorial,
            csv=parsed.csv,
            svg=parsed.svg,
            pacote_zip=parsed.pacote_zip,
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
