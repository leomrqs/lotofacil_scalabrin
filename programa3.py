#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
programa3.py — Cenário C2: encontra SB15_13 (Greedy Set-Cover) e verifica.

Entradas esperadas
------------------
resultados/S15.csv   (3 268 760 linhas, 15 nums)
resultados/S13.csv   (5 200 300 linhas, 13 nums)

Saídas
------
prog3_saida/SB15_13.csv
prog3_saida/cover13_log.csv

──────────────────────────────────────────────────────────────────────────────
Análise de complexidade (Greedy Set-Cover)

• Pré-processamento: O(n · m)  com n = |S15|,  m = 105  (15 C 13)
  (para cada linha S15 geramos suas 105 máscaras S13)

• Loop Greedy (lazy-update):
    – heap-pop/push log n
    – Máximo |SB| ≈ 12 k iterações
  Tempo prático ≈ O(n · log n)  pois m é constante.

Memória (modo streaming):
• Índice S13 → int : 5 200 300 × 4 B ≈ 20 MB
• Vetor uncovered  : 5 200 300 bits ≈ 0.65 MB
• Heap            : |S15| × 16 B ≈ 50 MB
• Linhas S15 texto: 55 MB
Pico medido ≈ 2.3 GB (overhead Python).
──────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import argparse, csv, heapq, os, sys, time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil

try:
    import bitarray
except ImportError:
    bitarray = None  # fallback

# ──────────────────────  Paths  ──────────────────────────────────────────────
BASE_IN  = Path("resultados")
OUT_DIR  = Path("prog3_saida")
OUT_DIR.mkdir(exist_ok=True)

S13_FILE = BASE_IN / "S13.csv"
S15_FILE = BASE_IN / "S15.csv"
SB_FILE  = OUT_DIR / "SB15_13.csv"
LOG_CSV  = OUT_DIR / "cover13_log.csv"

TOTAL_S13 = 5_200_300
LOWER_BOUND = (TOTAL_S13 + 104) // 105     # ceil(5200300 / 105) = 49 526

# ─────────────────── Bitmask helpers ────────────────────────────────────────
def seq_to_mask(seq: List[int]) -> int:
    m = 0
    for n in seq:
        m |= 1 << (n - 1)
    return m

# ────────────────────── Load S13 index ───────────────────────────────────────
def load_S13() -> Tuple[Dict[int, int], List[int]]:
    idx_map: Dict[int, int] = {}
    masks: List[int] = []
    with S13_FILE.open() as f:
        for i, row in enumerate(csv.reader(f)):
            mask = seq_to_mask(list(map(int, row)))
            idx_map[mask] = i
            masks.append(mask)
    return idx_map, masks

# ───── Sub-combinações cobertas por uma linha S15 (105 delas) ───────────────
def s15_cover_indices(nums: List[int], idx_map: Dict[int, int]) -> List[int]:
    idxs: List[int] = []
    n = len(nums)  # 15
    for i in range(n - 1):
        for j in range(i + 1, n):
            m = 0
            for k, val in enumerate(nums):
                if k != i and k != j:          # mantém 13 números
                    m |= 1 << (val - 1)
            idxs.append(idx_map[m])
    return idxs          # len == 105

# ───────────── Greedy Set-Cover principal ───────────────────────────────────
def greedy_set_cover(store_all: bool, pct_step: float = 1.0) -> Tuple[int, float]:
    t0 = time.perf_counter()
    idx_map, _ = load_S13()
    total = len(idx_map)
    uncovered: Set[int] = set(range(total))

    print("▶ Passo 1: varrendo S15 e calculando coberturas…")
    row_to_indices: List[List[int]] = []
    heap: List[Tuple[int, int]] = []
    lines_text: List[str] = []

    with S15_FILE.open() as f:
        for row_id, row in enumerate(csv.reader(f)):
            nums = list(map(int, row))
            indices = s15_cover_indices(nums, idx_map)
            lines_text.append(",".join(row))

            if store_all:
                row_to_indices.append(indices)

            heapq.heappush(heap, (-105, row_id))  # ganho máximo 105

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
        if len(true_gain) < -neg_gain:  # lazy update
            heapq.heappush(heap, (-len(true_gain), rid))
            continue

        uncovered.difference_update(true_gain)
        sb_lines.append(lines_text[rid])

        pct = 100 * (total - len(uncovered)) / total
        if pct >= next_print or not uncovered:
            print(f"   {pct:6.2f}% coberto | SB tamanho: {len(sb_lines):,}")
            next_print += pct_step

    SB_FILE.write_text("\n".join(sb_lines), encoding="ascii")
    elapsed = round(time.perf_counter() - t0, 1)
    return len(sb_lines), elapsed

# ──────────────────── Verificação completa ─────────────────────────────────-
def verify_sb(idx_map: Dict[int, int]) -> None:
    total = len(idx_map)
    print("\n▶ Passo 3: verificando cobertura 100 % …")
    covered = bitarray.bitarray(total) if bitarray else [False]*total
    if bitarray: covered.setall(False)

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            nums = list(map(int, row))
            for i in range(14):
                for j in range(i+1,15):
                    m = 0
                    for k, v in enumerate(nums):
                        if k != i and k != j:
                            m |= 1 << (v-1)
                    covered[idx_map[m]] = True

    ok = covered.all() if bitarray else (False not in covered)
    if not ok:
        sys.exit("❌ Falha: alguma S13 não coberta!")
    print("✔ Verificação OK — todas as 5 200 300 sequências cobertas.")

# ───────────────────────── Appender de log ───────────────────────────────────
def append_log(size_: int, seconds: float, peak_mb: float) -> None:
    import csv
    hdr = ["SB_size","Lower_bound","Approx_factor","Tempo (s)","Pico_RAM(MB)"]
    row = {
        "SB_size": size_,
        "Lower_bound": LOWER_BOUND,
        "Approx_factor": round(size_/LOWER_BOUND,4),
        "Tempo (s)": seconds,
        "Pico_RAM(MB)": peak_mb
    }
    write_header = not LOG_CSV.exists()
    with LOG_CSV.open("a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        if write_header: w.writeheader()
        w.writerow(row)
    print("📄 Log salvo em", LOG_CSV)

# ────────────────────────── CLI & main ──────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 3 — encontra SB15_13")
    p.add_argument("--stream", action="store_true",
                   help="menos RAM (recalcula indices on-the-fly), ~3× mais lento")
    return p.parse_args()

def main() -> None:
    for f in (S13_FILE,S15_FILE):
        if not f.exists():
            sys.exit(f"❌ Arquivo {f} não encontrado. Gere dados primeiro.")

    args = parse_args()
    process = psutil.Process(os.getpid())

    sb_size, elapsed = greedy_set_cover(store_all=not args.stream)
    peak_mb = round(process.memory_info().peak_wset/1_048_576,1) if os.name=="nt" \
              else round(process.memory_info().rss/1_048_576,1)

    idx_map,_ = load_S13()
    verify_sb(idx_map)
    append_log(sb_size, elapsed, peak_mb)

    print(f"\n✅ SB15_13.csv gerado ({sb_size:,} linhas) em {elapsed}s — "
          f"fator {sb_size/LOWER_BOUND:.3f} do limite; pico RAM {peak_mb} MB.")

if __name__ == "__main__":
    main()
