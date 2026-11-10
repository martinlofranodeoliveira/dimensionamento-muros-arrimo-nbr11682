"""Modelos de dados tipados para dimensionamento de muros de arrimo NBR 11682 / NBR 6118.

Aritmética estritamente racional e inteira (Zero-Float).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Tuple


class TipoMuro(str, Enum):
    """Tipologia construtiva da obra de contenção."""
    CONCRETO_ARMADO_BALANCO = "CONCRETO_ARMADO_BALANCO"
    GRAVIDADE_CONCRETO_CICLOPICO = "GRAVIDADE_CONCRETO_CICLOPICO"
    GRAVIDADE_ALVENARIA_PEDRA = "GRAVIDADE_ALVENARIA_PEDRA"
    GRAVIDADE_GABIAO = "GRAVIDADE_GABIAO"


class MetodoEmpuxo(str, Enum):
    """Método analítico de cálculo do empuxo de terra."""
    RANKINE = "RANKINE"
    COULOMB = "COULOMB"


class TipoCondicaoDrenagem(str, Enum):
    """Condição do sistema de barbacãs e drenagem profunda."""
    DRENAGEM_EFICIENTE_SEM_AGUA = "DRENAGEM_EFICIENTE_SEM_AGUA"
    PRESENCA_NIVEL_FREATICO = "PRESENCA_NIVEL_FREATICO"


@dataclass(frozen=True)
class GeometriaMuro:
    """Dimensões geométricas da seção transversal do muro de arrimo."""
    altura_total_h_m: Fraction
    largura_base_b_m: Fraction
    espessura_crista_m: Fraction
    espessura_base_paramento_m: Fraction
    espessura_sapata_m: Fraction = Fraction(0, 1)          # Apenas para concreto armado
    comprimento_ponta_m: Fraction = Fraction(0, 1)         # Balanço frontal da sapata (ponta)
    profundidade_embutimento_d_m: Fraction = Fraction(0, 1)# Embutimento frontal
    altura_dente_cisalhamento_m: Fraction = Fraction(0, 1) # Chave de cisalhamento
    largura_dente_cisalhamento_m: Fraction = Fraction(0, 1)
    fck_concreto_mpa: Fraction = Fraction(25, 1)


@dataclass(frozen=True)
class PropriedadesSolo:
    """Propriedades geotécnicas do solo de reaterro ou fundação."""
    tipo_solo: str
    peso_especifico_kn_m3: Fraction
    angulo_atrito_graus: int
    coesao_kpa: Fraction = Fraction(0, 1)
    coef_atrito_base_mu: Fraction = Fraction(50, 100)
    tensao_admissivel_solo_fundacao_kpa: Fraction = Fraction(250, 1)


@dataclass(frozen=True)
class CarregamentosExternos:
    """Ações atuantes sobre o muro de arrimo e terrapleno."""
    sobrecarga_uniforme_reaterro_kpa: Fraction = Fraction(0, 1)
    altura_nivel_freatico_m: Fraction = Fraction(0, 1) # Acima da base do muro
    inclinacao_terrapleno_graus: int = 0               # Beta


@dataclass(frozen=True)
class ComponenteForca:
    """Componente individual de equilíbrio estático da estrutura."""
    descricao: str
    forca_vertical_kn: Fraction
    forca_horizontal_kn: Fraction
    braco_x_m: Fraction # Em relação à ponta frontal inferior
    braco_y_m: Fraction
    momento_estabilizante_knm: Fraction
    momento_tombante_knm: Fraction


@dataclass(frozen=True)
class ResultadoEmpuxo:
    """Parâmetros e magnitudes dos empuxos de terra e água."""
    metodo: str
    coeficiente_ka: Fraction
    coeficiente_kp: Fraction
    empuxo_solo_horizontal_kn: Fraction
    empuxo_sobrecarga_horizontal_kn: Fraction
    empuxo_hidrostatico_horizontal_kn: Fraction
    empuxo_total_horizontal_kn: Fraction
    ponto_aplicacao_empuxo_y_m: Fraction
    empuxo_passivo_disponivel_kn: Fraction


@dataclass(frozen=True)
class ResultadoEstabilidadeGeotecnica:
    """Resultados das verificações de equilíbrio global do muro de arrimo."""
    forca_normal_total_base_kn: Fraction
    forca_horizontal_solicitante_kn: Fraction
    forca_resistente_deslizamento_kn: Fraction
    momento_estabilizante_total_knm: Fraction
    momento_tombante_total_knm: Fraction
    fator_seguranca_tombamento: Fraction
    fator_seguranca_deslizamento: Fraction
    posicao_resultante_base_x_m: Fraction
    excentricidade_base_e_m: Fraction
    limite_terco_medio_m: Fraction # B / 6
    dentro_do_terco_medio: bool
    tensao_maxima_base_kpa: Fraction
    tensao_minima_base_kpa: Fraction
    tensao_admissivel_kpa: Fraction
    aprovado_tombamento: bool
    aprovado_deslizamento: bool
    aprovado_capacidade_carga: bool


@dataclass(frozen=True)
class ResultadoEstruturalMuro:
    """Dimensionamento das armaduras e seção de concreto armado (NBR 6118)."""
    momento_fletor_calculo_base_md_knm: Fraction
    forca_cortante_calculo_base_vd_kn: Fraction
    area_armadura_flexao_cm2_m: Fraction
    area_armadura_minima_cm2_m: Fraction
    area_armadura_adotada_cm2_m: Fraction
    resistencia_cisalhamento_concreto_vrd1_kn: Fraction
    aprovado_cisalhamento: bool
    aprovado_estruturalmente: bool


@dataclass(frozen=True)
class DadosProjetoMuroArrimo:
    """Conjunto completo de dados de entrada do projeto de contenção."""
    identificacao_projeto: str
    tipo_muro: TipoMuro
    geometria: GeometriaMuro
    solo_reaterro: PropriedadesSolo
    solo_fundacao: PropriedadesSolo
    carregamentos: CarregamentosExternos
    responsavel_tecnico: str = "Engenharia Geotécnica"


@dataclass(frozen=True)
class ResultadoProjetoMuroArrimo:
    """Resultado executivo completo do dimensionamento do muro de arrimo."""
    identificacao_projeto: str
    tipo_muro: TipoMuro
    geometria: GeometriaMuro
    solo_reaterro: PropriedadesSolo
    solo_fundacao: PropriedadesSolo
    carregamentos: CarregamentosExternos
    empuxo: ResultadoEmpuxo
    estabilidade: ResultadoEstabilidadeGeotecnica
    componentes_estabilidade: Tuple[ComponenteForca, ...]
    estrutural: ResultadoEstruturalMuro | None
    aprovado_globalmente: bool
    conformidade_geral: bool
    alertas_tecnicos: Tuple[str, ...]
