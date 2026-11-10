"""Exportadores técnicos: memorial descritivo, CSV sanitizado e pacote ZIP determinístico.

Conforme normas ABNT NBR 11682:2009 e ABNT NBR 6118:2023.
Padrão de engenharia LOFRANO TECNOLOGIA.
"""

from __future__ import annotations

import csv
import io
import os
import zipfile
from fractions import Fraction
from typing import Any, Optional

from muros_arrimo_nbr11682.codecs import exportar_resultado_json
from muros_arrimo_nbr11682.models import ResultadoProjetoMuroArrimo


def _fmt(val: Fraction, casas: int = 2) -> str:
    """Formata fração para string decimal com número fixo de casas sem ponto flutuante IEEE-754."""
    num = val.numerator
    den = val.denominator
    if den == 1:
        return f"{num}.0" if casas > 0 else str(num)
    inteiro = num // den
    resto = abs(num % den)
    fator = 10**casas
    frac_parte = (resto * fator + den // 2) // den
    return f"{inteiro}.{frac_parte:0{casas}d}"


def _sanitizar_campo_csv(val: str) -> str:
    """Sanitiza strings contra injeção de fórmulas de planilhas eletrônicas."""
    if val and val[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{val}"
    return val


def gerar_memorial_muro_texto(res: ResultadoProjetoMuroArrimo) -> str:
    """Gera memorial técnico descritivo completo da obra de contenção."""
    linhas: list[str] = []
    w = 84
    linhas.append("=" * w)
    linhas.append("           LOFRANO TECNOLOGIA - ENGENHARIA GEOTÉCNICA E ESTRUTURAL")
    linhas.append("       MEMORIAL DE CÁLCULO DE MUROS DE CONTENÇÃO E ARRIMO (NBR 11682)")
    linhas.append("=" * w)
    linhas.append(f"Projeto / Obra:           {res.identificacao_projeto}")
    linhas.append(f"Tipologia Estrutural:     {res.tipo_muro.value}")
    linhas.append(f"Altura Total (H):         {_fmt(res.geometria.altura_total_h_m, 2)} m")
    linhas.append(f"Largura da Base (B):      {_fmt(res.geometria.largura_base_b_m, 2)} m")
    linhas.append(f"Espessura no Topo:        {_fmt(res.geometria.espessura_crista_m, 2)} m")
    linhas.append(f"Espessura Base Paramento: {_fmt(res.geometria.espessura_base_paramento_m, 2)} m")
    linhas.append("-" * w)

    st_tomb = "APROVADO (FS >= 1.50)" if res.estabilidade.aprovado_tombamento else "REPROVADO (RISCO DE TOMBAMENTO)"
    st_desl = "APROVADO (FS >= 1.50)" if res.estabilidade.aprovado_deslizamento else "REPROVADO (RISCO DE DESLIZAMENTO)"
    st_tensao = "CONFORME (sigma <= sigma_adm)" if res.estabilidade.aprovado_capacidade_carga else "REPROVADO (SOBRECARGA DO SOLO)"
    st_geral = "CONFORME NBR 11682 / NBR 6118" if res.conformidade_geral else "PENDÊNCIAS TÉCNICAS / RISCO"

    linhas.append("1. EMPUXOS DE TERRA ATUANTES (MÉTODO DE RANKINE)")
    linhas.append(f"  * Coeficiente Ativo (Ka):           {_fmt(res.empuxo.coeficiente_ka, 4)}")
    linhas.append(f"  * Coeficiente Passivo (Kp):         {_fmt(res.empuxo.coeficiente_kp, 4)}")
    linhas.append(f"  * Empuxo Ativo do Solo:             {_fmt(res.empuxo.empuxo_solo_horizontal_kn, 2)} kN/m")
    linhas.append(f"  * Empuxo Ativo de Sobrecarga (q):   {_fmt(res.empuxo.empuxo_sobrecarga_horizontal_kn, 2)} kN/m")
    linhas.append(f"  * Empuxo Hidrostático (Água):       {_fmt(res.empuxo.empuxo_hidrostatico_horizontal_kn, 2)} kN/m")
    linhas.append(f"  * Empuxo Total Solicitante (Eh):    {_fmt(res.empuxo.empuxo_total_horizontal_kn, 2)} kN/m")
    linhas.append(f"  * Braço do Empuxo da Base (y):      {_fmt(res.empuxo.ponto_aplicacao_empuxo_y_m, 2)} m")
    linhas.append(f"  * Empuxo Passivo Frontal Útil:      {_fmt(res.empuxo.empuxo_passivo_disponivel_kn, 2)} kN/m")
    linhas.append("-" * w)

    linhas.append("2. ESTABILIDADE GEOTÉCNICA GLOBAL")
    linhas.append(f"  * Força Normal Total na Base (N):   {_fmt(res.estabilidade.forca_normal_total_base_kn, 2)} kN/m")
    linhas.append(f"  * Momento Estabilizante Total (Me): {_fmt(res.estabilidade.momento_estabilizante_total_knm, 2)} kN.m/m")
    linhas.append(f"  * Momento Tombante Total (Mt):      {_fmt(res.estabilidade.momento_tombante_total_knm, 2)} kN.m/m")
    linhas.append(f"  * Fator de Seg. ao Tombamento (FS): {_fmt(res.estabilidade.fator_seguranca_tombamento, 2)} -> {st_tomb}")
    linhas.append(f"  * Força Resistente ao Deslizamento: {_fmt(res.estabilidade.forca_resistente_deslizamento_kn, 2)} kN/m")
    linhas.append(f"  * Fator de Seg. Deslizamento (FS):  {_fmt(res.estabilidade.fator_seguranca_deslizamento, 2)} -> {st_desl}")
    linhas.append("-" * w)

    linhas.append("3. TENSÕES DE CONTATO E EXCENTRICIDADE NA FUNDAÇÃO")
    linhas.append(f"  * Posição da Resultante (x_res):    {_fmt(res.estabilidade.posicao_resultante_base_x_m, 2)} m do pé")
    linhas.append(f"  * Excentricidade da Carga (e):      {_fmt(res.estabilidade.excentricidade_base_e_m, 2)} m")
    linhas.append(f"  * Limite do Terço Médio (B/6):      {_fmt(res.estabilidade.limite_terco_medio_m, 2)} m")
    linhas.append(f"  * Resultante no Terço Médio?:       {'SIM (SEM TRAÇÃO)' if res.estabilidade.dentro_do_terco_medio else 'NÃO (DESCOLAMENTO PARCIAL)'}")
    linhas.append(f"  * Tensão Máxima no Solo (sigma_max):{_fmt(res.estabilidade.tensao_maxima_base_kpa, 2)} kPa")
    linhas.append(f"  * Tensão Mínima no Solo (sigma_min):{_fmt(res.estabilidade.tensao_minima_base_kpa, 2)} kPa")
    linhas.append(f"  * Capacidade Admissível do Solo:    {_fmt(res.estabilidade.tensao_admissivel_kpa, 2)} kPa -> {st_tensao}")
    linhas.append("-" * w)

    if res.estrutural is not None:
        st_estrut = "CONFORME" if res.estrutural.aprovado_estruturalmente else "REPROVADO"
        linhas.append("4. VERIFICAÇÃO ESTRUTURAL DO PARAMENTO (NBR 6118:2023)")
        linhas.append(f"  * Momento Fletor de Cálculo (Md):   {_fmt(res.estrutural.momento_fletor_calculo_base_md_knm, 2)} kN.m/m")
        linhas.append(f"  * Força Cortante de Cálculo (Vd):   {_fmt(res.estrutural.forca_cortante_calculo_base_vd_kn, 2)} kN/m")
        linhas.append(f"  * Área de Aço de Flexão (As):       {_fmt(res.estrutural.area_armadura_flexao_cm2_m, 2)} cm²/m")
        linhas.append(f"  * Área de Aço Mínima (As,min):      {_fmt(res.estrutural.area_armadura_minima_cm2_m, 2)} cm²/m")
        linhas.append(f"  * Área de Aço Efetiva Adotada:      {_fmt(res.estrutural.area_armadura_adotada_cm2_m, 2)} cm²/m")
        linhas.append(f"  * Resistência ao Cisalhamento (VRd):{_fmt(res.estrutural.resistencia_cisalhamento_concreto_vrd1_kn, 2)} kN/m")
        linhas.append(f"  * Status da Verificação Estrutural: {st_estrut}")
        linhas.append("-" * w)

    linhas.append(f"STATUS GLOBAL DE CONFORMIDADE:        {st_geral}")
    linhas.append("-" * w)

    if res.alertas_tecnicos:
        linhas.append("5. RECOMENDAÇÕES E ALERTAS TÉCNICOS NORMATIVOS")
        for alerta in res.alertas_tecnicos:
            linhas.append(f"  [ALERTA] {alerta}")
    else:
        linhas.append("5. RECOMENDAÇÕES E ALERTAS TÉCNICOS NORMATIVOS")
        linhas.append("  Nenhum alerta impeditivo identificado. Projeto geotécnico em conformidade plena.")

    linhas.append("=" * w)
    linhas.append("Emitido via Lofrano Tecnologia - Conforme ABNT NBR 11682:2009 e ABNT NBR 6118:2023")
    linhas.append("=" * w)

    return "\n".join(linhas)


def gerar_csv_resumo_muro(res: ResultadoProjetoMuroArrimo) -> str:
    """Gera resumo técnico tabular em CSV sanitizado contra injeção de fórmulas."""
    saida = io.StringIO()
    writer = csv.writer(saida, delimiter=";", lineterminator="\n")

    writer.writerow([
        _sanitizar_campo_csv("modulo"),
        _sanitizar_campo_csv("parametro"),
        _sanitizar_campo_csv("valor"),
        _sanitizar_campo_csv("unidade"),
        _sanitizar_campo_csv("observacao"),
    ])

    linhas = [
        ("DADOS_PROJETO", "obra", res.identificacao_projeto, "texto", "Identificação"),
        ("DADOS_PROJETO", "tipologia", res.tipo_muro.value, "enum", "Tipo de contenção"),
        ("GEOMETRIA", "altura_total", _fmt(res.geometria.altura_total_h_m, 2), "m", "Altura total H"),
        ("GEOMETRIA", "largura_base", _fmt(res.geometria.largura_base_b_m, 2), "m", "Largura da sapata/base B"),
        ("GEOMETRIA", "espessura_crista", _fmt(res.geometria.espessura_crista_m, 2), "m", "Espessura topo"),
        ("GEOMETRIA", "espessura_base", _fmt(res.geometria.espessura_base_paramento_m, 2), "m", "Espessura paramento base"),
        ("EMPUXOS", "coeficiente_ka", _fmt(res.empuxo.coeficiente_ka, 4), "-", "Rankine ativo"),
        ("EMPUXOS", "empuxo_total_h", _fmt(res.empuxo.empuxo_total_horizontal_kn, 2), "kN/m", "Esforço horizontal"),
        ("ESTABILIDADE", "forca_normal_total", _fmt(res.estabilidade.forca_normal_total_base_kn, 2), "kN/m", "Carga vertical"),
        ("ESTABILIDADE", "fator_seguranca_tombamento", _fmt(res.estabilidade.fator_seguranca_tombamento, 2), "-", "Mínimo 1.50"),
        ("ESTABILIDADE", "fator_seguranca_deslizamento", _fmt(res.estabilidade.fator_seguranca_deslizamento, 2), "-", "Mínimo 1.50"),
        ("ESTABILIDADE", "excentricidade", _fmt(res.estabilidade.excentricidade_base_e_m, 2), "m", f"Limite B/6 = {_fmt(res.estabilidade.limite_terco_medio_m, 2)}"),
        ("ESTABILIDADE", "tensao_maxima_solo", _fmt(res.estabilidade.tensao_maxima_base_kpa, 2), "kPa", f"Admissível: {_fmt(res.estabilidade.tensao_admissivel_kpa, 2)}"),
        ("CONFORMIDADE", "status_tombamento", "APROVADO" if res.estabilidade.aprovado_tombamento else "REPROVADO", "status", "Segurança ao tombamento"),
        ("CONFORMIDADE", "status_deslizamento", "APROVADO" if res.estabilidade.aprovado_deslizamento else "REPROVADO", "status", "Segurança ao deslizamento"),
        ("CONFORMIDADE", "status_capacidade_carga", "APROVADO" if res.estabilidade.aprovado_capacidade_carga else "REPROVADO", "status", "Tensão de contato"),
        ("CONFORMIDADE", "status_geral", "CONFORME" if res.conformidade_geral else "PENDENCIAS", "status", "Conformidade global"),
    ]

    if res.estrutural is not None:
        linhas.extend([
            ("ESTRUTURAL", "momento_fletor_calculo", _fmt(res.estrutural.momento_fletor_calculo_base_md_knm, 2), "kNm/m", "Md na base"),
            ("ESTRUTURAL", "armadura_adotada", _fmt(res.estrutural.area_armadura_adotada_cm2_m, 2), "cm2/m", "Armadura de flexão"),
            ("ESTRUTURAL", "status_estrutural", "APROVADO" if res.estrutural.aprovado_estruturalmente else "REPROVADO", "status", "Verificação fuste"),
        ])

    for mod, param, val, un, obs in linhas:
        writer.writerow([
            _sanitizar_campo_csv(mod),
            _sanitizar_campo_csv(param),
            _sanitizar_campo_csv(val),
            _sanitizar_campo_csv(un),
            _sanitizar_campo_csv(obs),
        ])

    return saida.getvalue()


def gerar_pacote_zip_muro(
    res: ResultadoProjetoMuroArrimo,
    caminho_zip: str,
    svg_conteudo: Optional[str] = None,
) -> None:
    """Gera pacote determinístico ZIP com O_EXCL, evitando sobrescrita acidental."""
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(caminho_zip, flags, 0o644)
    fixed_time = (2026, 1, 1, 0, 0, 0)

    try:
        with open(fd, "wb", closefd=True) as f_out:
            with zipfile.ZipFile(f_out, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                # 1. Memorial descritivo em texto
                txt = gerar_memorial_muro_texto(res).encode("utf-8")
                zi_txt = zipfile.ZipInfo(filename="memorial_muro_arrimo.txt", date_time=fixed_time)
                zf.writestr(zi_txt, txt)

                # 2. Dados em JSON canônico
                js = exportar_resultado_json(res).encode("utf-8")
                zi_js = zipfile.ZipInfo(filename="dados_muro_arrimo.json", date_time=fixed_time)
                zf.writestr(zi_js, js)

                # 3. Resumo tabular em CSV sanitizado
                csv_data = gerar_csv_resumo_muro(res).encode("utf-8")
                zi_csv = zipfile.ZipInfo(filename="resumo_muro_arrimo.csv", date_time=fixed_time)
                zf.writestr(zi_csv, csv_data)

                # 4. Diagrama vetorial SVG se fornecido
                if svg_conteudo is not None:
                    zi_svg = zipfile.ZipInfo(filename="painel_muro_arrimo.svg", date_time=fixed_time)
                    zf.writestr(zi_svg, svg_conteudo.encode("utf-8"))
    except Exception:
        if os.path.exists(caminho_zip):
            try:
                os.remove(caminho_zip)
            except OSError:
                pass
        raise


def exportar_memorial_descritivo(arg1: Any, arg2: Optional[ResultadoProjetoMuroArrimo] = None) -> str:
    """Exporta memorial descritivo aceitando (resultado) ou (dados, resultado)."""
    if isinstance(arg1, ResultadoProjetoMuroArrimo):
        return gerar_memorial_muro_texto(arg1)
    if arg2 is not None and isinstance(arg2, ResultadoProjetoMuroArrimo):
        return gerar_memorial_muro_texto(arg2)
    raise ValueError("ResultadoProjetoMuroArrimo não fornecido para memorial descritivo.")


def exportar_csv_resumo(arg1: Any, arg2: Optional[ResultadoProjetoMuroArrimo] = None) -> str:
    """Exporta resumo em CSV aceitando (resultado) ou (dados, resultado)."""
    if isinstance(arg1, ResultadoProjetoMuroArrimo):
        return gerar_csv_resumo_muro(arg1)
    if arg2 is not None and isinstance(arg2, ResultadoProjetoMuroArrimo):
        return gerar_csv_resumo_muro(arg2)
    raise ValueError("ResultadoProjetoMuroArrimo não fornecido para CSV.")


def gerar_pacote_completo_zip(arg1: Any, arg2: Any, arg3: Optional[str] = None) -> None:
    """Gera pacote ZIP aceitando (res, caminho) ou (dados, res, caminho)."""
    if isinstance(arg1, ResultadoProjetoMuroArrimo):
        gerar_pacote_zip_muro(arg1, str(arg2))
    elif isinstance(arg2, ResultadoProjetoMuroArrimo) and arg3 is not None:
        gerar_pacote_zip_muro(arg2, str(arg3))
    else:
        raise ValueError("Parâmetros inválidos para geração de pacote ZIP.")
