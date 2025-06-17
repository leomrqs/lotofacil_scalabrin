#!/usr/bin/env python3
# AUTOR: Leonardo dos Santos Marques
# verify_all.py – Valida SB15_k (k = 14…11) em lote
#
# Uso:  python verify_all.py
#
# Requer diretórios/nomes padrão gerados pelos nossos scripts:
#   resultados/Sk.csv          (k = 14, 13, 12, 11)
#   progN_saida/SB15_k.csv     (N = 2, 3, 4, 5)
#
# Dependências: psutil (opcional) | bitarray (opcional – mais rápido)

from pathlib import Path
from itertools import combinations
import csv, sys, time

try:
    import bitarray
except ImportError:
    bitarray = None

BASE_IN = Path("resultados")
SB_DIRS = {
    14: Path("prog2_saida"),
    13: Path("prog3_saida"),
    12: Path("prog4_saida"),
    11: Path("prog5_saida"),
}

SUB_PER_LINE = {           # C(15,k)
    14: 15,
    13: 105,
    12: 455,
    11: 1_365,
}

def seq_to_mask(seq):
    m = 0
    for v in seq:
        m |= 1 << (v - 1)
    return m

def verify_k(k):
    sk_file = BASE_IN / f"S{k}.csv"
    sb_file = SB_DIRS[k] / f"SB15_{k}.csv"

    if not sk_file.exists():
        sys.exit(f"❌ Faltando {sk_file}  — execute bench.py para criar S{k}.csv.")
    if not sb_file.exists():
        sys.exit(f"❌ Faltando {sb_file}  — execute programa correspondente para gerar SB15_{k}.csv.")

    print(f"\n▶ Verificando k = {k}  (SB15_{k} cobre S{k})")
    t0 = time.perf_counter()

    # 1) índice S_k → id
    idx = {}
    with sk_file.open() as f:
        for i, row in enumerate(csv.reader(f)):
            idx[seq_to_mask(map(int, row))] = i
    total = len(idx)

    # 2) vetor de cobertura
    covered = bitarray.bitarray(total) if bitarray else [False] * total
    if bitarray:
        covered.setall(False)

    omit = list(combinations(range(15), 15 - k))  # tuplas a omitir
    print(f"   • S{k}: {total:,} seqs  ·  cada S15 cobre {SUB_PER_LINE[k]} delas")

    with sb_file.open() as f:
        for row in csv.reader(f):
            nums = list(map(int, row))
            bits = [1 << (n - 1) for n in nums]
            full = sum(bits)
            for o in omit:
                m = full
                for i in o:                     # remove 15-k bits
                    m ^= bits[i]
                covered[idx[m]] = True

    ok = covered.all() if bitarray else (False not in covered)
    elapsed = time.perf_counter() - t0
    if ok:
        print(f"   ✔ Cobertura 100 % confirmada em {elapsed:.1f}s")
    else:
        missing = (covered.count(False) if bitarray else covered.count(False))
        sys.exit(f"❌ Falha: {missing} sequências S{k} não cobertas.")

def main():
    print("=== Verificação em lote SB15_k ===")
    for k in (14, 13, 12, 11):
        verify_k(k)
    print("\n✅ Todos os quatro cenários estão corretos.")

if __name__ == "__main__":
    main()
