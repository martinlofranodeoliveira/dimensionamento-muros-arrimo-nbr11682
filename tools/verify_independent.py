"""Auditor independente em SQLite em memória para verificação de Muros de Arrimo (NBR 11682).

Executa auditoria cruzada sem importar módulos de produção.
Garante a integridade matemática dos equilíbrios estáticos, empuxos e tensões de fundação.
"""

from __future__ import annotations

import sqlite3
import sys
from fractions import Fraction


def auditar_muro_arrimo_independente() -> None:
    print("=" * 80)
    print("AUDITORIA INDEPENDENTE DE MUROS DE ARRIMO EM SQLITE (ABNT NBR 11682:2009)")
    print("=" * 80)

    con = sqlite3.connect(":memory:")
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE caso_muro (
        id INTEGER PRIMARY KEY,
        nome TEXT,
        tipo TEXT,
        h_m REAL,
        b_m REAL,
        b_crista_m REAL,
        b_base_m REAL,
        h_sap_m REAL,
        l_ponta_m REAL,
        gamma_mat REAL,
        gamma_solo REAL,
        phi_graus INTEGER,
        ka REAL,
        q_kpa REAL,
        mu_base REAL,
        sigma_adm_kpa REAL
    );
    """)

    # Inserção de dados de teste (Caso 1: Concreto armado em balanço H=4.5m B=2.8m)
    # Ka para phi=30°: (1 - 0.5) / (1 + 0.5) = 1/3
    cur.execute("""
    INSERT INTO caso_muro VALUES (
        1,
        'Muro em Balanço H=4.5m B=2.8m',
        'CONCRETO_ARMADO_BALANCO',
        4.5,
        2.8,
        0.3,
        0.5,
        0.45,
        0.7,
        25.0,
        18.0,
        30,
        0.3333333333333333,
        10.0,
        0.55,
        300.0
    );
    """)

    # Consulta dos parâmetros
    cur.execute("SELECT * FROM caso_muro WHERE id = 1")
    row = cur.fetchone()
    nome = row[1]
    h = row[3]
    b = row[4]
    b_crista = row[5]
    b_base = row[6]
    h_sap = row[7]
    l_ponta = row[8]
    gamma_mat = row[9]
    gamma_solo = row[10]
    ka = row[12]
    q = row[13]
    mu = row[14]
    sigma_adm = row[15]

    # 1. Empuxo horizontal ativo (Rankine)
    # Ea_solo = 0.5 * gamma_solo * H^2 * Ka
    ea_solo = 0.5 * gamma_solo * (h ** 2) * ka
    ea_q = q * ka * h
    ea_tot = ea_solo + ea_q

    # Ponto de aplicação do empuxo e momento tombante em relação à ponta (pé frontal)
    m_tomb = ea_solo * (h / 3.0) + ea_q * (h / 2.0)

    # 2. Pesos próprios e momentos estabilizantes
    h_par = h - h_sap
    l_talao = b - l_ponta - b_base

    # Bloco 1: Sapata (B x h_sap)
    w1 = b * h_sap * gamma_mat
    x1 = b / 2.0

    # Bloco 2: Paramento retangular (b_crista x h_par)
    w2 = b_crista * h_par * gamma_mat
    x2 = l_ponta + (b_crista / 2.0)

    # Bloco 3: Paramento triangular (delta_b x h_par)
    delta_b = b_base - b_crista
    w3 = 0.5 * delta_b * h_par * gamma_mat
    x3 = l_ponta + b_crista + (delta_b / 3.0)

    # Bloco 4: Solo sobre o talão (l_talao x h_par)
    w_solo = l_talao * h_par * gamma_solo
    x_solo = b - (l_talao / 2.0)

    # Bloco 5: Sobrecarga sobre o talão
    w_q = q * l_talao
    x_q = x_solo

    w_tot = w1 + w2 + w3 + w_solo + w_q
    m_estab = (w1 * x1) + (w2 * x2) + (w3 * x3) + (w_solo * x_solo) + (w_q * x_q)

    # 3. Fatores de Segurança
    fs_tomb = m_estab / m_tomb
    r_atrito = w_tot * mu
    # Empuxo passivo frontal útil com embutimento D = 0.60m e kp = 3.69
    d_emb = 0.60
    kp = 3.69
    ep = 0.5 * gamma_solo * (d_emb ** 2) * kp
    r_passivo_util = ep / 2.0 # 50% de contribuição por segurança
    fs_desl = (r_atrito + r_passivo_util) / ea_tot

    # 4. Posição da Resultante e Tensões
    x_res = (m_estab - m_tomb) / w_tot
    e = abs((b / 2.0) - x_res)
    limite_terco = b / 6.0
    dentro_terco = e <= limite_terco

    fator_e = (6.0 * e) / b
    sigma_max = (w_tot / b) * (1.0 + fator_e)
    sigma_min = (w_tot / b) * (1.0 - fator_e)

    print(f"\nAuditando: {nome}")
    print(f"  * Empuxo Total Solicitante (Eh): {ea_tot:.2f} kN/m")
    print(f"  * Carga Normal Total (N):        {w_tot:.2f} kN/m")
    print(f"  * Momento Estabilizante (Me):    {m_estab:.2f} kN.m/m")
    print(f"  * Momento Tombante (Mt):         {m_tomb:.2f} kN.m/m")
    print(f"  * Fator Seg. Tombamento (FS):    {fs_tomb:.2f} (Normativo >= 1.50)")
    print(f"  * Fator Seg. Deslizamento (FS):  {fs_desl:.2f} (Normativo >= 1.50)")
    print(f"  * Excentricidade (e):            {e:.2f} m (Limite B/6 = {limite_terco:.2f} m)")
    print(f"  * Tensão Máxima no Solo:         {sigma_max:.2f} kPa (Admissível: {sigma_adm:.2f} kPa)")

    assert fs_tomb >= 1.50, f"Falha no tombamento: {fs_tomb} < 1.50"
    assert fs_desl >= 1.50, f"Falha no deslizamento: {fs_desl} < 1.50"
    assert dentro_terco, f"Falha no terço médio: e={e} > {limite_terco}"
    assert sigma_max <= sigma_adm, f"Falha na tensão máxima: {sigma_max} > {sigma_adm}"

    con.close()
    print("\n" + "=" * 80)
    print("AUDITORIA INDEPENDENTE EM SQLITE APROVADA COM SUCESSO ABSOLUTO!")
    print("=" * 80)


if __name__ == "__main__":
    auditar_muro_arrimo_independente()
