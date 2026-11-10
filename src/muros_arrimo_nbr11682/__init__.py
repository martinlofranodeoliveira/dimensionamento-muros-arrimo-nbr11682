"""Dimensionamento de Muros de Arrimo e Obras de Contenção (ABNT NBR 11682 / NBR 6118).

LOFRANO TECNOLOGIA - Engenharia Geotécnica e Estrutural.
Aritmética 100% racional (Zero-Float).
"""

from __future__ import annotations

from muros_arrimo_nbr11682.calculator import (
    calcular_componentes_estabilidade,
    calcular_empuxos_terra,
    dimensionar_estrutural_paramento,
    dimensionar_projeto_muro_arrimo,
    obter_coeficientes_empuxo,
    obter_peso_especifico_muro,
    verificar_estabilidade_geotecnica,
)
from muros_arrimo_nbr11682.codecs import (
    carregar_projeto_muro_json,
    codificar_json_projeto,
    decodificar_json_projeto,
    exportar_resultado_json,
)
from muros_arrimo_nbr11682.constants import (
    FATOR_SEGURANCA_CAPACIDADE_CARGA_MINIMO,
    FATOR_SEGURANCA_DESLIZAMENTO_MINIMO,
    FATOR_SEGURANCA_TOMBAMENTO_MINIMO,
    PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3,
    PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3,
    PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3,
    PESO_ESPECIFICO_GABIAO_KN_M3,
    TABELA_SOLOS_PADRAO,
)
from muros_arrimo_nbr11682.exporters import (
    exportar_csv_resumo,
    exportar_memorial_descritivo,
    gerar_csv_resumo_muro,
    gerar_memorial_muro_texto,
    gerar_pacote_completo_zip,
    gerar_pacote_zip_muro,
)
from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    ComponenteForca,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    MetodoEmpuxo,
    PropriedadesSolo,
    ResultadoEmpuxo,
    ResultadoEstabilidadeGeotecnica,
    ResultadoEstruturalMuro,
    ResultadoProjetoMuroArrimo,
    TipoCondicaoDrenagem,
    TipoMuro,
)
from muros_arrimo_nbr11682.svg_generator import gerar_painel_svg

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "TipoMuro",
    "MetodoEmpuxo",
    "TipoCondicaoDrenagem",
    "GeometriaMuro",
    "PropriedadesSolo",
    "CarregamentosExternos",
    "ComponenteForca",
    "ResultadoEmpuxo",
    "ResultadoEstabilidadeGeotecnica",
    "ResultadoEstruturalMuro",
    "DadosProjetoMuroArrimo",
    "ResultadoProjetoMuroArrimo",
    "calcular_empuxos_terra",
    "calcular_componentes_estabilidade",
    "verificar_estabilidade_geotecnica",
    "dimensionar_estrutural_paramento",
    "dimensionar_projeto_muro_arrimo",
    "obter_coeficientes_empuxo",
    "obter_peso_especifico_muro",
    "carregar_projeto_muro_json",
    "exportar_resultado_json",
    "decodificar_json_projeto",
    "codificar_json_projeto",
    "gerar_memorial_muro_texto",
    "gerar_csv_resumo_muro",
    "gerar_pacote_zip_muro",
    "exportar_memorial_descritivo",
    "exportar_csv_resumo",
    "gerar_pacote_completo_zip",
    "gerar_painel_svg",
    "FATOR_SEGURANCA_TOMBAMENTO_MINIMO",
    "FATOR_SEGURANCA_DESLIZAMENTO_MINIMO",
    "FATOR_SEGURANCA_CAPACIDADE_CARGA_MINIMO",
    "PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3",
    "PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3",
    "PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3",
    "PESO_ESPECIFICO_GABIAO_KN_M3",
    "TABELA_SOLOS_PADRAO",
]
