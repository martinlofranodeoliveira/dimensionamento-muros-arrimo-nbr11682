"""Constantes normativas e parâmetros geotécnicos e estruturais para muros de arrimo.

Conforme normas ABNT NBR 11682:2009 (Estabilidade de Encostas) e ABNT NBR 6118:2023.
Aritmética 100% exata com números inteiros e frações racionais (fractions.Fraction).
Zero-Float garantido.
"""

from fractions import Fraction
from typing import NamedTuple


# Coeficientes de Ponderação e Fatores de Segurança Normativos (NBR 11682 Tabela 1)
FATOR_SEGURANCA_TOMBAMENTO_MINIMO = Fraction(3, 2)    # FS_tomb >= 1.50
FATOR_SEGURANCA_DESLIZAMENTO_MINIMO = Fraction(3, 2)  # FS_desl >= 1.50
FATOR_SEGURANCA_CAPACIDADE_CARGA_MINIMO = Fraction(2, 1)  # FS_solo >= 2.00

# Coeficientes de Ponderação Estruturais (NBR 6118)
GAMMA_CONCRETO = Fraction(14, 10)  # gamma_c = 1.40
GAMMA_ACO = Fraction(115, 100)     # gamma_s = 1.15
GAMMA_ACOES_DESFAVORAVEIS = Fraction(14, 10)  # gamma_f = 1.40

# Aço CA-50
FYK_ACO_CA50_MPA = Fraction(500, 1)
TAXA_ARMADURA_FLEXAO_MINIMA = Fraction(15, 10000)  # 0.15% da seção

# Pesos Específicos Padronizados (kN/m³)
PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3 = Fraction(25, 1)   # 25 kN/m³
PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3 = Fraction(22, 1) # 22 kN/m³
PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3 = Fraction(23, 1)   # 23 kN/m³
PESO_ESPECIFICO_GABIAO_KN_M3 = Fraction(19, 1)            # 19 kN/m³
PESO_ESPECIFICO_AGUA_KN_M3 = Fraction(10, 1)              # 10 kN/m³


class ParametrosSoloPadrao(NamedTuple):
    """Parâmetros semiempíricos de solo de reaterro e fundação."""
    nome: str
    peso_especifico_kn_m3: Fraction
    angulo_atrito_graus: int
    seno_phi: Fraction
    ka_rankine: Fraction          # Ka = (1 - sen(phi)) / (1 + sen(phi))
    kp_rankine: Fraction          # Kp = (1 + sen(phi)) / (1 - sen(phi))
    coef_atrito_base_mu: Fraction # tan(delta_base) na interface concreto-solo


TABELA_SOLOS_PADRAO: dict[str, ParametrosSoloPadrao] = {
    "AREIA_COMPACTA": ParametrosSoloPadrao(
        nome="Areia Grossa Compacta",
        peso_especifico_kn_m3=Fraction(19, 1),
        angulo_atrito_graus=35,
        seno_phi=Fraction(574, 1000),      # sen(35°) ~= 0.5736
        ka_rankine=Fraction(271, 1000),    # (1 - 0.5736)/(1 + 0.5736) ~= 0.271
        kp_rankine=Fraction(369, 100),     # 1 / 0.271 ~= 3.69
        coef_atrito_base_mu=Fraction(60, 100), # tan(2/3 * 35°) ~= 0.60
    ),
    "AREIA_MEDIA": ParametrosSoloPadrao(
        nome="Areia Média",
        peso_especifico_kn_m3=Fraction(18, 1),
        angulo_atrito_graus=30,
        seno_phi=Fraction(1, 2),           # sen(30°) = 0.5000 exato!
        ka_rankine=Fraction(1, 3),         # (1 - 0.5)/(1 + 0.5) = 1/3 exato!
        kp_rankine=Fraction(3, 1),         # 3.00 exato!
        coef_atrito_base_mu=Fraction(50, 100), # tan(20°) ~= 0.50
    ),
    "AREIA_FOFA": ParametrosSoloPadrao(
        nome="Areia Fofa / Silte Arenoso",
        peso_especifico_kn_m3=Fraction(17, 1),
        angulo_atrito_graus=28,
        seno_phi=Fraction(469, 1000),      # sen(28°) ~= 0.4695
        ka_rankine=Fraction(361, 1000),    # ~= 0.361
        kp_rankine=Fraction(277, 100),     # ~= 2.77
        coef_atrito_base_mu=Fraction(45, 100), # ~= 0.45
    ),
    "SILTE_ARGILOSO": ParametrosSoloPadrao(
        nome="Silte Argiloso Compacto",
        peso_especifico_kn_m3=Fraction(18, 1),
        angulo_atrito_graus=25,
        seno_phi=Fraction(423, 1000),      # sen(25°) ~= 0.4226
        ka_rankine=Fraction(406, 1000),    # ~= 0.406
        kp_rankine=Fraction(246, 100),     # ~= 2.46
        coef_atrito_base_mu=Fraction(40, 100), # ~= 0.40
    ),
    "ARGILA_MEDIA": ParametrosSoloPadrao(
        nome="Argila Média",
        peso_especifico_kn_m3=Fraction(17, 1),
        angulo_atrito_graus=20,
        seno_phi=Fraction(342, 1000),      # sen(20°) ~= 0.3420
        ka_rankine=Fraction(490, 1000),    # ~= 0.490
        kp_rankine=Fraction(204, 100),     # ~= 2.04
        coef_atrito_base_mu=Fraction(35, 100), # ~= 0.35
    ),
}
