"""Verifica a integridade das distribuições geradas (sdist e wheel)."""

from __future__ import annotations

import sys
import tarfile
import zipfile
from pathlib import Path


def main() -> None:
    dist_dir = Path(__file__).resolve().parent.parent / "dist"
    if not dist_dir.exists():
        print("Erro: Diretório dist/ não encontrado.")
        sys.exit(1)

    sdists = list(dist_dir.glob("*.tar.gz"))
    wheels = list(dist_dir.glob("*.whl"))

    if not sdists:
        print("Erro: Nenhum sdist .tar.gz encontrado em dist/")
        sys.exit(1)
    if not wheels:
        print("Erro: Nenhum wheel .whl encontrado em dist/")
        sys.exit(1)

    sdist = sdists[0]
    wheel = wheels[0]

    print(f"Verificando sdist: {sdist.name}")
    with tarfile.open(sdist, "r:gz") as tar:
        nomes = tar.getnames()
        arquivos_obrigatorios = [
            "pyproject.toml",
            "LICENSE",
            "README.md",
            "src/muros_arrimo_nbr11682/__init__.py",
            "src/muros_arrimo_nbr11682/calculator.py",
            "src/muros_arrimo_nbr11682/models.py",
            "src/muros_arrimo_nbr11682/constants.py",
            "src/muros_arrimo_nbr11682/codecs.py",
            "src/muros_arrimo_nbr11682/exporters.py",
            "src/muros_arrimo_nbr11682/svg_generator.py",
            "src/muros_arrimo_nbr11682/cli.py",
            "src/muros_arrimo_nbr11682/py.typed",
        ]
        for req in arquivos_obrigatorios:
            if not any(req in n for n in nomes):
                print(f"Erro: Arquivo obrigatório ausente no sdist: {req}")
                sys.exit(1)

    print(f"Verificando wheel: {wheel.name}")
    with zipfile.ZipFile(wheel, "r") as zf:
        nomes_whl = zf.namelist()
        arquivos_whl = [
            "muros_arrimo_nbr11682/__init__.py",
            "muros_arrimo_nbr11682/calculator.py",
            "muros_arrimo_nbr11682/models.py",
            "muros_arrimo_nbr11682/constants.py",
            "muros_arrimo_nbr11682/codecs.py",
            "muros_arrimo_nbr11682/exporters.py",
            "muros_arrimo_nbr11682/svg_generator.py",
            "muros_arrimo_nbr11682/cli.py",
            "muros_arrimo_nbr11682/py.typed",
        ]
        for req in arquivos_whl:
            if req not in nomes_whl:
                print(f"Erro: Arquivo obrigatório ausente no wheel: {req}")
                sys.exit(1)

    print("Distribuição verificada com sucesso: 100% dos arquivos obrigatórios presentes.")


if __name__ == "__main__":
    main()
