"""Gerador de diagramas vetoriais SVG (1440x900) para Muros de Arrimo NBR 11682 / NBR 6118.

Painel técnico profissional no padrão de engenharia visual da Lofrano Tecnologia.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

from muros_arrimo_nbr11682.exporters import _fmt
from muros_arrimo_nbr11682.models import ResultadoProjetoMuroArrimo


def gerar_painel_svg(
    arg1: Any,
    arg2: ResultadoProjetoMuroArrimo | None = None,
) -> str:
    """Gera painel vetorial SVG 1440x900 com corte esquemático, empuxos e tensões de fundação."""
    res: ResultadoProjetoMuroArrimo = (
        arg2 if arg2 is not None and isinstance(arg2, ResultadoProjetoMuroArrimo) else arg1
    )

    cor_fundo = "#0f172a"
    cor_card = "#1e293b"
    cor_borda = "#334155"
    cor_texto = "#f8fafc"
    cor_texto_mut = "#94a3b8"
    cor_ciano = "#06b6d4"
    cor_azul = "#3b82f6"
    cor_laranja = "#f97316"
    cor_verde = "#10b981"
    cor_vermelho = "#ef4444"
    cor_amarelo = "#eab308"
    cor_concreto = "#475569"
    cor_solo = "#78350f"

    status_cor = cor_verde if res.conformidade_geral else cor_vermelho
    status_texto = "CONFORME NBR 11682" if res.conformidade_geral else "PENDÊNCIAS TÉCNICAS"

    svg_linhas = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1440 900" width="1440" height="900" style="background:{cor_fundo}; font-family:-apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, Helvetica, Arial, sans-serif;">',
        '<defs>',
        '  <linearGradient id="gradHeader" x1="0" y1="0" x2="1" y2="0">',
        f'    <stop offset="0%" stop-color="{cor_azul}" stop-opacity="0.8"/>',
        f'    <stop offset="100%" stop-color="{cor_ciano}" stop-opacity="0.8"/>',
        '  </linearGradient>',
        '  <filter id="shadow" x="-5%" y="-5%" width="110%" height="110%">',
        '    <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000000" flood-opacity="0.4"/>',
        '  </filter>',
        '</defs>',
        f'<rect width="1440" height="900" fill="{cor_fundo}"/>',
        # Topo / Header
        f'<rect x="30" y="25" width="1380" height="75" rx="10" fill="url(#gradHeader)" filter="url(#shadow)"/>',
        '<text x="55" y="58" font-size="20" font-weight="bold" fill="#ffffff" letter-spacing="1">LOFRANO TECNOLOGIA | ENGENHARIA GEOTÉCNICA E ESTRUTURAL</text>',
        f'<text x="55" y="82" font-size="14" fill="#e0f2fe">DIMENSIONAMENTO DE MUROS DE ARRIMO E CONTENÇÃO — ABNT NBR 11682:2009 / NBR 6118:2023</text>',
        # Badge de Status Geral
        f'<rect x="1170" y="42" width="220" height="42" rx="21" fill="{status_cor}"/>',
        f'<text x="1280" y="68" font-size="13" font-weight="bold" fill="#ffffff" text-anchor="middle">{status_texto}</text>',
        # Identificação da Obra
        f'<rect x="30" y="115" width="1380" height="40" rx="6" fill="{cor_card}" stroke="{cor_borda}" stroke-width="1"/>',
        f'<text x="50" y="140" font-size="13" fill="{cor_texto_mut}">Obra / Projeto: <tspan fill="{cor_texto}" font-weight="bold">{res.identificacao_projeto}</tspan> | Tipologia: <tspan fill="{cor_ciano}" font-weight="bold">{res.tipo_muro.value}</tspan> | Solo: <tspan fill="{cor_amarelo}">{res.solo_reaterro.tipo_solo}</tspan></text>',
        # Painel Esquerdo: Desenho Esquemático do Muro e Diagramas de Empuxo (x=30..690)
        f'<rect x="30" y="170" width="670" height="700" rx="10" fill="{cor_card}" stroke="{cor_borda}" stroke-width="1"/>',
        f'<text x="55" y="202" font-size="16" font-weight="bold" fill="{cor_texto}">Perfil Esquemático e Ações Geotécnicas</text>',
        f'<line x1="55" y1="215" x2="675" y2="215" stroke="{cor_borda}" stroke-width="1"/>',
    ]

    # Geometria do desenho cotado (área do desenho: x: 120..580, y: 250..750)
    # Solo de reaterro à direita
    svg_linhas.append(f'<rect x="360" y="270" width="280" height="400" fill="{cor_solo}" fill-opacity="0.25"/>')
    svg_linhas.append(f'<text x="500" y="300" font-size="12" fill="{cor_laranja}" font-weight="bold" text-anchor="middle">Terrapleno de Reaterro (Solo)</text>')
    svg_linhas.append(f'<text x="500" y="320" font-size="11" fill="{cor_texto_mut}" text-anchor="middle">gamma = {_fmt(res.solo_reaterro.peso_especifico_kn_m3, 1)} kN/m³ | phi = {res.solo_reaterro.angulo_atrito_graus}°</text>')

    # Seção do Muro
    # Sapata: base x de 200 a 480 (largura 280), y de 620 a 670 (altura 50)
    # Paramento: x de 260 a 360, y de 270 a 620
    svg_linhas.append(f'<path d="M 200 670 L 480 670 L 480 620 L 360 620 L 310 270 L 260 270 L 260 620 L 200 620 Z" fill="{cor_concreto}" stroke="{cor_ciano}" stroke-width="2"/>')
    svg_linhas.append(f'<text x="310" y="445" font-size="13" font-weight="bold" fill="#ffffff" text-anchor="middle">FUSTE</text>')
    svg_linhas.append(f'<text x="340" y="650" font-size="12" font-weight="bold" fill="#ffffff" text-anchor="middle">SAPATA / BASE</text>')

    # Linha do terreno natural à frente e atrás
    svg_linhas.append(f'<line x1="80" y1="620" x2="200" y2="620" stroke="{cor_verde}" stroke-width="3" stroke-dasharray="4,2"/>')
    svg_linhas.append(f'<text x="140" y="610" font-size="10" fill="{cor_verde}" text-anchor="middle">Terreno Frontal</text>')
    svg_linhas.append(f'<line x1="310" y1="270" x2="650" y2="270" stroke="{cor_laranja}" stroke-width="3"/>')
    svg_linhas.append(f'<text x="580" y="260" font-size="10" fill="{cor_laranja}" text-anchor="middle">Linha do Terrapleno</text>')

    # Vetores de Empuxo
    svg_linhas.append(f'<polygon points="490,460 490,480 440,470" fill="{cor_vermelho}"/>')
    svg_linhas.append(f'<line x1="590" y1="470" x2="490" y2="470" stroke="{cor_vermelho}" stroke-width="4"/>')
    svg_linhas.append(f'<text x="540" y="455" font-size="12" font-weight="bold" fill="{cor_vermelho}" text-anchor="middle">Eh = {_fmt(res.empuxo.empuxo_total_horizontal_kn, 1)} kN/m</text>')

    # Diagrama de pressões na base de fundação (y=720..770)
    svg_linhas.append(f'<polygon points="200,720 480,720 480,760 200,780" fill="{cor_azul}" fill-opacity="0.3" stroke="{cor_azul}" stroke-width="2"/>')
    svg_linhas.append(f'<text x="200" y="805" font-size="11" font-weight="bold" fill="{cor_azul}">sigma_max = {_fmt(res.estabilidade.tensao_maxima_base_kpa, 1)} kPa</text>')
    svg_linhas.append(f'<text x="480" y="785" font-size="11" font-weight="bold" fill="{cor_azul}" text-anchor="end">sigma_min = {_fmt(res.estabilidade.tensao_minima_base_kpa, 1)} kPa</text>')
    svg_linhas.append(f'<text x="340" y="745" font-size="11" fill="#ffffff" text-anchor="middle">Pressões de Contato Solo-Base</text>')

    # Cotas principais
    svg_linhas.append(f'<text x="80" y="470" font-size="12" font-weight="bold" fill="{cor_texto_mut}">H = {_fmt(res.geometria.altura_total_h_m, 2)} m</text>')
    svg_linhas.append(f'<text x="340" y="700" font-size="12" font-weight="bold" fill="{cor_texto_mut}" text-anchor="middle">B = {_fmt(res.geometria.largura_base_b_m, 2)} m</text>')

    # Coluna Direita: Cards Técnicos (x=720..1410)
    # Card 1: Empuxos de Terra
    svg_linhas.append(f'<rect x="720" y="170" width="690" height="155" rx="10" fill="{cor_card}" stroke="{cor_borda}" stroke-width="1"/>')
    svg_linhas.append(f'<text x="745" y="200" font-size="15" font-weight="bold" fill="{cor_texto}">1. Empuxos de Terra (Teoria de Rankine)</text>')
    svg_linhas.append(f'<text x="745" y="230" font-size="13" fill="{cor_texto_mut}">Coeficiente Ativo (Ka): <tspan fill="{cor_texto}" font-weight="bold">{_fmt(res.empuxo.coeficiente_ka, 4)}</tspan> | Coeficiente Passivo (Kp): <tspan fill="{cor_texto}" font-weight="bold">{_fmt(res.empuxo.coeficiente_kp, 4)}</tspan></text>')
    svg_linhas.append(f'<text x="745" y="255" font-size="13" fill="{cor_texto_mut}">Empuxo Solo: <tspan fill="{cor_laranja}" font-weight="bold">{_fmt(res.empuxo.empuxo_solo_horizontal_kn, 2)} kN/m</tspan> | Empuxo Sobrecarga: <tspan fill="{cor_laranja}" font-weight="bold">{_fmt(res.empuxo.empuxo_sobrecarga_horizontal_kn, 2)} kN/m</tspan></text>')
    svg_linhas.append(f'<text x="745" y="280" font-size="13" fill="{cor_texto_mut}">Empuxo Hidrostático: <tspan fill="{cor_ciano}">{_fmt(res.empuxo.empuxo_hidrostatico_horizontal_kn, 2)} kN/m</tspan> | Passivo Útil: <tspan fill="{cor_verde}">{_fmt(res.empuxo.empuxo_passivo_disponivel_kn, 2)} kN/m</tspan></text>')
    svg_linhas.append(f'<text x="745" y="305" font-size="14" fill="{cor_vermelho}" font-weight="bold">Empuxo Total Solicitante (Eh): {_fmt(res.empuxo.empuxo_total_horizontal_kn, 2)} kN/m (y = {_fmt(res.empuxo.ponto_aplicacao_empuxo_y_m, 2)} m)</text>')

    # Card 2: Estabilidade Geotécnica Global (Tombamento e Deslizamento)
    svg_linhas.append(f'<rect x="720" y="340" width="690" height="175" rx="10" fill="{cor_card}" stroke="{cor_borda}" stroke-width="1"/>')
    svg_linhas.append(f'<text x="745" y="370" font-size="15" font-weight="bold" fill="{cor_texto}">2. Estabilidade Geotécnica Global (NBR 11682:2009)</text>')
    svg_linhas.append(f'<text x="745" y="400" font-size="13" fill="{cor_texto_mut}">Carga Normal Total (N): <tspan fill="{cor_texto}" font-weight="bold">{_fmt(res.estabilidade.forca_normal_total_base_kn, 2)} kN/m</tspan> | Força Resistente Atrito: <tspan fill="{cor_texto}" font-weight="bold">{_fmt(res.estabilidade.forca_resistente_deslizamento_kn, 2)} kN/m</tspan></text>')
    svg_linhas.append(f'<text x="745" y="425" font-size="13" fill="{cor_texto_mut}">Momento Estabilizante (Me): <tspan fill="{cor_verde}" font-weight="bold">{_fmt(res.estabilidade.momento_estabilizante_total_knm, 2)} kN.m/m</tspan></text>')
    svg_linhas.append(f'<text x="745" y="450" font-size="13" fill="{cor_texto_mut}">Momento Tombante (Mt): <tspan fill="{cor_vermelho}" font-weight="bold">{_fmt(res.estabilidade.momento_tombante_total_knm, 2)} kN.m/m</tspan></text>')

    cor_tomb = cor_verde if res.estabilidade.aprovado_tombamento else cor_vermelho
    cor_desl = cor_verde if res.estabilidade.aprovado_deslizamento else cor_vermelho
    svg_linhas.append(f'<text x="745" y="480" font-size="14" font-weight="bold" fill="{cor_tomb}">FS Tombamento: {_fmt(res.estabilidade.fator_seguranca_tombamento, 2)} (Mín. 1.50) — {"APROVADO" if res.estabilidade.aprovado_tombamento else "REPROVADO"}</text>')
    svg_linhas.append(f'<text x="745" y="502" font-size="14" font-weight="bold" fill="{cor_desl}">FS Deslizamento: {_fmt(res.estabilidade.fator_seguranca_deslizamento, 2)} (Mín. 1.50) — {"APROVADO" if res.estabilidade.aprovado_deslizamento else "REPROVADO"}</text>')

    # Card 3: Tensões de Contato e Excentricidade
    svg_linhas.append(f'<rect x="720" y="530" width="690" height="155" rx="10" fill="{cor_card}" stroke="{cor_borda}" stroke-width="1"/>')
    svg_linhas.append(f'<text x="745" y="560" font-size="15" font-weight="bold" fill="{cor_texto}">3. Tensões na Fundação e Regra do Terço Médio</text>')
    svg_linhas.append(f'<text x="745" y="590" font-size="13" fill="{cor_texto_mut}">Excentricidade (e): <tspan fill="{cor_texto}" font-weight="bold">{_fmt(res.estabilidade.excentricidade_base_e_m, 2)} m</tspan> | Limite B/6: <tspan fill="{cor_texto}" font-weight="bold">{_fmt(res.estabilidade.limite_terco_medio_m, 2)} m</tspan> ({"Dentro do Terço Médio" if res.estabilidade.dentro_do_terco_medio else "FORA DO TERÇO MÉDIO"})</text>')
    svg_linhas.append(f'<text x="745" y="615" font-size="13" fill="{cor_texto_mut}">Tensão Máxima (sigma_max): <tspan fill="{cor_ciano}" font-weight="bold">{_fmt(res.estabilidade.tensao_maxima_base_kpa, 2)} kPa</tspan> | Mínima: <tspan fill="{cor_ciano}">{_fmt(res.estabilidade.tensao_minima_base_kpa, 2)} kPa</tspan></text>')
    cor_solo_cap = cor_verde if res.estabilidade.aprovado_capacidade_carga else cor_vermelho
    svg_linhas.append(f'<text x="745" y="645" font-size="14" font-weight="bold" fill="{cor_solo_cap}">Capacidade Admissível do Terreno: {_fmt(res.estabilidade.tensao_admissivel_kpa, 2)} kPa — {"APROVADO" if res.estabilidade.aprovado_capacidade_carga else "CAPACIDADE INSUFICIENTE"}</text>')

    # Card 4: Alertas e Recomendações
    svg_linhas.append(f'<rect x="720" y="700" width="690" height="170" rx="10" fill="{cor_card}" stroke="{cor_borda}" stroke-width="1"/>')
    svg_linhas.append(f'<text x="745" y="730" font-size="15" font-weight="bold" fill="{cor_texto}">4. Recomendações Técnicas Normativas</text>')
    if res.alertas_tecnicos:
        y_alert = 755
        for i, alerta in enumerate(res.alertas_tecnicos[:3]):
            txt_curto = alerta[:85] + ("..." if len(alerta) > 85 else "")
            svg_linhas.append(f'<text x="745" y="{y_alert}" font-size="12" fill="{cor_laranja}">* {txt_curto}</text>')
            y_alert += 22
    else:
        svg_linhas.append(f'<text x="745" y="760" font-size="13" fill="{cor_verde}">Nenhum alerta impeditivo. Todas as verificações em plena conformidade.</text>')

    svg_linhas.append('</svg>')
    return "\n".join(svg_linhas)
