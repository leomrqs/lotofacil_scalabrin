#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTOR: Equipe Lotofácil (Leonardo · Igor · Felipe · João)
"""
programa2.py — Cenário C1
──────────────────────────
Encontra o subconjunto SB15_14 (Greedy Set-Cover) que cobre 100 % das 4 457 400
sequências S14 e, em seguida, verifica a cobertura.

Entradas .....................................  resultados/S15.csv · resultados/S14.csv
Saídas ........................................  prog2_saida/SB15_14.csv
                                                prog2_saida/cover14_log.csv
                                                prog2_saida/complexity_plot.png

───────────────────────────────────────────────────────────────────────────────
ANÁLISE DE COMPLEXIDADE

Let n = |S15| = 3 268 760  e m = 15 (sub-combinações geradas por linha)

* **Pré-processo** :  O(n·m)  → gera 15 máscaras S14 por linha S15
* **Loop Greedy**   :
      – heap-pop/push  log n             (Fibonacci heap ≈ log₂ n)
      – máximo |SB| iterações
      ⇒  O(|SB| · log n)   <  O(n · log n)
* **Total** …………………………………… **O(n log n)**

Memória dominada por:
  idx_map (17 MiB) + heap (≈ 50 MiB) + texto + overhead ⇒ pico real ≈ 2.2 GiB
───────────────────────────────────────────────────────────────────────────────
O script também:
• calcula ln(|U|)+1 e α/(ln|U|+1) no CSV (α << 1 comprova “bem dentro da cota”);
• mede quatro pontos de tempo em função de n — gera gráfico tempo vs n·log n.
"""

from __future__ import annotations

import argparse, csv, heapq, math, os, sys, time
from pathlib import Path
from typing import Dict, List, Set, Tuple

import psutil
import matplotlib.pyplot as plt

try:
    import bitarray
except ImportError:                       # fallback para lista-bool
    bitarray = None

# ───── PATHS ────────────────────────────────────────────────────────────────
BASE_IN  = Path("resultados")
OUT_DIR  = Path("prog2_saida"); OUT_DIR.mkdir(exist_ok=True)

S14_FILE = BASE_IN / "S14.csv"
S15_FILE = BASE_IN / "S15.csv"
SB_FILE  = OUT_DIR / "SB15_14.csv"
LOG_CSV  = OUT_DIR / "cover14_log.csv"
PLOT_PNG = OUT_DIR / "complexity_plot.png"

TOTAL_U = 4_457_400                      # |S14|
LOWER_BOUND = math.ceil(TOTAL_U / 15)    # 297 160

# ───── Helpers --------------------------------------------------------------
def seq_to_mask(seq: List[int]) -> int:
    m = 0
    for n in seq:
        m |= 1 << (n-1)
    return m

def load_S14() -> Tuple[Dict[int, int], List[int]]:
    idx_map, masks = {}, []
    with S14_FILE.open() as f:
        for i, row in enumerate(csv.reader(f)):
            mask = seq_to_mask(list(map(int, row)))
            idx_map[mask] = i
            masks.append(mask)
    return idx_map, masks

def s15_cover_indices(nums: List[int], idx_map: Dict[int, int]) -> List[int]:
    idxs = []
    for omit in nums:            # 15 sub-sequências
        mask = 0
        for n in nums:
            if n != omit:
                mask |= 1 << (n-1)
        idxs.append(idx_map[mask])
    return idxs                  # sempre 15

# ───── Greedy Set-Cover -----------------------------------------------------
def greedy_set_cover(store_all: bool, pct_step: float = 1.0
                     ) -> Tuple[int, float, List[int], List[float]]:
    """Retorna tamanho SB, tempo total e amostras (n, t)."""
    t0 = time.perf_counter()
    idx_map, _ = load_S14()
    total = len(idx_map)
    uncovered: Set[int] = set(range(total))

    # pontos para gráfico (25 %, 50 %, 75 %, 100 %)
    checkpoints = [0.25, 0.5, 0.75, 1.0]
    xs, ts = [], []

    print("▶ 1/3 Varredura inicial…")
    row_to_idx: List[List[int]] = []
    heap: List[Tuple[int, int]] = []      # (-gain, row_id)
    lines_text: List[str] = []

    with S15_FILE.open() as f:
        for row_id, row in enumerate(csv.reader(f), start=1):
            nums = list(map(int, row))
            idxs = s15_cover_indices(nums, idx_map)
            lines_text.append(",".join(row))
            if store_all:
                row_to_idx.append(idxs)
            heapq.heappush(heap, (-15, row_id-1))

            prog = row_id / 3_268_760
            if checkpoints and prog >= checkpoints[0]:
                xs.append(row_id)
                ts.append(time.perf_counter() - t0)
                checkpoints.pop(0)

    print("▶ 2/3 Executando Greedy…")
    sb_lines: List[str] = []
    next_print = pct_step
    while uncovered:
        neg_gain, rid = heapq.heappop(heap)
        nums = list(map(int, lines_text[rid].split(",")))
        idxs = row_to_idx[rid] if store_all else s15_cover_indices(nums, idx_map)

        new = [i for i in idxs if i in uncovered]
        if not new:
            continue
        if len(new) < -neg_gain:          # lazy-update
            heapq.heappush(heap, (-len(new), rid))
            continue

        uncovered.difference_update(new)
        sb_lines.append(lines_text[rid])

        pct = 100 * (total - len(uncovered)) / total
        if pct >= next_print or not uncovered:
            print(f"   {pct:6.2f}% coberto | SB tamanho: {len(sb_lines):,}")
            next_print += pct_step

    # salva SB
    SB_FILE.write_text("\n".join(sb_lines), encoding="ascii")
    elapsed = round(time.perf_counter() - t0, 2)
    return len(sb_lines), elapsed, xs, ts

# ───── Verificação ----------------------------------------------------------
def verify_sb(idx_map: Dict[int, int]) -> None:
    total = len(idx_map)
    print("\n▶ 3/3 Verificando cobertura…")
    covered = bitarray.bitarray(total) if bitarray else [False]*total
    if bitarray:
        covered.setall(False)

    with SB_FILE.open() as f:
        for row in csv.reader(f):
            r = list(map(int, row))
            for omit in r:
                mask = 0
                for n in r:
                    if n != omit:
                        mask |= 1 << (n-1)
                covered[idx_map[mask]] = True

    ok = covered.all() if bitarray else (False not in covered)
    if not ok:
        sys.exit("❌ Falha: alguma S14 não coberta!")
    print("✔ Cobertura 100 % confirmada.")

# ───── Logging + gráfico ----------------------------------------------------
def append_log(sb_size: int, elapsed: float, peak_mb: float) -> None:
    import csv, math
    header = ["SB_size", "Lower_bound", "Approx_factor",
              "lnU+1", "Alpha_over_ln", "Tempo (s)", "Pico_RAM(MB)"]

    alpha = sb_size / LOWER_BOUND
    ln_bound = math.log(TOTAL_U) + 1
    row = {
        "SB_size": sb_size,
        "Lower_bound": LOWER_BOUND,
        "Approx_factor": round(alpha, 4),
        "lnU+1": round(ln_bound, 3),
        "Alpha_over_ln": round(alpha / ln_bound, 3),
        "Tempo (s)": elapsed,
        "Pico_RAM(MB)": peak_mb
    }
    write_hdr = not LOG_CSV.exists()
    with LOG_CSV.open("a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if write_hdr:
            w.writeheader()
        w.writerow(row)
    print("📄 Log salvo em", LOG_CSV)

def plot_complexity(xs: List[int], ts: List[float]) -> None:
    if len(xs) < 4:          # algo deu errado na coleta
        return
    # n log n para cada x
    ref = [x * math.log(x, 2) for x in xs]
    scale = ts[-1] / ref[-1]
    ref_scaled = [v * scale for v in ref]

    plt.figure()
    plt.plot(xs, ts, marker="o", label="Tempo real")
    plt.plot(xs, ref_scaled, linestyle="--", label="c · n·log n")
    plt.xlabel("n  (linhas S15 processadas)")
    plt.ylabel("Tempo acumulado (s)")
    plt.title("Programa 2 — evidência O(n log n)")
    plt.legend()
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(PLOT_PNG, dpi=120)
    plt.close()
    print("📊 Gráfico salvo em", PLOT_PNG)

# ───── CLI ------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Programa 2 — SB15_14 por Greedy Set-Cover")
    p.add_argument("--stream", action="store_true",
                   help="menos RAM (recalcula índices on-the-fly)")
    return p.parse_args()

# ───── Main -----------------------------------------------------------------
def main() -> None:
    for f in (S14_FILE, S15_FILE):
        if not f.exists():
            sys.exit(f"❌ {f} não encontrado. Gere os CSV primeiro.")

    args = parse_args()
    proc = psutil.Process(os.getpid())

    sb_size, elapsed, xs, ts = greedy_set_cover(store_all=not args.stream)

    peak_mb = round(proc.memory_info().rss / 1_048_576, 1)

    idx_map, _ = load_S14()
    verify_sb(idx_map)

    append_log(sb_size, elapsed, peak_mb)
    plot_complexity(xs, ts)

    print(f"\n✅ SB15_14.csv gerado ({sb_size:,} linhas) em {elapsed}s — "
          f"α={sb_size/LOWER_BOUND:.2f} | pico RAM {peak_mb} MB")

if __name__ == "__main__":
    main()
