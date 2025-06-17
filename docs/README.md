# Projeto **Lotofácil — Algoritmos & Complexidade**

Repositório acadêmico que demonstra, passo a passo, como

1. **Gerar** todas as combinações possíveis da Lotofácil (25 números).
2. **Reduzir** drasticamente o número de cartões necessários usando a heurística **Greedy Set‑Cover**.

> **Status** — 16 / 06 / 2025 · Programas 1 – 5 concluídos

---

## 🚦 Fluxo em 5 passos

| 🔢 | O que fazer                   | Comando‑chave         | Saída principal                 |
| -- | ----------------------------- | --------------------- | ------------------------------- |
| 1  | **Gerar** S15…S11 + benchmark | `python bench.py`     | `resultados/*.csv`, `bench.csv` |
| 2  | **SB15‑14** (cobre S14)       | `python programa2.py` | `prog2_saida/SB15_14.csv`       |
| 3  | **SB15‑13** (cobre S13)       | `python programa3.py` | `prog3_saida/SB15_13.csv`       |
| 4  | **SB15‑12** (cobre S12)       | `python programa4.py` | `prog4_saida/SB15_12.csv`       |
| 5  | **SB15‑11** (cobre S11)       | `python programa5.py` | `prog5_saida/SB15_11.csv`       |

```bash
python verify_all.py          # verifica 100 % de cobertura (k = 14…11)
python calcular_custo_sb.py   # gera prog7_saida/resultados_custo_jogadas.csv
python package.py             # cria lotofacil_submission.zip para entrega
```

---

## 🌐 Visão rápida

| #          | Cenário / Objetivo               | Script                    | Pasta de saída | Artefato‑chave / Observação      |
| ---------- | -------------------------------- | ------------------------- | -------------- | -------------------------------- |
| PROGRAMA 1 | Gerar S15…S11 + benchmark        | `bench.py` + `lotogen.py` | `resultados/`  | `S15.csv … S11.csv`, `bench.csv` |
| PROGRAMA 2 | Cobrir **100 % S14** com SB15‑14 | `programa2.py`            | `prog2_saida/` | `SB15_14.csv`                    |
| PROGRAMA 3 | Cobrir **100 % S13** com SB15‑13 | `programa3.py`            | `prog3_saida/` | `SB15_13.csv`                    |
| PROGRAMA 4 | Cobrir **100 % S12** com SB15‑12 | `programa4.py`            | `prog4_saida/` | `SB15_12.csv`                    |
| PROGRAMA 5 | Cobrir **100 % S11** com SB15‑11 | `programa5.py`            | `prog5_saida/` | `SB15_11.csv`                    |
| EXTRA      | **Verificar** cobertura 14…11    | `verify_all.py`           | —              | Saída apenas no terminal         |
| PROGRAMA 7 | **Calcular custo** (R\$)         | `calcular_custo_sb.py`    | `prog7_saida/` | `resultados_custo_jogadas.csv`   |
| EXTRA      | **Empacotar** p/ submissão       | `package.py`              | raiz           | `lotofacil_submission.zip`       |

> Cada script grava **log CSV** com tempo, pico de RAM e fator α; consulte `*_log.csv` nas pastas.

---

## ⚙️ Instalação

```bash
git clone https://github.com/usuario/lotofacil_project.git
cd lotofacil_project
pip install psutil bitarray   # bitarray é opcional, apenas acelera verificação
```

*Requer Python ≥ 3.8 (testado em 3.11).*

---

## 🚀 Passo 1 — Gerar tabelas S15 … S11

```bash
python bench.py               # gera tudo + bench.csv
```

`bench.py` limpa a pasta `resultados/` quando roda sem argumentos.

---

## 🚀 Passo 2 — SB15‑14 (Programa 2)

```bash
python programa2.py            # cria prog2_saida/SB15_14.csv
```

≈ 3 min / 2.2 GB RAM.

---

## 🚀 Passo 3 — SB15‑13 (Programa 3)

```bash
python programa3.py            # cria prog3_saida/SB15_13.csv
```

≈ 25 min / 4.4 GB RAM.

---

## 🚀 Passo 4 — SB15‑12 (Programa 4)

```bash
python programa4.py            # cria prog4_saida/SB15_12.csv
python programa4.py --stream   # RAM ≤ 3 GB (≈ 20 % mais lento)
```

≈ 1 h 13 min / 12.8 GB RAM.

---

## 🚀 Passo 5 — SB15‑11 (Programa 5)

```bash
python programa5.py            # ~6–8 min / 3 GB RAM
python programa5.py --stream   # RAM ≤ 700 MB, +20 % tempo
```

---

## 🧐 Como interpretar os logs CSV

```
SB_size,Lower_bound,Approx_factor,Tempo (s),Pico_RAM(MB)
38100,11430,3.3333,4384.6,12810.3   # exemplo SB15‑12
```

- **SB\_size** — linhas no subconjunto
- **Lower\_bound** — ⌈|Sₖ| / C(15,k)⌉
- **Approx\_factor** α = SB\_size / Lower\_bound

---

## 📊 Benchmarks consolidados (16 jun 2025)

| SB      | |SB|    | α      | Tempo       | Pico RAM |
| ------- | ------- | ------ | ----------- | -------- |
| SB15‑14 | 532 555 | 1.79   | 188 s       | 2.2 GB   |
| SB15‑13 | 128 827 | 2.60   | 1 494 s     | 4.4 GB   |
| SB15‑12 | 38 100  | 3.33   | 4 384 s     | 12.8 GB  |
| SB15‑11 | 12 733  | 3.89   | 26 597 s    | 12.9 GB  |

---

## 💸 Custo financeiro (R\$ 3,00 por cartão)

```
SB15_14     | 532.555 | R$ 1.597.665   | 
SB15_13     | 128.827 | R$  386.481    | 
SB15_12     |  38.100 | R$  114.300    | 
SB15_11     |  12.733 | R$   38.199    | 
```

Gerado por `calcular_custo_sb.py`.

---

## 👥 Créditos

| Autor            | Funções principais               |
| ---------------- | -------------------------------- |
| Leonardo Marques | Greedy (P2,P5), README, Makefile |
| Igor Mamus       | Gerador + benchmark (P1)         |
| Felipe Ribas     | Greedy SB15‑13 (P3)              |
| João Manfrim     | Verificadores & logs             |

---

Contribuições via *issues* ou *pull‑requests* são bem‑vindas.

