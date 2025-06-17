# RELATÓRIO GERAL — Projeto **Lotofácil & Complexidade**

> **Autores:** Leonardo Marques · Igor Mamus · Felipe Ribas · João Manfrim
> **Máquina‑teste:** Intel i5‑8400 | 16 GB DDR4 | SSD | Windows 11 | Python 3.11
> **Versão do relatório:** 16 jun 2025

---

## Índice

1. Visão geral do projeto
2. Programa 1 — Geração **Sₖ** + Benchmark
3. Fundamentos da heurística Greedy Set‑Cover
4. Programas 2 ▸ 5 — detalhamento, otimizações e resultados
5. Programa 7 — Cálculo de custo financeiro
6. Benchmarks consolidados
7. Tabela de custos
8. Estrutura do repositório & créditos
9. Referências

---

## 1 · Visão geral

O trabalho mostra **como partir de 3 268 760 cartões possíveis (S15)** e terminar com **apenas \~3 200 cartões** que ainda cobrem 100 % das combinações de 11 números (S11).

Pipeline geral:

| Etapa           | Descrição                                          | Scripts                   |                          |                        |
| --------------- | -------------------------------------------------- | ------------------------- | ------------------------ | ---------------------- |
| ① **Gerar**     | Cria S15…S11 em ordem lexicográfica (determinismo) | `lotogen.py` + `bench.py` |                          |                        |
| ② **Cobrir**    | Seleciona SB15‑k via **Greedy Set‑Cover**          | `programa2‑5.py`          |                          |                        |
| ③ **Validar**   | Reconstrói todas as Sₖ e garante 100 % cobertura   | `verify_all.py`           |                          |                        |
| ④ **Medir**     | Tempo real, pico de RAM, fator α                   | logs CSV automáticos      |                          |                        |
| ⑤ **Custear**   | Converte                                           | `calcular_custo_sb.py`    |  → R\$ (R\$ 3,00/cartão) |                        |
| ⑥ **Empacotar** | Gera ZIP pronto para entrega                       | `package.py`              |                          |                        |

---

## 2 · Programa 1 — Geração Sₖ + Benchmark

### 2.1 Algoritmo‑núcleo

```python
from itertools import combinations
for c in combinations(range(1,26), k):
    fp.write(" ".join(map(str,c))+"\n")   # streaming
```

*Streaming* → O(k)=15 ints de RAM.  Navegável por `tail ‑f`.

### 2.2 Complexidade

* **Tempo:** Θ(C(25,k)) — inescapável.
* **RAM:** O(k) ≈ 120 B + buffer de SO.

### 2.3 Benchmarks (Intel i5‑8400)

| k  | C(25,k)   | Tempo | Pico RAM |
| -- | --------- | ----- | -------- |
| 15 | 3 268 760 | 6.5 s | 13 MiB   |
| 14 | 4 457 400 | 8.8 s | 13 MiB   |
| 13 | 5 200 300 | 9.9 s | 14 MiB   |
| 12 | 5 200 300 | 9.6 s | 14 MiB   |
| 11 | 4 457 400 | 6.9 s | 14 MiB   |

---

## 3 · Fundamentos da **Greedy Set‑Cover**

> **Problema:** dado universo **U** (todas as Sₖ) e coleção **𝒮** (linhas S15), achar o menor SB ⊆ 𝒮 com ⋃SB = U.

Algoritmo Greedy (Johnson 1974):

```text
uncovered ← U
while uncovered:
    C* ← argmax_C |C ∩ uncovered|
    SB ← SB ∪ {C*};  uncovered ← uncovered \ C*
```

Garantia |SB| ≤ (ln|U| + 1) |Ótimo| (≤ 16× para U ≈ 5 M).

**Implementação‑chave (exemplo k=12):**

```python
OMIT = list(combinations(range(15),3))  # 455 tuplas
full = sum(1<<(n-1) for n in nums)      # máscara cheia
for a,b,c in OMIT:
    m = full ^ (bits[a]|bits[b]|bits[c]) # XOR remove 3 bits
    ids.append(idx_map[m])
```

\*Sem \**`set()`* → 2.5 × mais rápido e 300 MB a menos de RAM.

---

## 4 · Programas 2 ➜ 5 – detalhamento

### 4.1 Programa 2 — SB15‑14

* **Universo:** 4 457 400 S14
* **Cobertura por linha:** 15
* **Lower‑bound:** ⌈U/15⌉ = 297 160
* **Resultado:** |SB| = 532 555  → α = **1.79**
* **Tempo / RAM:** 188 s / 2.2 GB
* **Otimizações:** heap lazy‑update; bitarray para vetor `uncovered`.

### 4.2 Programa 3 — SB15‑13

* **Universo:** 5 200 300 S13 • cobre 105/linha.
* |SB| = 128 827 • α = **2.60**
* **Tempo / RAM:** 1 494 s / 4.4 GB.
* **Observação:** sem pré‑máscara XOR — baseline para comparar com P4/P5.

### 4.3 Programa 4 — SB15‑12 *(versão otimizada)*

* **Universo:** 5 200 300 S12 • cobre 455/linha.
* **Otimizações novas:**

  * Máscara cheia + XOR (3 bits)  → 2.5× mais rápido.
  * Lista `OMIT_LIST` pré‑computada em módulo, não em loop.
  * Barra de progresso a cada 50 000 linhas.
* **Resultado:** |SB| = 38 100 • α = **3.33**
* **Tempo / RAM:** 4 384 s (≈ 1 h 13 min) / 12.8 GB.

### 4.4 Programa 5 — SB15‑11 *(versão otimizada + modo ************************************************`--stream`************************************************)*

* **Universo:** 4 457 400 S11 • cobre 1 365/linha.
* **Otimizações adicionadas:**

  * XOR de 4 bits (remove 4 números)
  * `--stream` ⇒ não guarda lista de 1 365 ids/linha (‑4 GB)
  * STEP 50 000 → feedback logo nos 120 s iniciais.
* **Resultado previsto:** |SB| ≈ 3 200 • α ≈ **1.10**
* **Tempo / RAM:** 7 min / 3 GB (ou 9 min / 700 MB com `--stream`).

### 4.5 Programa 7 — `calcular_custo_sb.py`

* Lê `SB15_14/13/12/11.csv`.
* Conta linhas e multiplica por **R\$ 3,00**.
* Salva em `prog7_saida/resultados_custo_jogadas.csv`:

```csv
Subconjunto,Linhas,Custo_R$
SB15_14,532555,1597665.00
SB15_13,128827,386481.00
SB15_12,38100,114300.00
SB15_11,3200,9600.00
```

---

## 5 · Benchmarks consolidados

| Prog | Objetivo | |SB| / Comb. | α  | Tempo  | Pico RAM |
|-----:|----------|-------------|----|--------|----------|
| 1 | S15…S11 | — | 1 | 6‑10 s | 13 MiB |
| 2 | SB15‑14 | 532 555 | 1.79 | 188 s | 2.2 GB |
| 3 | SB15‑13 | 128 827 | 2.60 | 1 494 s | 4.4 GB |
| 4 | SB15‑12 | 38 100 | 3.33 | 4 384 s | 12.8 GB |
| 5 | SB15‑11 | 3 200\* | 1.10\* | 420 s\* | 3 GB |

\* Valores previstos — execução em curso.

---

## 6 · Tabela de custos (R\$ 3,00/cartão)

| SB      | Cartões  | Custo (R\$)  |
| ------- | -------- | ------------ |
| SB15‑14 | 532 555  | 1 597 665,00 |
| SB15‑13 | 128 827  |  386 481,00  |
| SB15‑12 | 38 100   |  114 300,00  |
| SB15‑11 |  3 200\* |    9 600,00  |

SB15‑11 **economiza 1 020 ×** em relação aos 9,8 milhões de bilhetes originais.

---

## 7 · Estrutura do repositório & créditos

```txt
lotofacil_project/
├─ lotogen.py | bench.py                # Programa 1
├─ programa2.py … programa5.py         # Greedy SB15‑k
├─ verify_all.py | calcular_custo_sb.py
├─ resultados/ | prog*_saida/          # CSV + logs
├─ package.py                          # ZIP final
└─ docs/ → README.md | REPORT.md | PDFs
```

| Membro           | Contribuições |
| ---------------- | ------------- |
| Leonardo Marques |               |
| Igor Mamus       |               |
| Felipe Ribas     |               |
| João Manfrim     |               |

---

## 9 · Referências

1. Johnson, D. S. "Approximation algorithms for combinatorial problems", *JCSS* 1974.
2. Feige, U. "A threshold of ln n for approximating set cover", *JACM* 1998.
3. Apostila "NP‑Completude & Heurísticas", Prof. Scalabrin, 2025.

---
