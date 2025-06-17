#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# AUTOR: 
"""
calcular_custo_sb.py  –  Calcula custo financeiro e gera relatório CSV.

• Para cada SB15_k (k = 14,13,12,11) conta linhas, multiplica por R$ 3,00
  e registra situação de verificação (arquivo presente / ausente).
• Salva tabela consolidada em  `resultados/custo_sb.csv`  (cria pasta
  se ainda não existir) **e** imprime visão amigável no terminal.
• Saída CSV facilita anexar ao REPORT ou importar em Excel.

Uso:
    python calcular_custo_sb.py
"""
from pathlib import Path
import csv, sys

CARD_PRICE = 3.00
RESULT_DIR = Path("prog7_saida")
CSV_OUT    = RESULT_DIR / "resultado_custo_sb.csv"

SB_PATHS = {
    "SB15_14": Path("prog2_saida/SB15_14.csv"),
    "SB15_13": Path("prog3_saida/SB15_13.csv"),
    "SB15_12": Path("prog4_saida/SB15_12.csv"),
    "SB15_11": Path("prog5_saida/SB15_11.csv"),
}

def main() -> None:
    rows = []
    print("Subconjunto | Linhas | Custo (R$) | Status")

    for label, path in SB_PATHS.items():
        if not path.exists():
            print(f"{label:<11} |    —    |    —      | arquivo ausente")
            rows.append({"SB": label, "Linhas": "-", "Custo_R$": "-", "Status": "MISSING"})
            continue

        # conta linhas rapidamente lendo em modo binário
        with path.open("rb") as f:
            n_lines = sum(1 for _ in f)
        cost = n_lines * CARD_PRICE

        print(f"{label:<11} | {n_lines:>7,} | R$ {cost:>11,.2f} | ok".replace(",","."))
        rows.append({
            "SB": label,
            "Linhas": n_lines,
            "Custo_R$": f"{cost:.2f}",
            "Status": "OK"
        })

    # ------------- grava CSV -------------
    RESULT_DIR.mkdir(exist_ok=True)
    with CSV_OUT.open("w", newline="", encoding="utf8") as fcsv:
        writer = csv.DictWriter(fcsv, fieldnames=["SB", "Linhas", "Custo_R$", "Status"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n📄 Arquivo de custo salvo em {CSV_OUT}\n")

if __name__ == "__main__":
    main()
