#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTOR: Equipe Lotofácil  (Leonardo • Igor • Felipe • João)
"""
Programa 4 — Cenário C3
──────────────────────────────────────────────────────────────────────────────
Encontra **SB15_12** (subconjunto de S15 que cobre 100 % de S12) com
heurística **Greedy Set-Cover**.

Gera:
  • prog4_saida/SB15_12.csv           — subconjunto obtido
  • prog4_saida/cover12_log.csv       — métricas + α / ln|U|
  • prog4_saida/complexity_plot.png   — gráfico evidenciando O(n log n)

Derivação de complexidade
──────────────────────────────────────────────────────────────────────────────
Pré-processamento …  Θ(n·m)  com  n = |S15| ≈ 3,27 M  e  m = 455 = C(15,12)
Loop Greedy ……...…  Θ(n·log n)   (heap-pop/push a cada iteração)

⇒  T(n)  =  Θ(n log n)    (curva usada no gráfico).

Memória (modo padrão, `store_all=True`)
  • Índice S12        5 200 300 × 4 B ≈  20 MiB
  • Heap (-gain,id)    |S15| × 16 B ≈  50 MiB
  • Linhas S15 (txt)                     55 MiB
  • Overhead Python  →  pico medido ≈ 12,8 GiB
Modo `--stream` recalc. ids on-the-fly (≈3× mais lento, –4 GiB).

──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse
import csv
import heapq
import os
import sys
import time
from itertools import combinations
from math import log
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil

try:
    import bitarray
except ImportError:
    bitarray = None  # fallback se lib não instalada

# ─────────────────────────── PATHS & CONSTANTES ────────────────────────────
BASE_DIR   = Path("resultados")
OUT_DIR    = Path("prog4_saida");  OUT_DIR.mkdir(exist_ok=True)

S12_FILE   = BASE_DIR / "S12.csv"
S15_FILE   = BASE_DIR / "S15.csv"

SB_FILE    = OUT_DIR / "SB15_12.csv"
LOG_CSV    = OUT_DIR / "cover12_log.csv"
PLOT_PNG   = OUT_DIR / "complexity_plot.png"

TOTAL_S15      = 3_268_760
TOTAL_S12      = 5_200_300
SUB_PER_LINE   = 455                  # C(15,12)
LOWER_BOUND    = (TOTAL_S12 + SUB_PER_LINE - 1)//SUB_PER_LINE   # 11 431
LN_BOUND       = log(TOTAL_S12) + 1   # p/ relação α / ln

# ───────────────────────────── BITMASK HELPERS ─────────────────────────────
def mask_of(seq: List[int]) -> int:
    m = 0
    for v in seq:
        m |= 1 << (v-1)
    return m

def load_S12() -> Tuple[Dict[int,int], List[int]]:
    idx, masks = {}, []
    with S12_FILE.open() as f:
        for i, row in enumerate(csv.reader(f)):
            m = mask_of(list(map(int,row)))
            idx[m] = i
            masks.append(m)
    return idx, masks

# 455 tuplas de 3 posições a omitir
OMIT_LIST = list(combinations(range(15), 3))

def cover_ids(nums: List[int], idx_map: Dict[int,int]) -> List[int]:
    """Retorna ids S12 cobertos por esta linha S15."""
    bits  = [1 << (n-1) for n in nums]
    full  = 0
    for b in bits:
        full |= b
    ids: List[int] = []
    for a,b,c in OMIT_LIST:
        m = full ^ (bits[a] | bits[b] | bits[c])
        ids.append(idx_map[m])
    return ids        # len = 455

# ─────────────────────────── GREEDY SET-COVER ──────────────────────────────
def greedy(store_all: bool) -> Tuple[int,float]:
    t0        = time.perf_counter()
    idx_map,_ = load_S12()
    total     = len(idx_map)
    uncovered: Set[int] = set(range(total))

    # amostras para gráfico (25,50,75,100 %)
    milestones = {int(k*0.25*TOTAL_S15) for k in range(1,5)}
    samples: List[Tuple[int,float]] = []

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
            if store_all:
                row_to_idx.append(ids)
            heapq.heappush(heap, (-SUB_PER_LINE, rid-1))

            if rid % STEP == 0 or rid == TOTAL_S15:
                pct = 100*rid/TOTAL_S15
                spd = rid/(time.perf_counter()-t0)
                print(f"   {pct:5.1f}% lido ({rid:,}/{TOTAL_S15:,}) – {spd:,.0f} linhas/s")

            if rid in milestones:
                samples.append( (rid, time.perf_counter()-t0) )

    print("▶ 2/3  Greedy Set-Cover…")
    chosen: List[str] = []
    next_print = 1.0
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        ids = row_to_idx[rid] if store_all else cover_ids(
            list(map(int, lines[rid].split(","))), idx_map)

        new = [i for i in ids if i in uncovered]
        if not new:
            continue
        if len(new) < -neg_gain:               # lazy-update
            heapq.heappush(heap, (-len(new), rid))
            continue

        uncovered.difference_update(new)
        chosen.append(lines[rid])

        pct = 100*(TOTAL_S12 - len(uncovered))/TOTAL_S12
        if pct >= next_print or not uncovered:
            print(f"   {pct:6.2f}% coberto | SB tamanho: {len(chosen):,}")
            next_print += 1.0

    SB_FILE.write_text("\n".join(chosen), encoding="ascii")
    elapsed = round(time.perf_counter()-t0, 1)
    samples.append( (TOTAL_S15, elapsed) )
    _plot_complexity(samples)
    return len(chosen), elapsed

# ──────────────────────────── VERIFICAÇÃO ──────────────────────────────────
def verify(idx_map: Dict[int,int]) -> None:
    print("\n▶ 3/3  Verificando cobertura…")
    total = len(idx_map)
    covered = bitarray.bitarray(total) if bitarray else [False]*total
    if bitarray: covered.setall(False)

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            nums  = list(map(int,row))
            bits  = [1<<(n-1) for n in nums]
            full  = 0
            for b in bits: full |= b
            for a,b_,c in OMIT_LIST:
                m = full ^ (bits[a] | bits[b_] | bits[c])
                covered[idx_map[m]] = True

    ok = covered.all() if bitarray else (False not in covered)
    if not ok:
        sys.exit("❌ Falha: alguma S12 não coberta!")
    print("✔ Cobertura 100 % confirmada.")

# ───────────────────────────── CSV LOG ─────────────────────────────────────
def log_csv(size_:int, secs:float, peak:float)->None:
    hdr = ["SB_size","Lower_bound","Approx_factor",
           "ln|U|+1","Alpha_over_ln",
           "Tempo (s)","Pico_RAM(MB)"]
    alpha = round(size_/LOWER_BOUND,4)
    row = {
        "SB_size": size_,
        "Lower_bound": LOWER_BOUND,
        "Approx_factor": alpha,
        "ln|U|+1": round(LN_BOUND,3),
        "Alpha_over_ln": round(alpha/LN_BOUND,3),
        "Tempo (s)": secs,
        "Pico_RAM(MB)": peak
    }
    first = not LOG_CSV.exists()
    with LOG_CSV.open("a",newline="",encoding="utf8") as f:
        w = csv.DictWriter(f,fieldnames=hdr)
        if first: w.writeheader()
        w.writerow(row)
    print("📄 Log salvo em", LOG_CSV)

# ───────────────────────── GERAÇÃO DO GRÁFICO ──────────────────────────────
def _plot_complexity(samples: List[Tuple[int,float]])->None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        print("⚠ matplotlib não disponível — gráfico omitido.")
        return

    ns, ts = zip(*samples)
    c = ts[-1] / (ns[-1]*log(ns[-1]))
    theo = [c*n*log(n) for n in ns]

    plt.figure(figsize=(6,4))
    plt.plot(ns, ts, "o-", label="Tempo real")
    plt.plot(ns, theo, "--", label="c · n·log n")
    plt.title("Programa 4 — evidência O(n log n)")
    plt.xlabel("n  (linhas S15 processadas)")
    plt.ylabel("Tempo acumulado (s)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_PNG, dpi=120)
    plt.close()
    print(f"🖼  Gráfico salvo em {PLOT_PNG}")

# ───────────────────────────── CLI / MAIN ──────────────────────────────────
def parse_args()->argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 4 — encontra SB15_12")
    p.add_argument("--stream", action="store_true",
                   help="usa menos RAM (recalcula ids on-the-fly)")
    return p.parse_args()

def main()->None:
    for f in (S12_FILE, S15_FILE):
        if not f.exists():
            sys.exit(f"❌ {f} não encontrado. Execute bench.py primeiro.")

    args  = parse_args()
    proc  = psutil.Process(os.getpid())

    sb_size, secs = greedy(store_all=not args.stream)
    peak = round(proc.memory_info().peak_wset/1_048_576,1) if os.name=="nt" \
           else round(proc.memory_info().rss/1_048_576,1)

    idx_map,_ = load_S12()
    verify(idx_map)
    log_csv(sb_size, secs, peak)

    print(f"\n✅ SB15_12.csv gerado ({sb_size:,} linhas) em {secs}s — "
          f"α={sb_size/LOWER_BOUND:.3f}; pico RAM {peak} MB.")

if __name__ == "__main__":
    main()
