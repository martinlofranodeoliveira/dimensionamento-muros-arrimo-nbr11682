"""Codec JSON canônico RFC 8259 para dimensionamento de muros de arrimo NBR 11682.

Garante ausência estrita de ponto flutuante IEEE-754, rejeição de BOM,
verificação de chaves duplicadas e limitação de profundidade estrutural.
"""

from __future__ import annotations

import json
from enum import Enum
from fractions import Fraction
from typing import Any

from muros_arrimo_nbr11682.models import (
    CarregamentosExternos,
    DadosProjetoMuroArrimo,
    GeometriaMuro,
    PropriedadesSolo,
    ResultadoProjetoMuroArrimo,
    TipoMuro,
)


def _rejeitar_float(valor: str) -> None:
    raise ValueError(
        f"Ponto flutuante IEEE-754 ({valor}) não é permitido. "
        "Utilize inteiros ou strings numéricas fracionárias/decimais exatas."
    )


def _rejeitar_chaves_duplicadas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in resultado:
            raise ValueError(f"Chave duplicada encontrada no JSON: '{chave}'")
        resultado[chave] = valor
    return resultado


def _verificar_profundidade(obj: Any, profundidade: int = 1, limite: int = 32) -> None:
    if profundidade > limite:
        raise ValueError(
            f"Profundidade da estrutura JSON ({profundidade}) excede o limite máximo permitido de {limite}."
        )
    if isinstance(obj, dict):
        for v in obj.values():
            _verificar_profundidade(v, profundidade + 1, limite)
    elif isinstance(obj, list):
        for elem in obj:
            _verificar_profundidade(elem, profundidade + 1, limite)


def _para_fracao(val: Any) -> Fraction:
    if isinstance(val, (int, str)):
        return Fraction(val)
    if isinstance(val, Fraction):
        return val
    raise ValueError(f"Tipo inválido para conversão fracionária: {type(val).__name__} ({val})")


def _serializar_valor(val: Any) -> Any:
    if isinstance(val, Fraction):
        if val.denominator == 1:
            return val.numerator
        return f"{val.numerator}/{val.denominator}"
    if isinstance(val, Enum):
        return val.value
    if isinstance(val, tuple):
        return [_serializar_valor(x) for x in val]
    if isinstance(val, list):
        return [_serializar_valor(x) for x in val]
    if isinstance(val, dict):
        return {k: _serializar_valor(v) for k, v in val.items()}
    return val


def carregar_projeto_muro_json(conteudo: str) -> DadosProjetoMuroArrimo:
    """Carrega e valida o projeto de contenção a partir de JSON canônico RFC 8259."""
    if conteudo.startswith(("\ufeff", "\xef\xbb\xbf")):
        raise ValueError("Byte Order Mark (BOM) detectado. O arquivo deve ser codificado em UTF-8 puro.")

    try:
        dados = json.loads(
            conteudo,
            object_pairs_hook=_rejeitar_chaves_duplicadas,
            parse_float=_rejeitar_float,
        )
    except json.JSONDecodeError as err:
        raise ValueError(f"Erro de decodificação JSON: {err}") from err

    _verificar_profundidade(dados)

    if not isinstance(dados, dict):
        raise ValueError("O JSON raiz do projeto deve ser um objeto dicionário.")

    identificacao = str(dados.get("identificacao_projeto") or dados.get("nome_projeto") or "Muro de Contenção")

    # Tipo de Muro
    tipo_str = str(dados.get("tipo_muro") or "CONCRETO_ARMADO_BALANCO").upper().strip()
    try:
        tipo_muro = TipoMuro(tipo_str)
    except ValueError:
        tipo_muro = TipoMuro.CONCRETO_ARMADO_BALANCO

    # Geometria
    geo_raw = dados.get("geometria")
    if not isinstance(geo_raw, dict):
        raise ValueError("O campo 'geometria' deve ser um objeto JSON.")

    h_total = _para_fracao(geo_raw.get("altura_total_h_m") or geo_raw.get("altura_m") or 4)
    b_base = _para_fracao(geo_raw.get("largura_base_b_m") or geo_raw.get("base_m") or Fraction(25, 10))
    esp_crista = _para_fracao(geo_raw.get("espessura_crista_m") or Fraction(3, 10))
    esp_base_par = _para_fracao(geo_raw.get("espessura_base_paramento_m") or Fraction(5, 10))
    esp_sap = _para_fracao(geo_raw.get("espessura_sapata_m") or Fraction(4, 10))
    comp_ponta = _para_fracao(geo_raw.get("comprimento_ponta_m") or Fraction(6, 10))
    prof_emb = _para_fracao(geo_raw.get("profundidade_embutimento_d_m") or Fraction(5, 10))
    alt_dente = _para_fracao(geo_raw.get("altura_dente_cisalhamento_m") or 0)
    larg_dente = _para_fracao(geo_raw.get("largura_dente_cisalhamento_m") or 0)
    fck = _para_fracao(geo_raw.get("fck_concreto_mpa") or 25)

    geometria = GeometriaMuro(
        altura_total_h_m=h_total,
        largura_base_b_m=b_base,
        espessura_crista_m=esp_crista,
        espessura_base_paramento_m=esp_base_par,
        espessura_sapata_m=esp_sap,
        comprimento_ponta_m=comp_ponta,
        profundidade_embutimento_d_m=prof_emb,
        altura_dente_cisalhamento_m=alt_dente,
        largura_dente_cisalhamento_m=larg_dente,
        fck_concreto_mpa=fck,
    )

    # Solo de Reaterro
    solo_r_raw = dados.get("solo_reaterro") or {}
    if not isinstance(solo_r_raw, dict):
        raise ValueError("O campo 'solo_reaterro' deve ser um objeto JSON.")

    tipo_sr = str(solo_r_raw.get("tipo_solo", "AREIA_MEDIA")).upper().strip()
    peso_sr = _para_fracao(solo_r_raw.get("peso_especifico_kn_m3") or 18)
    phi_sr = int(solo_r_raw.get("angulo_atrito_graus") or 30)
    coesao_sr = _para_fracao(solo_r_raw.get("coesao_kpa") or 0)

    solo_reaterro = PropriedadesSolo(
        tipo_solo=tipo_sr,
        peso_especifico_kn_m3=peso_sr,
        angulo_atrito_graus=phi_sr,
        coesao_kpa=coesao_sr,
    )

    # Solo de Fundação
    solo_f_raw = dados.get("solo_fundacao") or {}
    if not isinstance(solo_f_raw, dict):
        raise ValueError("O campo 'solo_fundacao' deve ser um objeto JSON.")

    tipo_sf = str(solo_f_raw.get("tipo_solo", "AREIA_COMPACTA")).upper().strip()
    peso_sf = _para_fracao(solo_f_raw.get("peso_especifico_kn_m3") or 19)
    phi_sf = int(solo_f_raw.get("angulo_atrito_graus") or 32)
    coesao_sf = _para_fracao(solo_f_raw.get("coesao_kpa") or 0)
    mu_base = _para_fracao(solo_f_raw.get("coef_atrito_base_mu") or Fraction(5, 10))
    tensao_adm = _para_fracao(solo_f_raw.get("tensao_admissivel_solo_fundacao_kpa") or 250)

    solo_fundacao = PropriedadesSolo(
        tipo_solo=tipo_sf,
        peso_especifico_kn_m3=peso_sf,
        angulo_atrito_graus=phi_sf,
        coesao_kpa=coesao_sf,
        coef_atrito_base_mu=mu_base,
        tensao_admissivel_solo_fundacao_kpa=tensao_adm,
    )

    # Carregamentos Externos
    carreg_raw = dados.get("carregamentos") or {}
    if not isinstance(carreg_raw, dict):
        raise ValueError("O campo 'carregamentos' deve ser um objeto JSON.")

    q_sobrecarga = _para_fracao(carreg_raw.get("sobrecarga_uniforme_reaterro_kpa") or 0)
    h_agua = _para_fracao(carreg_raw.get("altura_nivel_freatico_m") or 0)
    beta = int(carreg_raw.get("inclinacao_terrapleno_graus") or 0)

    carregamentos = CarregamentosExternos(
        sobrecarga_uniforme_reaterro_kpa=q_sobrecarga,
        altura_nivel_freatico_m=h_agua,
        inclinacao_terrapleno_graus=beta,
    )

    responsavel = str(dados.get("responsavel_tecnico", "Engenharia Geotécnica"))

    return DadosProjetoMuroArrimo(
        identificacao_projeto=identificacao,
        tipo_muro=tipo_muro,
        geometria=geometria,
        solo_reaterro=solo_reaterro,
        solo_fundacao=solo_fundacao,
        carregamentos=carregamentos,
        responsavel_tecnico=responsavel,
    )


def exportar_resultado_json(res: ResultadoProjetoMuroArrimo) -> str:
    """Serializa o resultado em JSON canônico RFC 8259 determinístico."""
    dados: dict[str, Any] = {
        "normas_referencia": [
            "ABNT NBR 11682:2009",
            "ABNT NBR 6118:2023",
        ],
        "identificacao_projeto": res.identificacao_projeto,
        "tipo_muro": res.tipo_muro.value,
        "geometria": {
            "altura_total_h_m": _serializar_valor(res.geometria.altura_total_h_m),
            "largura_base_b_m": _serializar_valor(res.geometria.largura_base_b_m),
            "espessura_crista_m": _serializar_valor(res.geometria.espessura_crista_m),
            "espessura_base_paramento_m": _serializar_valor(res.geometria.espessura_base_paramento_m),
            "espessura_sapata_m": _serializar_valor(res.geometria.espessura_sapata_m),
            "comprimento_ponta_m": _serializar_valor(res.geometria.comprimento_ponta_m),
            "profundidade_embutimento_d_m": _serializar_valor(res.geometria.profundidade_embutimento_d_m),
            "fck_concreto_mpa": _serializar_valor(res.geometria.fck_concreto_mpa),
        },
        "empuxo_terra": {
            "metodo": res.empuxo.metodo,
            "coeficiente_ka": _serializar_valor(res.empuxo.coeficiente_ka),
            "coeficiente_kp": _serializar_valor(res.empuxo.coeficiente_kp),
            "empuxo_solo_horizontal_kn": _serializar_valor(res.empuxo.empuxo_solo_horizontal_kn),
            "empuxo_sobrecarga_horizontal_kn": _serializar_valor(res.empuxo.empuxo_sobrecarga_horizontal_kn),
            "empuxo_hidrostatico_horizontal_kn": _serializar_valor(res.empuxo.empuxo_hidrostatico_horizontal_kn),
            "empuxo_total_horizontal_kn": _serializar_valor(res.empuxo.empuxo_total_horizontal_kn),
            "ponto_aplicacao_empuxo_y_m": _serializar_valor(res.empuxo.ponto_aplicacao_empuxo_y_m),
            "empuxo_passivo_disponivel_kn": _serializar_valor(res.empuxo.empuxo_passivo_disponivel_kn),
        },
        "estabilidade_geotecnica": {
            "forca_normal_total_base_kn": _serializar_valor(res.estabilidade.forca_normal_total_base_kn),
            "forca_horizontal_solicitante_kn": _serializar_valor(res.estabilidade.forca_horizontal_solicitante_kn),
            "forca_resistente_deslizamento_kn": _serializar_valor(res.estabilidade.forca_resistente_deslizamento_kn),
            "momento_estabilizante_total_knm": _serializar_valor(res.estabilidade.momento_estabilizante_total_knm),
            "momento_tombante_total_knm": _serializar_valor(res.estabilidade.momento_tombante_total_knm),
            "fator_seguranca_tombamento": _serializar_valor(res.estabilidade.fator_seguranca_tombamento),
            "fator_seguranca_deslizamento": _serializar_valor(res.estabilidade.fator_seguranca_deslizamento),
            "posicao_resultante_base_x_m": _serializar_valor(res.estabilidade.posicao_resultante_base_x_m),
            "excentricidade_base_e_m": _serializar_valor(res.estabilidade.excentricidade_base_e_m),
            "limite_terco_medio_m": _serializar_valor(res.estabilidade.limite_terco_medio_m),
            "dentro_do_terco_medio": res.estabilidade.dentro_do_terco_medio,
            "tensao_maxima_base_kpa": _serializar_valor(res.estabilidade.tensao_maxima_base_kpa),
            "tensao_minima_base_kpa": _serializar_valor(res.estabilidade.tensao_minima_base_kpa),
            "tensao_admissivel_kpa": _serializar_valor(res.estabilidade.tensao_admissivel_kpa),
            "aprovado_tombamento": res.estabilidade.aprovado_tombamento,
            "aprovado_deslizamento": res.estabilidade.aprovado_deslizamento,
            "aprovado_capacidade_carga": res.estabilidade.aprovado_capacidade_carga,
        },
        "aprovado_globalmente": res.aprovado_globalmente,
        "conformidade_geral": res.conformidade_geral,
        "alertas_tecnicos": list(res.alertas_tecnicos),
    }

    if res.estrutural is not None:
        dados["verificacao_estrutural_paramento"] = {
            "momento_fletor_calculo_base_md_knm": _serializar_valor(res.estrutural.momento_fletor_calculo_base_md_knm),
            "forca_cortante_calculo_base_vd_kn": _serializar_valor(res.estrutural.forca_cortante_calculo_base_vd_kn),
            "area_armadura_flexao_cm2_m": _serializar_valor(res.estrutural.area_armadura_flexao_cm2_m),
            "area_armadura_minima_cm2_m": _serializar_valor(res.estrutural.area_armadura_minima_cm2_m),
            "area_armadura_adotada_cm2_m": _serializar_valor(res.estrutural.area_armadura_adotada_cm2_m),
            "resistencia_cisalhamento_concreto_vrd1_kn": _serializar_valor(
                res.estrutural.resistencia_cisalhamento_concreto_vrd1_kn
            ),
            "aprovado_cisalhamento": res.estrutural.aprovado_cisalhamento,
            "aprovado_estruturalmente": res.estrutural.aprovado_estruturalmente,
        }

    return json.dumps(dados, ensure_ascii=False, indent=2, sort_keys=True)


decodificar_json_projeto = carregar_projeto_muro_json


def codificar_json_projeto(
    arg1: Any,
    arg2: ResultadoProjetoMuroArrimo | None = None,
) -> str:
    """Codifica resultado em JSON RFC 8259, aceitando (resultado) ou (dados, resultado)."""
    if isinstance(arg1, ResultadoProjetoMuroArrimo):
        return exportar_resultado_json(arg1)
    if arg2 is not None and isinstance(arg2, ResultadoProjetoMuroArrimo):
        return exportar_resultado_json(arg2)
    raise ValueError("ResultadoProjetoMuroArrimo não fornecido para codificação JSON.")
