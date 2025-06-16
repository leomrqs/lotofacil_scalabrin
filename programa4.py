#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
programa4.py — Cenário C3: encontra SB15_12 (Greedy Set-Cover) e verifica.

Entradas esperadas
------------------
resultados/S15.csv   (3.268.760 linhas, 15 nums)
resultados/S12.csv   (5.200.300 linhas, 12 nums)

Saídas
------
prog4_saida/SB15_12.csv
prog4_saida/cover12_log.csv

──────────────────────────────────────────────────────────────────────────────
Análise de complexidade (Greedy Set-Cover)

• Pré-processamento: O(n · m)  com n = |S15|,  m = 455  (15 C 12)
  (para cada linha S15 geramos suas 455 máscaras S12)

• Loop Greedy (lazy-update):
  Tempo prático ≈ O(n · log n), pois m é uma constante relativamente pequena
  e o custo é dominado pelas operações na heap.

Memória (modo streaming):
• Índice S12 → int : 5.200.300 × 4 B ≈ 20 MB
• Vetor uncovered   : 5.200.300 bits ≈ 0.65 MB
• Heap              : |S15| × 16 B ≈ 50 MB
• Linhas S15 texto  : 55 MB
Pico medido será similar aos programas anteriores, em torno de 2.3-2.5 GB.
──────────────────────────────────────────────────────────────────────────────
"""
from __future__ import annotations

import argparse
import csv
import heapq
import itertools
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil

try:
    import bitarray
except ImportError:
    bitarray = None  # fallback

# ──────────────────────  Paths  ──────────────────────────────────────────────
BASE_IN = Path("resultados")
OUT_DIR = Path("prog4_saida")
OUT_DIR.mkdir(exist_ok=True)

S12_FILE = BASE_IN / "S12.csv"
S15_FILE = BASE_IN / "S15.csv"
SB_FILE = OUT_DIR / "SB15_12.csv"
LOG_CSV = OUT_DIR / "cover12_log.csv"

TOTAL_S12 = 5_200_300
COMBOS_PER_S15 = 455  # C(15, 12)
LOWER_BOUND = (TOTAL_S12 + COMBOS_PER_S15 - 1) // COMBOS_PER_S15  # ceil()

# ─────────────────── Bitmask helpers ────────────────────────────────────────
def seq_to_mask(seq: List[int]) -> int:
    """Converte uma sequência de números em uma máscara de bits."""
    m = 0
    for n in seq:
        m |= 1 << (n - 1)
    return m

# ────────────────────── Load S12 index ───────────────────────────────────────
def load_S12() -> Tuple[Dict[int, int], List[int]]:
    """Carrega as combinações S12, mapeando cada máscara de bits para um índice."""
    idx_map: Dict[int, int] = {}
    masks: List[int] = []
    with S12_FILE.open() as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader):
            mask = seq_to_mask(list(map(int, row)))
            idx_map[mask] = i
            masks.append(mask)
    return idx_map, masks

# ───── Sub-combinações cobertas por uma linha S15 (455 delas) ───────────────
def s15_cover_indices(nums: List[int], idx_map: Dict[int, int]) -> List[int]:
    """Gera os índices de S12 cobertos por uma única linha de S15."""
    idxs: List[int] = []
    # Para obter combinações de 12, escolhemos 3 números para omitir de 15
    for omitted_indices in itertools.combinations(range(15), 3):
        m = 0
        omitted_set = set(omitted_indices)
        for i, val in enumerate(nums):
            if i not in omitted_set:
                m |= 1 << (val - 1)
        idxs.append(idx_map[m])
    return idxs

# ───────────── Greedy Set-Cover principal ───────────────────────────────────
def greedy_set_cover(store_all: bool, pct_step: float = 1.0) -> Tuple[int, float]:
    """Executa o algoritmo Greedy Set-Cover para encontrar SB15_12."""
    t0 = time.perf_counter()
    idx_map, _ = load_S12()
    total = len(idx_map)
    uncovered: Set[int] = set(range(total))

    print("▶ Passo 1: varrendo S15 e calculando coberturas iniciais…")
    row_to_indices: List[List[int]] = []
    heap: List[Tuple[int, int]] = []
    lines_text: List[str] = []

    with S15_FILE.open() as f:
        reader = csv.reader(f)
        for row_id, row in enumerate(reader):
            lines_text.append(",".join(row))
            # Otimização: o ganho inicial é sempre 455
            heapq.heappush(heap, (-COMBOS_PER_S15, row_id))

            if store_all:
                nums = list(map(int, row))
                indices = s15_cover_indices(nums, idx_map)
                row_to_indices.append(indices)

    print("▶ Passo 2: executando Greedy Set-Cover…")
    sb_lines: List[str] = []
    next_print = pct_step
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        
        # Recalcular ganho real (lazy update)
        nums = list(map(int, lines_text[rid].split(",")))
        indices = (
            row_to_indices[rid] if store_all
            else s15_cover_indices(nums, idx_map)
        )
        true_gain_indices = [i for i in indices if i in uncovered]

        if not true_gain_indices:
            continue
        
        # Se o ganho real for menor que o da heap, re-insere e tenta o próximo
        if len(true_gain_indices) < -neg_gain:
            heapq.heappush(heap, (-len(true_gain_indices), rid))
            continue

        # Seleciona esta linha S15
        uncovered.difference_update(true_gain_indices)
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
    """Verifica se o SB gerado cobre 100% do universo S12."""
    total = len(idx_map)
    print("\n▶ Passo 3: verificando cobertura 100 % …")
    covered = bitarray.bitarray(total) if bitarray else [False] * total
    if bitarray:
        covered.setall(False)

    with SB_FILE.open() as f:
        reader = csv.reader(f)
        for row in reader:
            nums = list(map(int, row))
            for omitted_indices in itertools.combinations(range(15), 3):
                m = 0
                omitted_set = set(omitted_indices)
                for i, v in enumerate(nums):
                    if i not in omitted_set:
                        m |= 1 << (v - 1)
                covered[idx_map[m]] = True

    ok = covered.all() if bitarray else (False not in covered)
    if not ok:
        sys.exit("❌ Falha na verificação! Alguma sequência S12 não foi coberta.")
    print(f"✔ Verificação OK — todas as {total:,} sequências S12 cobertas.")

# ───────────────────────── Appender de log ───────────────────────────────────
def append_log(size_: int, seconds: float, peak_mb: float) -> None:
    """Adiciona uma linha de resultado ao arquivo de log CSV."""
    hdr = ["SB_size", "Lower_bound", "Approx_factor", "Tempo (s)", "Pico_RAM(MB)"]
    row = {
        "SB_size": size_,
        "Lower_bound": LOWER_BOUND,
        "Approx_factor": round(size_ / LOWER_BOUND, 4),
        "Tempo (s)": seconds,
        "Pico_RAM(MB)": peak_mb,
    }
    write_header = not LOG_CSV.exists()
    with LOG_CSV.open("a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        if write_header:
            w.writeheader()
        w.writerow(row)
    print("📄 Log salvo em", LOG_CSV)

# ────────────────────────── CLI & main ──────────────────────────────────────
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 4 — encontra SB15_12")
    p.add_argument(
        "--stream",
        action="store_true",
        help="menos RAM (recalcula indices on-the-fly), mais lento",
    )
    return p.parse_args()

def main() -> None:
    for f in (S12_FILE, S15_FILE):
        if not f.exists():
            sys.exit(f"❌ Arquivo {f} não encontrado. Execute a fase de geração primeiro.")

    args = parse_args()
    process = psutil.Process(os.getpid())

    sb_size, elapsed = greedy_set_cover(store_all=not args.stream)
    
    peak_mb = (
        round(process.memory_info().peak_wset / 1_048_576, 1)
        if os.name == "nt"
        else round(process.memory_info().rss / 1_048_576, 1)
    )

    idx_map, _ = load_S12()
    verify_sb(idx_map)
    append_log(sb_size, elapsed, peak_mb)

    print(
        f"\n✅ SB15_12.csv gerado ({sb_size:,} linhas) em {elapsed}s — "
        f"fator {sb_size/LOWER_BOUND:.3f} do limite; pico RAM {peak_mb} MB."
    )

if __name__ == "__main__":
    main()