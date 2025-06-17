#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
programa5.py — Cenário C4: encontra SB15_11 e verifica 100 %.

Entradas:  resultados/S15.csv   resultados/S11.csv
Saídas  :  prog5_saida/SB15_11.csv   prog5_saida/cover11_log.csv
"""

from __future__ import annotations
import argparse, csv, heapq, os, sys, time
from itertools import combinations
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil
try:
    import bitarray
except ImportError:
    bitarray = None

# ─────── Paths & consts ─────────────────────────────────────────────────────
BASE     = Path("resultados")
OUT_DIR  = Path("prog5_saida"); OUT_DIR.mkdir(exist_ok=True)

S11_FILE = BASE / "S11.csv"
S15_FILE = BASE / "S15.csv"
SB_FILE  = OUT_DIR / "SB15_11.csv"
LOG_CSV  = OUT_DIR / "cover11_log.csv"

TOTAL_S15     = 3_268_760
TOTAL_S11     = 4_457_400
SUB_PER_LINE  = 1_365                  # 15 C 11
LOWER_BOUND   = (TOTAL_S11 + SUB_PER_LINE - 1)//SUB_PER_LINE   # 3 266

# ─────── Helpers ────────────────────────────────────────────────────────────
def mask(seq: List[int]) -> int:
    m = 0
    for v in seq: m |= 1 << (v-1)
    return m

def load_S11() -> Tuple[Dict[int,int], List[int]]:
    idx, lst = {}, []
    with S11_FILE.open() as f:
        for i, row in enumerate(csv.reader(f)):
            m = mask(list(map(int,row)))
            idx[m] = i
            lst.append(m)
    return idx, lst

OMIT_LIST = list(combinations(range(15),4))  # 1 365 tuples of 4 indices

def cover_ids(nums: List[int], idx_map: Dict[int,int]) -> List[int]:
    """Gera lista de ids S11 cobertos removendo 4 posições."""
    full = 0
    bits = [1 << (n-1) for n in nums]
    for b in bits: full |= b
    ids = []
    for omit in OMIT_LIST:
        m = full
        m ^= bits[omit[0]] | bits[omit[1]] | bits[omit[2]] | bits[omit[3]]
        ids.append(idx_map[m])
    return ids           # len = 1 365

# ─────── Greedy Set-Cover ───────────────────────────────────────────────────
def greedy(store_all: bool) -> Tuple[int,float]:
    t0      = time.perf_counter()
    idx_map, _ = load_S11()
    uncovered: Set[int] = set(range(len(idx_map)))

    print("▶ 1/3  Varredura inicial…")
    row_to_idx: List[List[int]] = []
    heap: List[Tuple[int,int]]  = []
    lines: List[str]            = []

    STEP = 50_000
    with S15_FILE.open() as f:
        for rid, row in enumerate(csv.reader(f), 1):
            nums = list(map(int,row))
            ids  = cover_ids(nums, idx_map)

            lines.append(",".join(row))
            if store_all: row_to_idx.append(ids)
            heapq.heappush(heap, (-SUB_PER_LINE, rid-1))

            if rid % STEP == 0 or rid == TOTAL_S15:
                pct = 100*rid/TOTAL_S15
                spd = rid/(time.perf_counter()-t0)
                print(f"   {pct:5.1f}% lido ({rid:,}/{TOTAL_S15:,}) "
                      f"– {spd:,.0f} linhas/s")

    print("▶ 2/3  Greedy Set-Cover…")
    chosen: List[str] = []
    next_print = 1.0
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        nums = list(map(int, lines[rid].split(",")))
        ids  = row_to_idx[rid] if store_all else cover_ids(nums, idx_map)

        new_ids = [i for i in ids if i in uncovered]
        if not new_ids:
            continue
        if len(new_ids) < -neg_gain:   # lazy-update
            heapq.heappush(heap, (-len(new_ids), rid))
            continue

        uncovered.difference_update(new_ids)
        chosen.append(lines[rid])

        pct = 100*(TOTAL_S11 - len(uncovered))/TOTAL_S11
        if pct >= next_print or not uncovered:
            print(f"   {pct:6.2f}% coberto | SB tamanho: {len(chosen):,}")
            next_print += 1.0

    SB_FILE.write_text("\n".join(chosen), encoding="ascii")
    return len(chosen), round(time.perf_counter()-t0,1)

# ─────── Verificação 100 % ──────────────────────────────────────────────────
def verify(idx_map: Dict[int,int]) -> None:
    print("\n▶ 3/3  Verificando cobertura…")
    total   = len(idx_map)
    covered = bitarray.bitarray(total) if bitarray else [False]*total
    if bitarray: covered.setall(False)

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            nums = list(map(int,row))
            bits = [1<<(n-1) for n in nums]
            full = 0
            for b in bits: full |= b
            for omit in OMIT_LIST:
                m = full ^ (bits[omit[0]]|bits[omit[1]]|bits[omit[2]]|bits[omit[3]])
                covered[idx_map[m]] = True

    ok = covered.all() if bitarray else (False not in covered)
    print("✔ Cobertura 100 % confirmada." if ok else
          "❌ Falha: alguma S11 não coberta!")
    if not ok: sys.exit(1)

# ─────── CSV Log ────────────────────────────────────────────────────────────
def log(size_:int, secs:float, peak:float)->None:
    import csv
    hdr = ["SB_size","Lower_bound","Approx_factor","Tempo (s)","Pico_RAM(MB)"]
    line= {"SB_size":size_,"Lower_bound":LOWER_BOUND,
           "Approx_factor":round(size_/LOWER_BOUND,4),
           "Tempo (s)":secs,"Pico_RAM(MB)":peak}
    first = not LOG_CSV.exists()
    with LOG_CSV.open("a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=hdr)
        if first: w.writeheader()
        w.writerow(line)
    print("📄 Log salvo em", LOG_CSV)

# ─────── CLI / Main ─────────────────────────────────────────────────────────
def parse_args()->argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 5 — SB15_11")
    p.add_argument("--stream", action="store_true",
                   help="economiza RAM (não armazena idxs)")
    return p.parse_args()

def main()->None:
    for f in (S11_FILE, S15_FILE):
        if not f.exists():
            sys.exit(f"❌ {f} não encontrado. Gere os CSV primeiro.")

    args = parse_args()
    proc = psutil.Process(os.getpid())

    sb_size, secs = greedy(store_all=not args.stream)
    peak = round(proc.memory_info().peak_wset/1_048_576,1) if os.name=="nt" \
           else round(proc.memory_info().rss/1_048_576,1)

    idx_map,_ = load_S11()
    verify(idx_map)
    log(sb_size, secs, peak)

    print(f"\n✅ SB15_11.csv gerado ({sb_size:,} linhas) em {secs}s — "
          f"fator {sb_size/LOWER_BOUND:.3f} do limite; pico RAM {peak} MB.")

if __name__ == "__main__":
    main()
