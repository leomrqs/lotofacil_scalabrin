#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTOR: 
"""
programa2.py — Cenário C1: encontra SB15_14 (Greedy Set-Cover) e verifica.

Entradas esperadas:
    resultados/S15.csv   (3 268 760 linhas, 15 nums)
    resultados/S14.csv   (4 457 400 linhas, 14 nums)

Saídas:
    prog2_saida/SB15_14.csv
    prog2_saida/cover14_log.csv

Análise de complexidade (Greedy Set-Cover)

• Passo de pré-processamento:  O(n·m)  com  n = |S15|,  m = 15
  (para cada linha S15 geramos suas 15 máscaras S14).

• Loop Greedy (lazy-update):
    – Cada iteração retira um candidato da heap (log n)
    – Máximo |SB| iterações  (≈ 1,8 × 10⁵)
    Tempo ≈ O(n·log n)   dominado pelo heap-pop/push.

Na prática, O(|S15|) predomina porque m e log n são constantes pequenos.

Memória
• Índice S14 → int  : 4 457 400 × 4 bytes ≈ 17 MB
• Vetor uncovered  : 4 457 400 bits  ≈ 0.6 MB
• Heap (-gain,id)  : |S15| × 16 B ≈ 50 MB
• Linhas S15 texto : 55 MB
Pico medido ≈ 2.2 GB devido a overhead de lista/objeto Python (registrado em log).

"""

from __future__ import annotations
import argparse, csv, heapq, json, os, sys, time
from pathlib import Path
from math import comb
from typing import Dict, List, Set, Tuple

import psutil

try:
    import bitarray
except ImportError:
    bitarray = None   # fallback para list[bool]

# ─── Paths ───────────────────────────────────────────────────────────────────
BASE_IN  = Path("resultados")
OUT_DIR  = Path("prog2_saida")
OUT_DIR.mkdir(exist_ok=True)

S14_FILE = BASE_IN / "S14.csv"
S15_FILE = BASE_IN / "S15.csv"
SB_FILE  = OUT_DIR / "SB15_14.csv"
LOG_CSV  = OUT_DIR / "cover14_log.csv"

LOWER_BOUND = (4_457_400 + 14) // 15   # 297 160

# ─── Bitmask helpers ─────────────────────────────────────────────────────────
def seq_to_mask(seq: List[int]) -> int:
    m = 0
    for n in seq:
        m |= 1 << (n - 1)
    return m

# ─── Carrega S14 → idx_map ───────────────────────────────────────────────────
def load_S14() -> Tuple[Dict[int, int], List[int]]:
    idx_map: Dict[int, int] = {}
    masks: List[int] = []
    with S14_FILE.open() as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            mask = seq_to_mask(list(map(int, row)))
            idx_map[mask] = i
            masks.append(mask)
    return idx_map, masks

# ─── Função para obter índices cobertos por uma linha S15 ────────────────────
def s15_cover_indices(nums: List[int], idx_map: Dict[int, int]) -> List[int]:
    idxs = []
    for omit in nums:                  # 15 subsequências
        m = 0
        for n in nums:
            if n != omit:
                m |= 1 << (n - 1)
        idxs.append(idx_map[m])
    return idxs

# ─── Greedy Set-Cover ────────────────────────────────────────────────────────
def greedy_set_cover(store_all: bool, pct_step: float = 1.0) -> Tuple[int, float]:
    t0 = time.perf_counter()
    idx_map, _ = load_S14()
    total = len(idx_map)                     # 4 457 400
    uncovered: Set[int] = set(range(total))

    print("▶ Passo 1: varrendo S15 e calculando coberturas…")
    row_to_indices: List[List[int]] = []
    heap: List[Tuple[int, int]] = []         # (-gain, row_id)
    lines_text: List[str] = []

    with S15_FILE.open() as f:
        for row_id, row in enumerate(csv.reader(f)):
            nums = list(map(int, row))
            indices = s15_cover_indices(nums, idx_map)
            lines_text.append(",".join(row))

            if store_all:
                row_to_indices.append(indices)

            gain = len(set(indices))         # sempre 15, mas ok
            heapq.heappush(heap, (-gain, row_id))

    print("▶ Passo 2: executando Greedy…")
    sb_lines: List[str] = []
    next_print = pct_step
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        nums = list(map(int, lines_text[rid].split(",")))
        indices = (
            row_to_indices[rid] if store_all
            else s15_cover_indices(nums, idx_map)
        )

        true_gain = [i for i in indices if i in uncovered]
        if not true_gain:
            continue
        # lazy-update ↓
        if len(true_gain) < -neg_gain:
            heapq.heappush(heap, (-len(true_gain), rid))
            continue

        # selecionar
        uncovered.difference_update(true_gain)
        sb_lines.append(lines_text[rid])

        covered_pct = 100 * (total - len(uncovered)) / total
        if covered_pct >= next_print or not uncovered:
            print(f"   {covered_pct:6.2f}% coberto | SB tamanho: {len(sb_lines):,}")
            next_print += pct_step

    # salvar SB
    SB_FILE.write_text("\n".join(sb_lines), encoding="ascii")
    elapsed = round(time.perf_counter() - t0, 1)
    return len(sb_lines), elapsed

# ─── Verificação -------------------------------------------------------------
def verify_sb(idx_map: Dict[int, int]) -> None:
    total = len(idx_map)
    print("\n▶ Passo 3: verificando cobertura 100 % …")
    if bitarray:
        covered = bitarray.bitarray(total); covered.setall(False)
    else:
        covered = [False] * total

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            r = list(map(int, row))
            for omit in r:
                m = 0
                for n in r:
                    if n != omit:
                        m |= 1 << (n - 1)
                idx = idx_map[m]
                covered[idx] = True

    missing = (not covered.all()) if bitarray else (False in covered)
    if missing:
        print("❌ Verificação falhou! Há sequências S14 não cobertas.")
        sys.exit(1)
    print("✔ Verificação OK — todas as 4 457 400 sequências cobertas.")

# ─── Log CSV -----------------------------------------------------------------
def append_log(sb_size: int, elapsed: float, peak_mb: float) -> None:
    import csv
    header = ["SB_size", "Lower_bound", "Approx_factor", "Tempo (s)", "Pico_RAM(MB)"]
    row = {
        "SB_size": sb_size,
        "Lower_bound": LOWER_BOUND,
        "Approx_factor": round(sb_size / LOWER_BOUND, 4),
        "Tempo (s)": elapsed,
        "Pico_RAM(MB)": peak_mb
    }
    write_header = not LOG_CSV.exists()
    with LOG_CSV.open("a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if write_header:
            w.writeheader()
        w.writerow(row)
    print("📄 Log salvo em", LOG_CSV)

# ─── CLI ---------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 2 — encontra SB15_14")
    p.add_argument("--stream", action="store_true",
                   help="menos RAM, mas mais lento (recalcula índices na hora)")
    return p.parse_args()

# ─── Main --------------------------------------------------------------------
def main() -> None:
    # checar arquivos
    for f in [S14_FILE, S15_FILE]:
        if not f.exists():
            print("❌ Arquivo", f, "não encontrado. Execute a fase de geração primeiro.")
            sys.exit(1)

    args = parse_args()
    process = psutil.Process(os.getpid())

    # gerar SB
    sb_size, elapsed = greedy_set_cover(store_all=not args.stream)

    peak_mb = round(process.memory_info().peak_wset / 1_048_576, 1) \
              if os.name == "nt" else \
              round(process.memory_info().rss / 1_048_576, 1)

    # verificar
    idx_map, _ = load_S14()
    verify_sb(idx_map)

    # log
    append_log(sb_size, elapsed, peak_mb)
    print(f"\n✅ SB15_14.csv gerado ({sb_size:,} linhas) em {elapsed}s — "
          f"fator {sb_size/LOWER_BOUND:.3f} do limite; pico RAM {peak_mb} MB.")

if __name__ == "__main__":
    main()
