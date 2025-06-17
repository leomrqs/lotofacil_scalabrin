#!/usr/bin/env python3
# -*- coding: utf-8 -*
# AUTOR: Leonardo dos Santos Marques
"""
package_zip.py — consolida todo o material do projeto Lotofácil
em **lotofacil_submission.zip** (raiz).

Conteúdo incluído
-----------------
• Scripts‑chave *.py  (gerador, benchmark, programas 2‑5, verificador, custo, este pacote)  
• Documentos de topo – README, REPORT, MakeFile  
• Pastas de resultados: resultados/, prog2_saida/, …, prog7_saida/  
• PDFs que existirem em docs/

Regra de ouro: se o ZIP já existir, é **apagado** antes de ser recriado –
evita submissões corrompidas.

Uso
----
    python package_zip.py
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import datetime

ROOT = Path(__file__).resolve().parent
ZIP_NAME = "lotofacil_submission.zip"
OUT_ZIP = ROOT / ZIP_NAME

# ------------------------------------------------------------
#  Contém todos os scripts necessários para reproduzir resultados
# ------------------------------------------------------------
CODE_FILES = [
    "lotogen.py", "bench.py",
    "programa2.py", "programa3.py", "programa4.py", "programa5.py",
    "verify_all.py", "calcular_custo_sb.py", "package.py"
]

DOC_FILES = [
    "README.md", "REPORT.md", "MakeFile",  # uso a grafia encontrada no repo
]

RESULT_DIRS = [
    "resultados", "prog2_saida", "prog3_saida",
    "prog4_saida", "prog5_saida", "prog7_saida"
]

PDF_DIR = ROOT / "docs"      # incluir quaisquer PDFs do relatório

# ------------------------------------------------------------

def add(z: ZipFile, path: Path, arc_prefix: str = "") -> None:
    """Adiciona arquivo / diretório recursivamente no zip."""
    if path.is_dir():
        for sub in path.iterdir():
            add(z, sub, arc_prefix + path.name + "/")
    else:
        arcname = arc_prefix + path.name
        z.write(path, arcname)
        print(f"  + {arcname}")

# ------------------------------------------------------------

def main() -> None:
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
        print("ℹ️  ZIP anterior removido.")

    with ZipFile(OUT_ZIP, "w", ZIP_DEFLATED) as z:
        print("📦  Incluindo scripts Python…")
        for fname in CODE_FILES:
            fp = ROOT / fname
            if fp.exists():
                add(z, fp)
            else:
                print(f"  ! {fname} não encontrado (ok se ainda não implementado).")

        print("📄  Incluindo documentos de topo…")
        for fname in DOC_FILES:
            fp = ROOT / fname
            if fp.exists():
                add(z, fp)
            else:
                print(f"  ! {fname} ausente.")

        print("📂  Incluindo pastas de resultados…")
        for d in RESULT_DIRS:
            dp = ROOT / d
            if dp.exists():
                add(z, dp)
            else:
                print(f"  • {d} ainda não existe — será ignorado.")

        if PDF_DIR.exists():
            print("📑  Incluindo PDFs em docs/ …")
            for pdf in PDF_DIR.glob("*.pdf"):
                add(z, pdf, "docs/")

    size_mb = OUT_ZIP.stat().st_size / (1024 * 1024)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    print(f"\n✅ {ZIP_NAME} criado ({size_mb:.1f} MB) – {stamp}")

if __name__ == "__main__":
    main()
