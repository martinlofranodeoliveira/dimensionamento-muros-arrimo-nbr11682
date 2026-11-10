"""Motor analítico determinístico de dimensionamento de muros de arrimo NBR 11682 / NBR 6118.

Executa o cálculo de empuxos de terra (Rankine), equilíbrio estático de forças e momentos,
verificações de estabilidade geotécnica (tombamento, deslizamento, tensões na base) e
dimensionamento estrutural do paramento em concreto armado.
Aritmética 100% exata com números inteiros e frações racionais (Zero-Float).
"""

from __future__ import annotations

from fractions import Fraction
from typing import List, Tuple

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
from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    ComponenteForca,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    PropriedadesSolo,
    ResultadoEmpuxo,
    ResultadoEstabilidadeGeotecnica,
    ResultadoEstruturalMuro,
    ResultadoProjetoMuroArrimo,
    TipoMuro,
)


def obter_peso_especifico_muro(tipo_muro: TipoMuro) -> Fraction:
    """Retorna o peso específico volumétrico do material da contenção em kN/m³."""
    if tipo_muro == TipoMuro.CONCRETO_ARMADO_BALANCO:
        return PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3
    elif tipo_muro == TipoMuro.GRAVIDADE_CONCRETO_CICLOPICO:
        return PESO_ESPECIFICO_CONCRETO_CICLOPICO_KN_M3
    elif tipo_muro == TipoMuro.GRAVIDADE_ALVENARIA_PEDRA:
        return PESO_ESPECIFICO_ALVENARIA_PEDRA_KN_M3
    elif tipo_muro == TipoMuro.GRAVIDADE_GABIAO:
        return PESO_ESPECIFICO_GABIAO_KN_M3
    return PESO_ESPECIFICO_CONCRETO_ARMADO_KN_M3


def obter_coeficientes_empuxo(solo: PropriedadesSolo) -> Tuple[Fraction, Fraction]:
    """Retorna os coeficientes de empuxo ativo Ka e passivo Kp de Rankine em frações exatas."""
    chave = solo.tipo_solo.upper().strip()
    if chave in TABELA_SOLOS_PADRAO:
        p = TABELA_SOLOS_PADRAO[chave]
        return p.ka_rankine, p.kp_rankine

    # Cálculo a partir do ângulo de atrito aproximado via tabela ou valor conservador
    phi = solo.angulo_atrito_graus
    if phi >= 35:
        return Fraction(271, 1000), Fraction(369, 100)
    elif phi >= 30:
        return Fraction(1, 3), Fraction(3, 1)
    elif phi >= 28:
        return Fraction(361, 1000), Fraction(277, 100)
    elif phi >= 25:
        return Fraction(406, 1000), Fraction(246, 100)
    else:
        return Fraction(490, 1000), Fraction(204, 100)


def calcular_empuxos_terra(
    geometria: GeometriaMuro,
    solo: PropriedadesSolo,
    carregamentos: CarregamentosExternos,
) -> ResultadoEmpuxo:
    """Calcula os empuxos ativo de terra, sobrecarga e água atuantes na contenção."""
    ka, kp = obter_coeficientes_empuxo(solo)
    h = geometria.altura_total_h_m

    # 1. Empuxo ativo do solo (diagrama triangular)
    # Ea_solo = 0.5 * gamma * H^2 * Ka
    empuxo_solo_h = Fraction(1, 2) * solo.peso_especifico_kn_m3 * (h * h) * ka
    momento_solo_base = empuxo_solo_h * (h / Fraction(3, 1))

    # 2. Empuxo ativo de sobrecarga uniforme (diagrama retangular)
    # Ea_q = q * Ka * H
    empuxo_q_h = carregamentos.sobrecarga_uniforme_reaterro_kpa * ka * h
    momento_q_base = empuxo_q_h * (h / Fraction(2, 1))

    # 3. Empuxo hidrostático se houver nível freático acima da base
    hw = min(h, carregamentos.altura_nivel_freatico_m)
    if hw > Fraction(0, 1):
        empuxo_w_h = Fraction(1, 2) * PESO_ESPECIFICO_AGUA_KN_M3 * (hw * hw)
        momento_w_base = empuxo_w_h * (hw / Fraction(3, 1))
    else:
        empuxo_w_h = Fraction(0, 1)
        momento_w_base = Fraction(0, 1)

    empuxo_total_h = empuxo_solo_h + empuxo_q_h + empuxo_w_h

    # Ponto de aplicação ponderado da resultante do empuxo acima da base
    if empuxo_total_h > Fraction(0, 1):
        momento_total_base = momento_solo_base + momento_q_base + momento_w_base
        y_resultante = momento_total_base / empuxo_total_h
    else:
        y_resultante = Fraction(0, 1)

    # 4. Empuxo passivo frontal disponível no embutimento
    d = geometria.profundidade_embutimento_d_m
    if d > Fraction(0, 1):
        empuxo_passivo_disp = Fraction(1, 2) * solo.peso_especifico_kn_m3 * (d * d) * kp
    else:
        empuxo_passivo_disp = Fraction(0, 1)

    return ResultadoEmpuxo(
        metodo="Rankine (1857)",
        coeficiente_ka=ka,
        coeficiente_kp=kp,
        empuxo_solo_horizontal_kn=empuxo_solo_h,
        empuxo_sobrecarga_horizontal_kn=empuxo_q_h,
        empuxo_hidrostatico_horizontal_kn=empuxo_w_h,
        empuxo_total_horizontal_kn=empuxo_total_h,
        ponto_aplicacao_empuxo_y_m=y_resultante,
        empuxo_passivo_disponivel_kn=empuxo_passivo_disp,
    )


def calcular_componentes_estabilidade(
    tipo_muro: TipoMuro,
    geometria: GeometriaMuro,
    solo: PropriedadesSolo,
    carregamentos: CarregamentosExternos,
    empuxo: ResultadoEmpuxo,
) -> Tuple[List[ComponenteForca], Fraction, Fraction, Fraction]:
    """Calcula o peso de cada bloco geométrico, solo sobre o talão e momentos em relação ao pé frontal."""
    componentes: List[ComponenteForca] = []
    gamma_mat = obter_peso_especifico_muro(tipo_muro)
    b = geometria.largura_base_b_m
    h = geometria.altura_total_h_m

    if tipo_muro == TipoMuro.CONCRETO_ARMADO_BALANCO:
        h_sap = geometria.espessura_sapata_m
        if h_sap <= Fraction(0, 1):
            h_sap = max(Fraction(3, 10), h / Fraction(10, 1)) # mínimo 30cm ou H/10
        h_par = h - h_sap
        l_ponta = geometria.comprimento_ponta_m
        b_base = geometria.espessura_base_paramento_m
        b_crista = geometria.espessura_crista_m
        l_talao = b - l_ponta - b_base

        if l_talao < Fraction(0, 1):
            l_talao = Fraction(0, 1)

        # 1. Sapata do Muro (Retângulo B x h_sap)
        w_sap = b * h_sap * gamma_mat
        braco_x_sap = b / Fraction(2, 1)
        componentes.append(
            ComponenteForca(
                descricao="Peso Próprio da Sapata / Base",
                forca_vertical_kn=w_sap,
                forca_horizontal_kn=Fraction(0, 1),
                braco_x_m=braco_x_sap,
                braco_y_m=h_sap / Fraction(2, 1),
                momento_estabilizante_knm=w_sap * braco_x_sap,
                momento_tombante_knm=Fraction(0, 1),
            )
        )

        # 2. Paramento Retangular (b_crista x h_par)
        w_par_ret = b_crista * h_par * gamma_mat
        braco_x_par_ret = l_ponta + (b_crista / Fraction(2, 1))
        componentes.append(
            ComponenteForca(
                descricao="Peso do Paramento (Trecho Retangular)",
                forca_vertical_kn=w_par_ret,
                forca_horizontal_kn=Fraction(0, 1),
                braco_x_m=braco_x_par_ret,
                braco_y_m=h_sap + (h_par / Fraction(2, 1)),
                momento_estabilizante_knm=w_par_ret * braco_x_par_ret,
                momento_tombante_knm=Fraction(0, 1),
            )
        )

        # 3. Paramento Triangular (se b_base > b_crista)
        delta_b = b_base - b_crista
        if delta_b > Fraction(0, 1):
            w_par_tri = Fraction(1, 2) * delta_b * h_par * gamma_mat
            braco_x_par_tri = l_ponta + b_crista + (delta_b / Fraction(3, 1))
            componentes.append(
                ComponenteForca(
                    descricao="Peso do Paramento (Trecho Triangular / Escalonado)",
                    forca_vertical_kn=w_par_tri,
                    forca_horizontal_kn=Fraction(0, 1),
                    braco_x_m=braco_x_par_tri,
                    braco_y_m=h_sap + (h_par / Fraction(3, 1)),
                    momento_estabilizante_knm=w_par_tri * braco_x_par_tri,
                    momento_tombante_knm=Fraction(0, 1),
                )
            )

        # 4. Peso do Prisma de Solo sobre o Talão Posterior
        if l_talao > Fraction(0, 1):
            w_solo_talao = l_talao * h_par * solo.peso_especifico_kn_m3
            braco_x_solo = b - (l_talao / Fraction(2, 1))
            componentes.append(
                ComponenteForca(
                    descricao="Peso do Solo sobre o Talão Posterior",
                    forca_vertical_kn=w_solo_talao,
                    forca_horizontal_kn=Fraction(0, 1),
                    braco_x_m=braco_x_solo,
                    braco_y_m=h_sap + (h_par / Fraction(2, 1)),
                    momento_estabilizante_knm=w_solo_talao * braco_x_solo,
                    momento_tombante_knm=Fraction(0, 1),
                )
            )

            # 5. Sobrecarga Uniforme sobre o Talão Posterior
            if carregamentos.sobrecarga_uniforme_reaterro_kpa > Fraction(0, 1):
                w_q_talao = carregamentos.sobrecarga_uniforme_reaterro_kpa * l_talao
                componentes.append(
                    ComponenteForca(
                        descricao="Sobrecarga Acidental sobre o Talão Posterior",
                        forca_vertical_kn=w_q_talao,
                        forca_horizontal_kn=Fraction(0, 1),
                        braco_x_m=braco_x_solo,
                        braco_y_m=h,
                        momento_estabilizante_knm=w_q_talao * braco_x_solo,
                        momento_tombante_knm=Fraction(0, 1),
                    )
                )

    else:
        # Muro de Gravidade (Concreto Ciclópico, Alvenaria de Pedra ou Gabião)
        # Seção trapezoidal: base inferior B, topo b_crista
        b_crista = geometria.espessura_crista_m
        b_base = geometria.espessura_base_paramento_m if geometria.espessura_base_paramento_m > Fraction(0, 1) else b

        # Bloco retangular central
        b_ret = min(b, b_crista)
        w_ret = b_ret * h * gamma_mat
        braco_x_ret = b_ret / Fraction(2, 1)
        componentes.append(
            ComponenteForca(
                descricao="Peso da Seção Retangular do Muro de Gravidade",
                forca_vertical_kn=w_ret,
                forca_horizontal_kn=Fraction(0, 1),
                braco_x_m=braco_x_ret,
                braco_y_m=h / Fraction(2, 1),
                momento_estabilizante_knm=w_ret * braco_x_ret,
                momento_tombante_knm=Fraction(0, 1),
            )
        )

        # Bloco triangular posterior (se houver inclinação no paramento posterior)
        delta_b_post = b - b_ret
        if delta_b_post > Fraction(0, 1):
            w_tri = Fraction(1, 2) * delta_b_post * h * gamma_mat
            # Centroide do triângulo com ângulo reto na base posterior (x=B):
            braco_x_tri = b_ret + (delta_b_post * Fraction(2, 3))
            componentes.append(
                ComponenteForca(
                    descricao="Peso da Cunha Triangular do Muro de Gravidade",
                    forca_vertical_kn=w_tri,
                    forca_horizontal_kn=Fraction(0, 1),
                    braco_x_m=braco_x_tri,
                    braco_y_m=h / Fraction(3, 1),
                    momento_estabilizante_knm=w_tri * braco_x_tri,
                    momento_tombante_knm=Fraction(0, 1),
                )
            )

            # Cunha de solo de reaterro apoiada sobre o paramento posterior inclinado
            w_solo_inc = Fraction(1, 2) * delta_b_post * h * solo.peso_especifico_kn_m3
            braco_x_solo_inc = b_ret + (delta_b_post / Fraction(3, 1))
            componentes.append(
                ComponenteForca(
                    descricao="Peso do Reaterro sobre o Paramento Posterior Inclinado",
                    forca_vertical_kn=w_solo_inc,
                    forca_horizontal_kn=Fraction(0, 1),
                    braco_x_m=braco_x_solo_inc,
                    braco_y_m=h * Fraction(2, 3),
                    momento_estabilizante_knm=w_solo_inc * braco_x_solo_inc,
                    momento_tombante_knm=Fraction(0, 1),
                )
            )

    # Dente de cisalhamento se fornecido
    if geometria.altura_dente_cisalhamento_m > Fraction(0, 1) and geometria.largura_dente_cisalhamento_m > Fraction(0, 1):
        w_dente = geometria.altura_dente_cisalhamento_m * geometria.largura_dente_cisalhamento_m * gamma_mat
        braco_x_dente = b / Fraction(2, 1)
        componentes.append(
            ComponenteForca(
                descricao="Peso do Dente de Cisalhamento da Fundação",
                forca_vertical_kn=w_dente,
                forca_horizontal_kn=Fraction(0, 1),
                braco_x_m=braco_x_dente,
                braco_y_m=-geometria.altura_dente_cisalhamento_m / Fraction(2, 1),
                momento_estabilizante_knm=w_dente * braco_x_dente,
                momento_tombante_knm=Fraction(0, 1),
            )
        )

    # Somatório de forças verticais e momentos estabilizantes
    normal_total = sum((c.forca_vertical_kn for c in componentes), Fraction(0, 1))
    momento_estab_total = sum((c.momento_estabilizante_knm for c in componentes), Fraction(0, 1))

    # Momento tombante gerado pelos empuxos
    momento_tomb_total = empuxo.empuxo_total_horizontal_kn * empuxo.ponto_aplicacao_empuxo_y_m

    return componentes, normal_total, momento_estab_total, momento_tomb_total


def verificar_estabilidade_geotecnica(
    geometria: GeometriaMuro,
    solo_fundacao: PropriedadesSolo,
    empuxo: ResultadoEmpuxo,
    normal_total: Fraction,
    momento_estab_total: Fraction,
    momento_tomb_total: Fraction,
) -> ResultadoEstabilidadeGeotecnica:
    """Realiza as verificações de tombamento, deslizamento e tensões de contato no terreno."""
    b = geometria.largura_base_b_m

    # 1. Fator de Segurança contra Tombamento
    if momento_tomb_total > Fraction(0, 1):
        fs_tomb = momento_estab_total / momento_tomb_total
    else:
        fs_tomb = Fraction(999, 1) # Sem empuxo tombante

    aprovado_tomb = fs_tomb >= FATOR_SEGURANCA_TOMBAMENTO_MINIMO

    # 2. Fator de Segurança contra Deslizamento
    # Força resistente de atrito: R = N * mu + (0.5 * Ep)
    mu = solo_fundacao.coef_atrito_base_mu
    r_atrito = normal_total * mu
    r_passivo_util = empuxo.empuxo_passivo_disponivel_kn / Fraction(2, 1) # minorado em 50% por segurança
    forca_resistente_total = r_atrito + r_passivo_util
    forca_solicitante_h = empuxo.empuxo_total_horizontal_kn

    if forca_solicitante_h > Fraction(0, 1):
        fs_desl = forca_resistente_total / forca_solicitante_h
    else:
        fs_desl = Fraction(999, 1)

    aprovado_desl = fs_desl >= FATOR_SEGURANCA_DESLIZAMENTO_MINIMO

    # 3. Posição da Resultante e Excentricidade
    momento_liquido = momento_estab_total - momento_tomb_total
    if normal_total > Fraction(0, 1):
        x_res = momento_liquido / normal_total
    else:
        x_res = Fraction(0, 1)

    centro_b = b / Fraction(2, 1)
    e = abs(centro_b - x_res)
    limite_terco_medio = b / Fraction(6, 1)
    dentro_terco_medio = e <= limite_terco_medio

    # 4. Tensões na Base de Fundação
    sigma_adm = solo_fundacao.tensao_admissivel_solo_fundacao_kpa
    if dentro_terco_medio:
        # Diagrama trapezoidal completo (sem tração)
        fator_e = (Fraction(6, 1) * e) / b
        sigma_max = (normal_total / b) * (Fraction(1, 1) + fator_e)
        sigma_min = (normal_total / b) * (Fraction(1, 1) - fator_e)
    else:
        # Descolamento parcial: diagrama triangular de base 3 * x_res
        if x_res > Fraction(0, 1):
            sigma_max = (Fraction(2, 1) * normal_total) / (Fraction(3, 1) * x_res)
        else:
            sigma_max = Fraction(99999, 1)
        sigma_min = Fraction(0, 1)

    aprovado_tensao = sigma_max <= sigma_adm and dentro_terco_medio

    return ResultadoEstabilidadeGeotecnica(
        forca_normal_total_base_kn=normal_total,
        forca_horizontal_solicitante_kn=forca_solicitante_h,
        forca_resistente_deslizamento_kn=forca_resistente_total,
        momento_estabilizante_total_knm=momento_estab_total,
        momento_tombante_total_knm=momento_tomb_total,
        fator_seguranca_tombamento=fs_tomb,
        fator_seguranca_deslizamento=fs_desl,
        posicao_resultante_base_x_m=x_res,
        excentricidade_base_e_m=e,
        limite_terco_medio_m=limite_terco_medio,
        dentro_do_terco_medio=dentro_terco_medio,
        tensao_maxima_base_kpa=sigma_max,
        tensao_minima_base_kpa=sigma_min,
        tensao_admissivel_kpa=sigma_adm,
        aprovado_tombamento=aprovado_tomb,
        aprovado_deslizamento=aprovado_desl,
        aprovado_capacidade_carga=aprovado_tensao,
    )


def dimensionar_estrutural_paramento(
    geometria: GeometriaMuro,
    solo: PropriedadesSolo,
    carregamentos: CarregamentosExternos,
) -> ResultadoEstruturalMuro:
    """Calcula as armaduras de flexão e verifica o cisalhamento na base do fuste (NBR 6118)."""
    h_sap = geometria.espessura_sapata_m
    if h_sap <= Fraction(0, 1):
        h_sap = max(Fraction(3, 10), geometria.altura_total_h_m / Fraction(10, 1))
    h_par = geometria.altura_total_h_m - h_sap

    ka, _ = obter_coeficientes_empuxo(solo)

    # Empuxo atuante ao longo do fuste livre do paramento
    # Solo: E1 = 0.5 * gamma * h_par^2 * Ka
    e_solo_par = Fraction(1, 2) * solo.peso_especifico_kn_m3 * (h_par * h_par) * ka
    m_solo_par = e_solo_par * (h_par / Fraction(3, 1))

    # Sobrecarga: E2 = q * Ka * h_par
    e_q_par = carregamentos.sobrecarga_uniforme_reaterro_kpa * ka * h_par
    m_q_par = e_q_par * (h_par / Fraction(2, 1))

    # Esforços característicos na base do paramento
    vk = e_solo_par + e_q_par
    mk = m_solo_par + m_q_par

    # Esforços de projeto (majorados em 1.4)
    vd = vk * GAMMA_ACOES_DESFAVORAVEIS
    md = mk * GAMMA_ACOES_DESFAVORAVEIS

    # Altura útil d (espessura na base - cobrimento de 4cm)
    b_base = geometria.espessura_base_paramento_m
    cobrimento = Fraction(4, 100) # 4 cm
    d = max(Fraction(15, 100), b_base - cobrimento)

    # Resistência de cálculo do aço CA-50: fyd = 500 MPa / 1.15 em kN/cm²:
    # 500 MPa = 50 kN/cm² -> fyd = 50 / 1.15 = 5000 / 115 kN/cm²
    fyd_kn_cm2 = (FYK_ACO_CA50_MPA / Fraction(10, 1)) / GAMMA_ACO
    d_cm = d * Fraction(100, 1)

    # Armadura de flexão As = Md / (0.9 * d * fyd) [Md em kN.cm = Md_knm * 100]
    md_kn_cm = md * Fraction(100, 1)
    braco_z_cm = Fraction(9, 10) * d_cm
    as_flexao_cm2 = md_kn_cm / (braco_z_cm * fyd_kn_cm2)

    # Armadura mínima NBR 6118 (0.15% da seção de concreto por metro linear)
    area_concreto_cm2_m = b_base * Fraction(100, 1) * Fraction(100, 1) # b=1m = 100cm
    as_min_cm2 = area_concreto_cm2_m * TAXA_ARMADURA_FLEXAO_MINIMA

    as_adotada_cm2 = max(as_flexao_cm2, as_min_cm2)

    # Verificação ao cisalhamento do concreto VRd1 (sem armadura transversal)
    # tau_Rd = 0.05 * fck^(2/3) aproximado ou fórmula simplificada NBR 6118:
    # VRd1 ~= 0.25 * fctd * b * d
    # Para fck = 25 MPa: fctd ~= 1.28 MPa = 1280 kPa
    fck = geometria.fck_concreto_mpa
    fctd_kpa = (Fraction(21, 100) * (fck * Fraction(1000, 1))) / GAMMA_CONCRETO
    vrd1_kn = Fraction(25, 100) * fctd_kpa * Fraction(1, 1) * d # b = 1.0 m

    aprovado_cisalha = vd <= vrd1_kn

    return ResultadoEstruturalMuro(
        momento_fletor_calculo_base_md_knm=md,
        forca_cortante_calculo_base_vd_kn=vd,
        area_armadura_flexao_cm2_m=as_flexao_cm2,
        area_armadura_minima_cm2_m=as_min_cm2,
        area_armadura_adotada_cm2_m=as_adotada_cm2,
        resistencia_cisalhamento_concreto_vrd1_kn=vrd1_kn,
        aprovado_cisalhamento=aprovado_cisalha,
        aprovado_estruturalmente=aprovado_cisalha,
    )


def dimensionar_projeto_muro_arrimo(dados: DadosProjetoMuroArrimo) -> ResultadoProjetoMuroArrimo:
    """Executa o dimensionamento completo e gera alertas normativos para o muro de contenção."""
    alertas: List[str] = []

    # 1. Validações preliminares
    geo = dados.geometria
    if geo.altura_total_h_m <= Fraction(0, 1):
        raise ValueError(f"Altura do muro deve ser positiva: {geo.altura_total_h_m}")
    if geo.largura_base_b_m <= Fraction(0, 1):
        raise ValueError(f"Largura da base deve ser positiva: {geo.largura_base_b_m}")

    # 2. Cálculo dos Empuxos de Terra
    empuxo = calcular_empuxos_terra(geo, dados.solo_reaterro, dados.carregamentos)

    # 3. Componentes de Peso e Momentos
    componentes, normal_tot, m_estab, m_tomb = calcular_componentes_estabilidade(
        tipo_muro=dados.tipo_muro,
        geometria=geo,
        solo=dados.solo_reaterro,
        carregamentos=dados.carregamentos,
        empuxo=empuxo,
    )

    # 4. Estabilidade Geotécnica Global
    estabilidade = verificar_estabilidade_geotecnica(
        geometria=geo,
        solo_fundacao=dados.solo_fundacao,
        empuxo=empuxo,
        normal_total=normal_tot,
        momento_estab_total=m_estab,
        momento_tomb_total=m_tomb,
    )

    # 5. Dimensionamento Estrutural (se aplicável para concreto armado)
    if dados.tipo_muro == TipoMuro.CONCRETO_ARMADO_BALANCO:
        res_estrutural = dimensionar_estrutural_paramento(geo, dados.solo_reaterro, dados.carregamentos)
    else:
        res_estrutural = None

    # 6. Avaliação Geral e Alertas Técnicos
    aprovado_geo = (
        estabilidade.aprovado_tombamento
        and estabilidade.aprovado_deslizamento
        and estabilidade.aprovado_capacidade_carga
    )
    aprovado_est = res_estrutural.aprovado_estruturalmente if res_estrutural is not None else True
    conformidade = aprovado_geo and aprovado_est

    if not estabilidade.aprovado_tombamento:
        alertas.append(
            f"Fator de segurança ao tombamento insuficiente: FS_tomb = {estabilidade.fator_seguranca_tombamento} "
            f"(Mínimo normativo exigido pela NBR 11682: {FATOR_SEGURANCA_TOMBAMENTO_MINIMO})."
        )

    if not estabilidade.aprovado_deslizamento:
        alertas.append(
            f"Fator de segurança ao deslizamento insuficiente: FS_desl = {estabilidade.fator_seguranca_deslizamento} "
            f"(Mínimo normativo exigido pela NBR 11682: {FATOR_SEGURANCA_DESLIZAMENTO_MINIMO}). "
            "Recomenda-se aumentar a base ou prever dente de cisalhamento."
        )

    if not estabilidade.dentro_do_terco_medio:
        alertas.append(
            f"Resultante fora do terço médio da base (excentricidade e = {estabilidade.excentricidade_base_e_m} m > B/6 = {estabilidade.limite_terco_medio_m} m). "
            "Risco iminente de descolamento e tração na interface solo-fundação."
        )

    if estabilidade.tensao_maxima_base_kpa > estabilidade.tensao_admissivel_kpa:
        alertas.append(
            f"Tensão máxima de contato na base ({estabilidade.tensao_maxima_base_kpa} kPa) excede a capacidade de carga admissível do solo ({estabilidade.tensao_admissivel_kpa} kPa)."
        )

    if res_estrutural is not None and not res_estrutural.aprovado_cisalhamento:
        alertas.append(
            f"Esforço cortante na base do fuste ({res_estrutural.forca_cortante_calculo_base_vd_kn} kN) excede a resistência de cálculo do concreto ({res_estrutural.resistencia_cisalhamento_concreto_vrd1_kn} kN). "
            "Necessário aumentar a espessura da base do paramento."
        )

    if dados.carregamentos.altura_nivel_freatico_m > Fraction(0, 1):
        alertas.append(
            f"Presença de nível freático a {dados.carregamentos.altura_nivel_freatico_m} m da base. "
            "Obrigatoriedade de barbacãs e dreno longitudinal profundo para alívio de empuxo hidrostático."
        )

    return ResultadoProjetoMuroArrimo(
        identificacao_projeto=dados.identificacao_projeto,
        tipo_muro=dados.tipo_muro,
        geometria=dados.geometria,
        solo_reaterro=dados.solo_reaterro,
        solo_fundacao=dados.solo_fundacao,
        carregamentos=dados.carregamentos,
        empuxo=empuxo,
        estabilidade=estabilidade,
        componentes_estabilidade=tuple(componentes),
        estrutural=res_estrutural,
        aprovado_globalmente=aprovado_geo,
        conformidade_geral=conformidade,
        alertas_tecnicos=tuple(alertas),
    )
