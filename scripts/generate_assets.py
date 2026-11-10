"""Gera painel visual esquemático SVG e captura screenshot PNG via headless Chrome."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from muros_arrimo_nbr11682.calculator import dimensionar_projeto_muro_arrimo
from muros_arrimo_nbr11682.codecs import decodificar_json_projeto
from muros_arrimo_nbr11682.svg_generator import gerar_painel_svg


def main() -> None:
    base_dir = Path(__file__).resolve().parent.parent
    exemplo_json = base_dir / "examples" / "muro_concreto_balanco_edificio.json"
    docs_dir = base_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    svg_out = docs_dir / "painel_exemplo.svg"
    png_out = docs_dir / "exemplo.png"

    print("Carregando exemplo de muro em balanço...")
    dados = decodificar_json_projeto(exemplo_json.read_text(encoding="utf-8"))
    res = dimensionar_projeto_muro_arrimo(dados)

    print("Gerando painel vetorial SVG (1440x900)...")
    svg_conteudo = gerar_painel_svg(res)
    svg_out.write_text(svg_conteudo, encoding="utf-8")
    print(f"SVG gerado em: {svg_out}")

    # Renderização via Google Chrome Headless
    chrome_bin = shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
    if not chrome_bin:
        print("Aviso: Navegador Chrome/Chromium não encontrado no ambiente.")
        return

    print(f"Renderizando screenshot de alta resolução via {chrome_bin}...")
    cmd = [
        chrome_bin,
        "--headless",
        "--disable-gpu",
        "--hide-scrollbars",
        "--window-size=1440,900",
        f"--screenshot={png_out}",
        str(svg_out),
    ]
    subprocess.run(cmd, check=True)
    if png_out.exists():
        tamanho_kb = png_out.stat().st_size / 1024
        print(f"Screenshot PNG gerada com sucesso: {png_out} ({tamanho_kb:.1f} KB)")


if __name__ == "__main__":
    main()
