#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""lotogen.py — gerador de combinações Lotofácil.

Suporta saída em:
    • texto separado por espaço (.txt)
    • CSV separado por vírgula (.csv)

Exemplos:
    python lotogen.py 15 --csv -o ./resultados
    python lotogen.py --all --csv
"""
from __future__ import annotations
import argparse, math, sys, csv
from itertools import combinations
from pathlib import Path
from time import perf_counter
from typing import Iterable, Sequence, TextIO, List

TOTAL_NUMBERS = 25
DEFAULT_KS = [15, 14, 13, 12, 11]
PROGRESS_STEP = 100_000

def nchoosek(k: int) -> int:
    return math.comb(TOTAL_NUMBERS, k)

def generate_combinations(k: int) -> Iterable[Sequence[int]]:
    return combinations(range(1, TOTAL_NUMBERS + 1), k)

def open_sink(path: Path, csv_mode: bool) -> TextIO:
    if csv_mode:
        return open(path, 'w', newline='', encoding='ascii')
    return open(path, 'w', buffering=1, encoding='ascii')

def human_int(n: int) -> str:
    return f'{n:,}'.replace(',', ' ')

def progress_msg(k: int, cur: int, total: int) -> None:
    pct = cur * 100 / total
    print(f'\r[S{k}] {human_int(cur)}/{human_int(total)} ({pct:5.1f} %)', end='', file=sys.stderr)
    if cur == total:
        print(file=sys.stderr)

def write_table(k: int, out_dir: Path, csv_mode: bool, step: int=PROGRESS_STEP) -> None:
    total = nchoosek(k)
    filename = f'S{k}.{"csv" if csv_mode else "txt"}'
    target = out_dir / filename
    target.parent.mkdir(parents=True, exist_ok=True)

    print(f'▶️  S{k}: {human_int(total)} comb → {target}')
    start = perf_counter()
    written = 0
    with open_sink(target, csv_mode) as fh:
        if csv_mode:
            writer = csv.writer(fh)
        for written, combo in enumerate(generate_combinations(k), start=1):
            if csv_mode:
                writer.writerow(combo)
            else:
                fh.write(" ".join(map(str, combo)) + "\n")
            if written % step == 0 or written == total:
                progress_msg(k, written, total)
    elapsed = perf_counter() - start
    if written != total:
        raise RuntimeError(f'Validação falhou S{k}: {written} ≠ {total}')
    size_mb = target.stat().st_size / (1024 * 1024)
    print(f'✅  S{k} | {human_int(written)} linhas | {size_mb:.1f} MB | {elapsed:.2f} s\n')

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description='Gerador de combinações Lotofácil')
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument('ks', metavar='K', type=int, nargs='*', help='valores de k (ex.: 15 13)')
    group.add_argument('--all', action='store_true', help='gera S15…S11')
    ap.add_argument('--csv', action='store_true', help='salvar como .csv')
    ap.add_argument('-o', '--outdir', default='.', help='diretório de saída')
    ap.add_argument('--step', type=int, default=PROGRESS_STEP, help='linhas por update')
    return ap.parse_args()

def main() -> None:
    args = parse_args()
    ks: List[int] = DEFAULT_KS if args.all else args.ks
    if not ks:
        print('Nenhum K informado', file=sys.stderr)
        sys.exit(1)
    out_dir = Path(args.outdir).expanduser().resolve()
    for k in ks:
        if not 1 <= k <= TOTAL_NUMBERS:
            print(f'⚠️  ignorando K={k}', file=sys.stderr)
            continue
        write_table(k, out_dir, csv_mode=args.csv, step=args.step)

if __name__ == '__main__':
    main()
