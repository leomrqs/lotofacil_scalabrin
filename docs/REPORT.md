# RELATÓRIO GERAL — Projeto **Lotofácil & Complexidade**

> **Autores:** Leonardo Marques · Igor Mamus · Felipe Ribas · João Manfrim\
> **Plataforma‑teste:** Intel i5‑8400 · 16 GB DDR4 · SSD · Windows 11 · Python 3.11\
> **Versão:** 16 jun 2025

---

## Índice

1. Visão geral
2. Programa 1 — Geração Sₖ + Benchmark
3. Fundamentos da heurística Greedy Set‑Cover
4. Programas 2 – 3 — Resultados SB15‑14, SB15‑13 (implementação menos otimizada)
5. Programas 4 e 5 — SB15‑12, SB15‑11 (implementação otimizada)
6. Benchmarks consolidados (P1 – P5)
7. Custo financeiro dos subconjuntos
8. Estrutura de repositório & contribuições
10. Referências

---

## 1 · Visão geral

- **Objetivo global:** Cobrir 100 % das sequências Sₖ (k = 14, 13, 12, 11) usando o menor número possível de cartões S15.
- **Pipeline:**
  1. **Gerar** exaustivamente Sₖ (Programa 1) em ordem lexicográfica ― garante checagem determinística.
  2. **Selecionar** subconjuntos SB15‑k via **Greedy Set‑Cover** (Programas 2‑5).
  3. **Medir** tempo, pico de RAM e fator de aproximação α = |SB| / Lower‑bound.
  4. **Converter** em custo financeiro (R\$ 3,00 por cartão).

---

## 2 · Programa 1 — Geração exaustiva & Benchmark

### 2.1 Implementação‑núcleo

```python
from itertools import combinations

def stream_Sk(k: int, fp):
    for comb in combinations(range(1, 26), k):      # ordem lexicográfica
        fp.write(" ".join(map(str, comb)) + "\n")  # streaming: O(k) RAM
```

*Streaming* garante consumo O(k) memória (\~120 B). A ordem lexicográfica facilita hashes incrementais e retomada.

### 2.2 Complexidade teórica

| Métrica | Valor          | Justificativa                            |
| ------- | -------------- | ---------------------------------------- |
| Tempo   | Θ(C(25,k))     | listar todas as combinações é inevitável |
| RAM     | O(k) = 15 ints | apenas a combinação corrente + buffer SO |

### 2.3 Resultados de Geração Lexicográfica (`bench.py`)

| k  | C(25,k)   | Tempo (s) | Pico RAM (MiB) |
| -- | --------- | --------- | -------------- |
| 15 | 3 268 760 | 6.5       | 13.4           |
| 14 | 4 457 400 | 8.8       | 13.4           |
| 13 | 5 200 300 | 9.9       | 13.7           |
| 12 | 5 200 300 | 9.6       | 13.7           |
| 11 | 4 457 400 | 6.9       | 13.8           |

> **Observação:** tempo cresce linearmente com C(25,k); RAM permanece constante.

---

## 3 · Fundamentos da **Greedy Set‑Cover**

### 3.1 Definição

Dado **U** (universo Sₖ) e coleção **𝒮** (todas as linhas S15), encontrar o menor SB ⊆ 𝒮 tal que **⋃SB = U**.

### 3.2 Algoritmo Greedy

```text
uncovered ← U
while uncovered ≠ ∅:
    C* ← argmax_{C∈𝒮} |C ∩ uncovered|
    SB ← SB ∪ {C*}
    uncovered ← uncovered \ C*
```

**Teorema (Johnson 1974):** |SB| ≤ (ln|U| + 1) · |Ótimo|.  Para |U| ≈ 5 M, cota ≤ 16.

### 3.3 Trecho crítico (Programa 4)

```python
OMIT_LIST = list(combinations(range(15), 3))  # 455 tuplas (15 C 12)
full_mask = sum(1 << (n-1) for n in nums)
for o in OMIT_LIST:        # remove 3 bits via XOR
    m = full_mask ^ (bits[o[0]] | bits[o[1]] | bits[o[2]])
    covered.append(idx_map[m])
```

*Evita **`set()`** por iteração; cada máscara S12 sai com 3 operações de bit ― \~2,5× mais rápido que reconstruir inteiro.*

---

## 4 · Programas 2 – 4 — Resultados

\| SB          | Universo | |SB| | Lower‑bound | α | Tempo | Pico RAM | |-------------|----------|-----|--------------|----|-------|----------| | **SB15‑14** | 4 457 400 S14 | 532 555 | 297 160 | **1.79** | 188 s | 2.2 GB | | **SB15‑13** | 5 200 300 S13 | 128 827 | 49 527  | **2.60** | 1 494 s | 4.4 GB | | **SB15‑12** | 5 200 300 S12 | 38 100  | 11 430 | **3.33** | 4 384 s | 12.8 GB |

Validação 100 % cobertura executada via reconstrução das C(15,k) máscaras.

---

## 5 · Programa 5 — SB15‑11 (implementação otimizada)

- Cada linha S15 cobre **1 365** sequências S11 (C(15,11)).
- Limite inferior: **3 266** cartões.

### 5.1 Otimizações adicionais

| Técnica                                | Impacto                              |
| -------------------------------------- | ------------------------------------ |
| Pré‑cálculo `OMIT_LIST` (1 365 tuplas) | -3 M `combinations`                  |
| Máscara base + XOR                     | 2× mais rápido que re‑combinar       |
| Modo `--stream`                        | corta \~4 GB RAM (custo +20 % tempo) |
| STEP 50 000                            | feedback a cada \~2 min              |

> **Execução longa:** previsão |SB| ≈ 3 200 → α ≈ 1.10; \~7 min / 3 GB RAM.

---

## 6 · Benchmarks consolidados

| Prog | Chunk   | Tempo    | RAM     | α      |
| ---- | ------- | -------- | ------- | ------ |
| 1    | S15…S11 | 6 – 10 s | 13 MiB  | 1      |
| 2    | SB15‑14 | 188 s    | 2.2 GB  | 1.79   |
| 3    | SB15‑13 | 1 494 s  | 4.4 GB  | 2.60   |
| 4    | SB15‑12 | 4 384 s  | 12.8 GB | 3.33   |
| 5    | SB15‑11 | em exec. | 3 GB    | 1.10\* |

\* valor previsto.

---

## 7 · Custo financeiro (R\$ 3,00)

\| SB | |SB| | Custo | |----|-----|----------------| | SB15‑14 | 532 555 | **R\$ 1 597 665,00** | | SB15‑13 | 128 827 | **R\$   386 481,00** | | SB15‑12 | 38 100  | **R\$   114 300,00** | | SB15‑11 | ≈ 3 200 | ≈ R\$     9 600,00 |

> Redução de 9,8 milhões (gerar todos) para \~9,6 mil (SB15‑11) → **economia 1 020×**.

---

## 8 · Estrutura & contribuições

```text
lotofacil_project/
├─ lotogen.py, 
├─ bench.py                # Programa 1 (=python bench.py)
├─ programa2.py … programa5.py         # Greedy SB15‑k (=python programa2-5*.py)
├─ verify_all.py, calcular_custo_sb.py # utilitários
├─ resultados/, prog*_saida/           # CSV + logs
├─ docs/ (README.md, REPORT.md, PDFs)
└─ package.py                          # zip automatizado
```

| Membro           | Contribuições            |
| ---------------- | ------------------------ |
| Leonardo Marques | P2, P5, README, Makefile |
| Igor Mamus       | P1 (geração & bench)     |
| Felipe Ribas     | P3 (Greedy SB15‑13)      |
| João Manfrim     | Verificadores & métricas |



## 10 · Referências

1. Johnson, D. S. "Approximation algorithms for combinatorial problems", *JCSS* 1974.
2. Feige, U. "A threshold of ln n for approximating set cover", *JACM* 1998.
3. Apostila "NP‑Completude & Heurísticas", Prof. Scalabrin, 2025.

---


