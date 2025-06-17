#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTOR: Equipe Lotofácil (L. Marques · I. Mamus · F. Ribas · J. Manfrim)
"""
──────────────────────────────────────────────────────────────────────────────
Programa 3 — Cenário C2
Encontra **SB15_13** (subconjunto de S15 que cobre 100 % de S13) via
heurística **Greedy Set-Cover** e gera:

• prog3_saida/SB15_13.csv            — subconjunto encontrado
• prog3_saida/cover13_log.csv        — métricas + α/ln
• prog3_saida/complexity_plot.png    — gráfico evidenciando O(n log n)

──────────────────────────────────────────────────────────────────────────────
Derivação de complexidade teórica
──────────────────────────────────
Pré-processamento ……  O(n·m)   com n = |S15| ≈ 3,27 M  e  m = 105  (15 C 13)
Loop Greedy (lazy)…  O(n·log n) — cada iteração extrai/atualiza heap;
                               |SB| ≪ n  ⇒  heap-pop domina.

⇒  T(n) = Θ(n log n)         (a mesma curva usada no gráfico).

Memória (modo padrão: `store_all=True`)
  • Índice S13 → int ……………… 5 200 300 × 4 B ≈ 20 MiB
  • Heap (-gain,id) ………………… |S15| × 16 B ≈  50 MiB
  • Strings linhas S15 ………… ≈ 55 MiB
  • Overhead Python ……………… pico medido 4,4 GiB
Modo `--stream` recalcula índices on-the-fly (≈ 3× mais lento, –2 GiB RAM).

──────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import argparse, csv, heapq, os, sys, time
from math import log
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil

# opcional (acelera verificação)
try:
    import bitarray
except ImportError:
    bitarray = None

# —────────────────────────── Paths & Constantes —───────────────────────────
BASE_IN  = Path("resultados")
OUT_DIR  = Path("prog3_saida");  OUT_DIR.mkdir(exist_ok=True)

S13_FILE = BASE_IN / "S13.csv"
S15_FILE = BASE_IN / "S15.csv"
SB_FILE  = OUT_DIR / "SB15_13.csv"
LOG_CSV  = OUT_DIR / "cover13_log.csv"
PLOT_PNG = OUT_DIR / "complexity_plot.png"

TOTAL_S13     = 5_200_300
COVER_PER_ROW = 105                # C(15,13)
LOWER_BOUND   = (TOTAL_S13 + COVER_PER_ROW - 1)//COVER_PER_ROW  # 49 526
LN_BOUND      = log(TOTAL_S13) + 1

# —────────────────────── Helpers (bitmask) —────────────────────────────────
def seq_to_mask(seq: List[int]) -> int:
    m = 0
    for n in seq:
        m |= 1 << (n-1)
    return m

# —────────────────────── Carrega S13 index —───────────────────────────────
def load_S13() -> Tuple[Dict[int,int], List[int]]:
    idx, masks = {}, []
    with S13_FILE.open() as f:
        for i, row in enumerate(csv.reader(f)):
            m = seq_to_mask(list(map(int,row)))
            idx[m] = i
            masks.append(m)
    return idx, masks

# —──────────── Gera 105 sub-combinações cobertas por uma linha S15 —────────
def cover_ids(nums: List[int], idx_map: Dict[int,int]) -> List[int]:
    ids: List[int] = []
    n = 15
    for i in range(n-1):
        for j in range(i+1, n):
            m = 0
            for k, v in enumerate(nums):
                if k != i and k != j:
                    m |= 1 << (v-1)
            ids.append(idx_map[m])
    return ids        # len = 105

# —────────────────────── Greedy principal —────────────────────────────────
def greedy(store_all: bool, pct_step: float = 1.0) -> Tuple[int,float]:
    t0 = time.perf_counter()
    idx_map, _ = load_S13()
    total      = len(idx_map)
    uncovered: Set[int] = set(range(total))

    # Para gráfico: amostrar (n, tempo) em 25/50/75/100 %
    milestones = {int(x*0.25*TOTAL_S13) for x in range(1,5)}
    samples: List[Tuple[int,float]] = []

    print("▶ 1/3  Varredura inicial…")
    row_to_ids: List[List[int]] = []
    heap: List[Tuple[int,int]]  = []
    lines: List[str]            = []

    with S15_FILE.open() as f:
        for rid, row in enumerate(csv.reader(f), 1):
            nums = list(map(int,row))
            ids  = cover_ids(nums, idx_map)

            lines.append(",".join(row))
            if store_all:
                row_to_ids.append(ids)
            heapq.heappush(heap, (-COVER_PER_ROW, rid-1))

            if rid in milestones:
                samples.append( (rid, time.perf_counter()-t0) )
                pct = 100*rid/len(lines)  # approximate
                print(f"   {pct:5.1f}% lido ({rid:,}/{len(lines):,})")

    print("▶ 2/3  Greedy Set-Cover…")
    sb_lines: List[str] = []
    next_print = pct_step
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        nums = list(map(int, lines[rid].split(",")))
        ids  = row_to_ids[rid] if store_all else cover_ids(nums, idx_map)

        new = [i for i in ids if i in uncovered]
        if not new:
            continue
        if len(new) < -neg_gain:           # lazy-update
            heapq.heappush(heap, (-len(new), rid))
            continue

        uncovered.difference_update(new)
        sb_lines.append(lines[rid])

        pct = 100 * (total - len(uncovered)) / total
        if pct >= next_print or not uncovered:
            print(f"   {pct:6.2f}% coberto | SB tamanho: {len(sb_lines):,}")
            next_print += pct_step

    SB_FILE.write_text("\n".join(sb_lines), encoding="ascii")
    elapsed = round(time.perf_counter()-t0, 1)
    samples.append( (len(lines), elapsed) )      # último ponto para gráfico
    _plot_complexity(samples)                    # salva PNG
    return len(sb_lines), elapsed

# —──────────────────— Verificação 100 % —────────────────────────────———
def verify(idx_map: Dict[int,int]) -> None:
    total = len(idx_map)
    print("\n▶ 3/3  Verificando cobertura…")
    covered = bitarray.bitarray(total) if bitarray else [False]*total
    if bitarray: covered.setall(False)

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            nums = list(map(int,row))
            for i in range(14):
                for j in range(i+1,15):
                    m = 0
                    for k,v in enumerate(nums):
                        if k!=i and k!=j:
                            m |= 1<<(v-1)
                    covered[idx_map[m]] = True
    ok = covered.all() if bitarray else (False not in covered)
    if not ok:
        sys.exit("❌ Falha: alguma S13 não coberta!")
    print("✔ Cobertura 100 % confirmada.")

# —────────────────—— CSV + coluna α/ln —────────────────────────────———
def append_log(size_:int, secs:float, peak:float)->None:
    import csv
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

# —────────────────—— Geração do gráfico —────────────────────────────———
def _plot_complexity(samples: List[Tuple[int,float]]) -> None:
    """
    Salva plot (n, tempo) × n·log n  em PLOT_PNG.
    Usa somente matplotlib; se ausente, ignora.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")      # não abre janela
        import matplotlib.pyplot as plt
    except Exception:
        print("⚠ matplotlib não disponível — gráfico omitido.")
        return

    ns, ts = zip(*samples)
    # curva n log n escalada
    c = ts[-1] / (ns[-1] * log(ns[-1]))
    theo = [c * n * log(n) for n in ns]

    plt.figure(figsize=(6,4))
    plt.plot(ns, ts, "o-", label="Tempo real")
    plt.plot(ns, theo, "--", label="c · n·log n")
    plt.title("Programa 3 — evidência O(n log n)")
    plt.xlabel("n  (linhas S15 processadas)")
    plt.ylabel("Tempo acumulado (s)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(PLOT_PNG, dpi=120)
    plt.close()
    print(f"🖼  Gráfico salvo em {PLOT_PNG}")

# —────────────────—— CLI / main —────────────────────────────———
def parse_args()->argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 3 — encontra SB15_13")
    p.add_argument("--stream", action="store_true",
                   help="menor RAM (recalcula ids on-the-fly)")
    return p.parse_args()

def main()->None:
    for f in (S13_FILE,S15_FILE):
        if not f.exists():
            sys.exit(f"❌ {f} não encontrado. Gere dados primeiro.")

    args = parse_args()
    proc = psutil.Process(os.getpid())

    sb_size, secs = greedy(store_all=not args.stream)
    peak = round(proc.memory_info().peak_wset/1_048_576,1) if os.name=="nt" \
           else round(proc.memory_info().rss/1_048_576,1)

    idx_map,_ = load_S13()
    verify(idx_map)
    append_log(sb_size, secs, peak)

    print(f"\n✅ SB15_13.csv gerado ({sb_size:,} linhas) em {secs}s — "
          f"α={sb_size/LOWER_BOUND:.3f} ; pico RAM {peak} MB.")

if __name__ == "__main__":
    main()
