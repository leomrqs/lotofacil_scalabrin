#!/usr/bin/env python3
# AUTOR - Leonardo dos Santos Marques & Igor Mamus
"""
bench.py — Benchmark Lotofácil (gera Sk → CSV, mede desempenho)

Fluxo padrão
------------
1. Limpa ./resultados/ (salvo --keep)
2. Para cada k (15-11 ou lista fornecida):
   • executa lotogen.py  →  S{k}.csv
   • mede Tempo, Vazão, Pico RAM, CPU user/sys, I/O gravado
3. Grava resultados/bench.csv  (cabeçalhos com unidades claras)
4. Empacota S*.csv em:
      resultados/resultados.tar        (rápido, sem compressão)
   ou resultados/resultados.tar.gz     (--gz, mais lento)

Uso:
    python bench.py            # completo, tar sem gzip
    python bench.py --gz       # tar.gz
    python bench.py 15 13 --notar   # apenas S15 e S13, sem tar
Requer:  pip install psutil
"""

from __future__ import annotations

import argparse
import csv
import shutil
import tarfile
import time
from math import comb
from pathlib import Path
from typing import List

import psutil
import subprocess

# ─── Configurações ───────────────────────────────────────────────────────────
RESULT_DIR = Path("resultados")
DEFAULT_KS = [15, 14, 13, 12, 11]

LOG_CSV = RESULT_DIR / "bench.csv"
TAR_RAW = RESULT_DIR / "resultados.tar"
TAR_GZ  = RESULT_DIR / "resultados.tar.gz"

CSV_HEADER = [
    "k",
    "Combinações",
    "Tempo (s)",
    "Linhas/s",
    "Arquivo (MB)",
    "MB gravados/s",
    "Pico RAM (MB)",
    "CPU usuário (s)",
    "CPU sistema (s)",
    "I/O gravado (MB)",
    "Arquivo",
]


# ─── Utilidades ──────────────────────────────────────────────────────────────
def mb(val_bytes: int, digits: int = 1) -> float:
    """Converte bytes → MB com arredondamento."""
    return round(val_bytes / 1_048_576, digits)


def clean_result_dir() -> None:
    if RESULT_DIR.exists():
        shutil.rmtree(RESULT_DIR)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


# ─── Núcleo de coleta ────────────────────────────────────────────────────────
def run_generator(k: int) -> dict:
    """Executa lotogen.py e retorna dicionário de métricas de desempenho."""
    cmd = ["python", "lotogen.py", str(k), "--csv", "--outdir", str(RESULT_DIR)]
    print("⚙️ ", " ".join(cmd))

    start = time.perf_counter()
    proc = subprocess.Popen(cmd)
    psp = psutil.Process(proc.pid)

    peak_rss = 0
    last_cpu_user = last_cpu_sys = last_io_bytes = 0

    while proc.poll() is None:  # loop até término
        try:
            mem = psp.memory_info().rss
            peak_rss = max(peak_rss, mem)
            last_cpu_user, last_cpu_sys = psp.cpu_times()[:2]
            last_io_bytes = psp.io_counters().write_bytes
        except psutil.Error:
            break  # processo já finalizado
        time.sleep(0.1)

    elapsed = round(time.perf_counter() - start, 2)
    combos = comb(25, k)
    lines_s = round(combos / elapsed, 1)

    file_path = RESULT_DIR / f"S{k}.csv"
    size_mb = mb(file_path.stat().st_size)
    mb_s = round(size_mb / elapsed, 2)

    return {
        "k": k,
        "Combinações": combos,
        "Tempo (s)": elapsed,
        "Linhas/s": lines_s,
        "Arquivo (MB)": size_mb,
        "MB gravados/s": mb_s,
        "Pico RAM (MB)": mb(peak_rss),
        "CPU usuário (s)": round(last_cpu_user, 2),
        "CPU sistema (s)": round(last_cpu_sys, 2),
        "I/O gravado (MB)": mb(last_io_bytes),
        "Arquivo": file_path.name,
    }


# ─── Persistência ────────────────────────────────────────────────────────────
def save_csv(rows: List[dict]) -> None:
    """Grava bench.csv com cabeçalhos amigáveis."""
    with LOG_CSV.open("w", newline="", encoding="utf8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        writer.writeheader()
        writer.writerows(rows)
    print("📄 Log salvo em", LOG_CSV)


def create_tar(rows: List[dict], compress: bool) -> None:
    """Empacota todos os S*.csv em tar (com ou sem gzip)."""
    tar_path = TAR_GZ if compress else TAR_RAW
    mode = "w:gz" if compress else "w"
    print("🗜️  Empacotando em", tar_path.name)
    with tarfile.open(tar_path, mode) as tar:
        for r in rows:
            src = RESULT_DIR / r["Arquivo"]
            print("  • adicionando", src.name)
            tar.add(src, arcname=src.name)
    print("📦", tar_path, "criado.")


# ─── CLI ─────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Benchmark Lotofácil (Sk → CSV)")
    ap.add_argument("ks", metavar="K", type=int, nargs="*", help="lista de k (vazio → 15…11)")
    ap.add_argument("--keep", action="store_true", help="não limpar ./resultados/")
    ap.add_argument("--gz",   action="store_true", help="criar resultados.tar.gz (compactado)")
    ap.add_argument("--notar", action="store_true", help="não criar arquivo tar")
    return ap.parse_args()


# ─── Execução principal ─────────────────────────────────────────────────────
def main() -> None:
    args = parse_args()
    ks = DEFAULT_KS if not args.ks else args.ks

    if not args.keep and ks == DEFAULT_KS:
        clean_result_dir()
    else:
        RESULT_DIR.mkdir(exist_ok=True)

    rows = [run_generator(k) for k in ks]
    save_csv(rows)

    if not args.notar:
        create_tar(rows, compress=args.gz)


if __name__ == "__main__":
    main()
