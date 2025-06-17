#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
programa4.py — Cenário C3: encontra SB15_12 e verifica 100 %.

Entradas (gerados por bench.py):
    resultados/S15.csv   (3 268 760 linhas, 15 números)
    resultados/S12.csv   (5 200 300 linhas, 12 números)
Saídas:
    prog4_saida/SB15_12.csv
    prog4_saida/cover12_log.csv
"""
from __future__ import annotations

import argparse
import csv
import heapq
import os
import sys
import time
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil

try:
    import bitarray
except ImportError:
    bitarray = None  # fallback para list[bool]

# ────────────────────────── CONSTANTES & PATHS ────────────────────────────
BASE_DIR = Path("resultados")
OUT_DIR = Path("prog4_saida")
OUT_DIR.mkdir(exist_ok=True)

S12_FILE = BASE_DIR / "S12.csv"
S15_FILE = BASE_DIR / "S15.csv"
SB_FILE = OUT_DIR / "SB15_12.csv"
LOG_CSV = OUT_DIR / "cover12_log.csv"

TOTAL_S15 = 3_268_760
TOTAL_S12 = 5_200_300
SUB_PER_LINE = 455  # C(15,12)
LOWER_BOUND = (TOTAL_S12 + SUB_PER_LINE - 1) // SUB_PER_LINE  # 11 431

# ────────────────────────────── HELPERS ───────────────────────────────────

def mask(seq: List[int]) -> int:
    """Converte sequência para bitmask de 25 bits."""
    m = 0
    for v in seq:
        m |= 1 << (v - 1)
    return m


def load_S12() -> Tuple[Dict[int, int], List[int]]:
    """Carrega S12.csv e devolve (mask→id, lista_masks)."""
    idx_map: Dict[int, int] = {}
    masks: List[int] = []
    with S12_FILE.open() as f:
        for i, row in enumerate(csv.reader(f)):
            m = mask(list(map(int, row)))
            idx_map[m] = i
            masks.append(m)
    return idx_map, masks


# Lista de 455 combinações de 3 posições para omitir
OMIT_LIST = list(combinations(range(15), 3))


def cover_ids(nums: List[int], idx_map: Dict[int, int]) -> List[int]:
    """Retorna lista de ids S12 cobertos por esta linha S15."""
    bits = [1 << (n - 1) for n in nums]
    full = 0
    for b in bits:
        full |= b
    ids: List[int] = []
    for a, b, c in OMIT_LIST:
        m = full ^ (bits[a] | bits[b] | bits[c])
        ids.append(idx_map[m])
    return ids  # len == 455

# ─────────────────────────── GREEDY SET‑COVER ─────────────────────────────

def greedy(store_all: bool) -> Tuple[int, float]:
    t0 = time.perf_counter()
    idx_map, _ = load_S12()
    uncovered: Set[int] = set(range(len(idx_map)))

    print("▶ 1/3  Varredura inicial…")
    row_to_idx: List[List[int]] = []
    heap: List[Tuple[int, int]] = []
    lines: List[str] = []

    STEP = 50_000
    with S15_FILE.open() as f:
        for rid, row in enumerate(csv.reader(f), 1):
            nums = list(map(int, row))
            ids = cover_ids(nums, idx_map)

            lines.append(",".join(row))
            if store_all:
                row_to_idx.append(ids)
            heapq.heappush(heap, (-SUB_PER_LINE, rid - 1))

            if rid % STEP == 0 or rid == TOTAL_S15:
                pct = 100 * rid / TOTAL_S15
                speed = rid / (time.perf_counter() - t0)
                print(f"   {pct:5.1f}% lido ({rid:,}/{TOTAL_S15:,}) – {speed:,.0f} linhas/s")

    print("▶ 2/3  Greedy Set-Cover…")
    chosen: List[str] = []
    next_print = 1.0
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        nums = list(map(int, lines[rid].split(",")))
        ids = row_to_idx[rid] if store_all else cover_ids(nums, idx_map)

        new_ids = [i for i in ids if i in uncovered]
        if not new_ids:
            continue
        if len(new_ids) < -neg_gain:  # lazy-update
            heapq.heappush(heap, (-len(new_ids), rid))
            continue

        uncovered.difference_update(new_ids)
        chosen.append(lines[rid])

        pct = 100 * (TOTAL_S12 - len(uncovered)) / TOTAL_S12
        if pct >= next_print or not uncovered:
            print(f"   {pct:6.2f}% coberto | SB tamanho: {len(chosen):,}")
            next_print += 1.0

    SB_FILE.write_text("\n".join(chosen), encoding="ascii")
    return len(chosen), round(time.perf_counter() - t0, 1)

# ──────────────────────────── VERIFICAÇÃO ─────────────────────────────────

def verify(idx_map: Dict[int, int]) -> None:
    print("\n▶ 3/3  Verificando cobertura…")
    total = len(idx_map)
    covered = bitarray.bitarray(total) if bitarray else [False] * total
    if bitarray:
        covered.setall(False)

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            nums = list(map(int, row))
            bits = [1 << (n - 1) for n in nums]
            full = 0
            for b in bits:
                full |= b
            for a, b, c in OMIT_LIST:
                m = full ^ (bits[a] | bits[b] | bits[c])
                covered[idx_map[m]] = True

    ok = covered.all() if bitarray else (False not in covered)
    if not ok:
        sys.exit("❌ Falha: alguma S12 não coberta!")
    print("✔ Cobertura 100 % confirmada.")

# ───────────────────────────── CSV LOG ─────────────────────────────────────

def log(size_: int, secs: float, peak: float) -> None:
    hdr = ["SB_size", "Lower_bound", "Approx_factor", "Tempo (s)", "Pico_RAM(MB)"]
    row = {
        "SB_size": size_,
        "Lower_bound": LOWER_BOUND,
        "Approx_factor": round(size_ / LOWER_BOUND, 4),
        "Tempo (s)": secs,
        "Pico_RAM(MB)": peak,
    }
    first = not LOG_CSV.exists()
    with LOG_CSV.open("a", newline="", encoding="utf8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=hdr)
        if first:
            writer.writeheader()
        writer.writerow(row)
    print("📄 Log salvo em", LOG_CSV)

# ───────────────────────────── CLI / MAIN ──────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 4 — SB15_12")
    p.add_argument("--stream", action="store_true", help="economiza RAM (on-the-fly)")
    return p.parse_args()


def main() -> None:
    # Check files exist
    for f in (S12_FILE, S15_FILE):
        if not f.exists():
            sys.exit(f"❌ Arquivo {f} não encontrado. Execute bench.py primeiro.")

    args = parse_args()
    process = psutil.Process(os.getpid())

    sb_size, secs = greedy(store_all=not args.stream)

    peak_mb = (
        round(process.memory_info().peak_wset / 1_048_576, 1)
        if os.name == "nt"
        else round(process.memory_info().rss / 1_048_576, 1)
    )

    idx_map, _ = load_S12()
    verify(idx_map)
    log(sb_size, secs, peak_mb)

    print(
        (
            f"\n✅ SB15_12.csv gerado ({sb_size:,} linhas) em {secs}s — "
            f"fator {sb_size / LOWER_BOUND:.3f} do limite; pico RAM {peak_mb} MB."
        )
    )


if __name__ == "__main__":
    main()
