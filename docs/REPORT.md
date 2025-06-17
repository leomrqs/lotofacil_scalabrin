# RELATÓRIO GERAL — Projeto **Lotofácil & Complexidade**

> **Autores:** Leonardo Marques · Igor Mamus · Felipe Ribas · João Manfrim  
> **Máquina-teste:** Intel i5-8400 | 16 GB DDR4 | SSD | Windows 11 | Python 3.11  
> **Versão:** 16 jun 2025

---

## Índice
1. Visão geral  
2. Programa 1 — Geração **Sₖ** + Benchmark  
3. Fundamentos teóricos (Greedy Set-Cover)  
4. Programas 2 → 5 — detalhe e análise de complexidade  
5. Programa 7 — Custo financeiro  
6. Benchmarks consolidados  
7. Tabela de custos  
8. Estrutura de repositório & créditos  
9. Referências  

---

## 1 · Visão geral

O projeto parte de **3 268 760** cartões de 15 números (todas as S15) e chega a **∼ 3 200** cartões
que cobrem **100 %** das combinações-alvo de 11 números (S11).

**Pipeline**

| Etapa | Descrição | Scripts |
|-------|-----------|---------|
| ① Gerar  | S15…S11 lexicográficas | `lotogen.py` + `bench.py` |
| ② Cobrir | obtém SB15-k com Greedy | `programa2.py` … `programa5.py` |
| ③ Validar | garante 100 % cobertura | `verify_all.py` |
| ④ Medir  | tempo, RAM, α, α ∕ (ln|U|+1) | logs CSV |
| ⑤ Custear | R\$ 3,00 / cartão | `calcular_custo_sb.py` (Prog 7) |
| ⑥ ZIP    | material de entrega | `package.py` |

---

## 2 · Programa 1 — Geração **Sₖ**

### 2.1 Algoritmo

```python
for c in combinations(range(1,26), k):       # ordem lexicográfica
    fp.write(" ".join(map(str, c)) + "\n")   # streaming (O(k) RAM)
````

### 2.2 Complexidade

| Métrica   | Valor        | Observação               |
| --------- | ------------ | ------------------------ |
| **Tempo** | Θ(C(25,k))   | listar tudo é inevitável |
| **RAM**   | O(k)=15 ints | ≈ 120 B + buffer SO      |

### 2.3 Benchmarks (i5-8400)

|  k | C(25,k)   | Tempo (s) | Pico RAM |
| -: | --------- | --------- | -------- |
| 15 | 3 268 760 | 6.5       | 13 MiB   |
| 14 | 4 457 400 | 8.8       | 13 MiB   |
| 13 | 5 200 300 | 9.9       | 14 MiB   |
| 12 | 5 200 300 | 9.6       | 14 MiB   |
| 11 | 4 457 400 | 6.9       | 14 MiB   |

---

## 3 · Fundamentos — **Greedy Set-Cover**

> Dado **U** (todas as Sₖ) e coleção **𝒮** (S15), achar SB ⊆ 𝒮 tal que
> ⋃SB = U **e** |SB| mínimo (NP-Completo).

### 3.1 Algoritmo Greedy (Johnson 1974)

```
uncovered ← U
while uncovered ≠ ∅:
    C* ← argmax_{C∈𝒮} |C ∩ uncovered|
    SB ← SB ∪ {C*}
    uncovered ← uncovered \ C*
```

*Garantia de aproximação*
|SB| ≤ (ln|U| + 1) · |Ótimo|.
Para |U| ≈ 5 M ⇒ cota ≤ 16.

### 3.2 Implementação-base (k = 12)

```python
OMIT = list(combinations(range(15), 3))      # 455 tuplas
full = sum(1 << (n-1) for n in nums)         # máscara cheia
for a, b, c in OMIT:                         # XOR remove 3 números
    m = full ^ (bits[a] | bits[b] | bits[c])
    covered.append(idx_map[m])
```

*Sem `set()` e com XOR → 2,5 × mais rápido; -300 MiB de RAM.*

---

## 4 · Programas 2 → 5 — detalhe e **complexidade derivada**

\| Prog | k-alvo | |U| | Sub/linha | **Pré-proc.** | **Loop Greedy** | **Complexidade total** |
\|:---:|:-----:|--------|-----------|---------------|-----------------|------------------------|
\| **2** | 14 | 4 457 400 | 15  | O(n·15) | |SB|·log n | **O(n log n)** |
\| **3** | 13 | 5 200 300 | 105 | O(n·105) | |SB|·log n | **O(n log n)** |
\| **4** | 12 | 5 200 300 | 455 | O(n·455) | |SB|·log n | **O(n log n)** (*XOR 3 bits*) |
\| **5** | 11 | 4 457 400 | 1 365 | O(n·1 365) | |SB|·log n | **O(n log n)** (*XOR 4 bits + stream*) |

### 4.1 Resultados e α-razão

\| SB | |U| | ln|U|+1 | |SB| | Lower | **α** | **α ∕ (ln|U|+1)** | Tempo | RAM |
\|----|-----|--------|-------|-------|------|------|----------------|-------|-----|
\| SB15-14 | 4 457 400 | 16.31 | 532 555 | 297 160 | **1.79** | **0.110** | 188 s | 2.2 GB |
\| SB15-13 | 5 200 300 | 16.46 | 128 827 | 49 527  | **2.60** | **0.158** | 1 494 s | 4.4 GB |
\| SB15-12 | 5 200 300 | 16.46 | 38 100  | 11 430 | **3.33** | **0.202** | 4 384 s | 12.8 GB |
\| SB15-11 | 4 457 400 | 16.31 | 12 733 | 3 266 | **3.90** | **0.239** | 7 h 23 m | 12.9 GB |

> Todos os **α ∕ (ln|U|+1) ≤ 0 .24** ⇒ bem abaixo da cota teórica (1 .0).

#### Otimizações por programa

* **P2** — heap lazy-update + `bitarray`.
* **P3** — baseline (sem XOR) para comparação.
* **P4** — máscara cheia + XOR (3 bits), `OMIT_LIST` global, barra 50 000.
* **P5** — máscara cheia + XOR (4 bits), modo `--stream` (-4 GB RAM), barra 50 000.

---

## 5 · Programa 7 — Custo financeiro

`calcular_custo_sb.py` gera:

| Subconjunto |  Linhas |  Custo (R\$) | Status |
| ----------- | ------: | -----------: | ------ |
| SB15-14     | 532 555 | 1 597 665,00 | ok     |
| SB15-13     | 128 827 |   386 481,00 | ok     |
| SB15-12     |  38 100 |   114 300,00 | ok     |
| SB15-11     |  12 733 |    38 199,00 | ok     |

Arquivo salvo em `prog7_saida/resultados_custo_jogadas.csv`.

---

## 6 · Benchmarks consolidados

| Prog | Escopo  | α    | α ∕ ln | Tempo    | RAM     |
| :--: | ------- | ---- | ------ | -------- | ------- |
|   1  | S15…S11 | —    | —      | 6-15 s   | 13 MiB  |
|   2  | SB15-14 | 1.79 | 0.11   | 188 s    | 2.2 GB  |
|   3  | SB15-13 | 2.60 | 0.16   | 1 494 s  | 4.4 GB  |
|   4  | SB15-12 | 3.33 | 0.20   | 4 384 s  | 12.8 GB |
|   5  | SB15-11 | 3.90 | 0.24   | 26 598 s | 12.9 GB |

---

## 7 · Tabela de custos

| SB      | Cartões |          R\$ |
| ------- | ------: | -----------: |
| SB15-14 | 532 555 | 1 597 665,00 |
| SB15-13 | 128 827 |   386 481,00 |
| SB15-12 |  38 100 |   114 300,00 |
| SB15-11 |  12 733 |    38 199,00 |

De 3 268 760 cartões iniciais (R\$ 9,8 mi) para 12 733 cartões (R\$ 38 mil) → **economia 257 ×**.

---

## 8 · Estrutura & créditos

```
lotofacil_project/
├─ lotogen.py | bench.py
├─ programa2.py … programa5.py
├─ verify_all.py | calcular_custo_sb.py | package.py
├─ resultados/ | prog2-7_saida/
└─ docs/ → README.md | REPORT.md
```

| Membro               | Contribuições                                                |
| -------------------- | ------------------------------------------------------------ |
| **Leonardo Marques** | Algoritmos P2 & P5, otimizações XOR, README/REPORT, Makefile |
| **Igor Mamus**       | Geração lexicográfica (P1), bench, validate-hash             |
| **Felipe Ribas**     | Greedy SB15-13 (P3), profiling de memória                    |
| **João Manfrim**     | Verificadores, scripts de custo & package                    |

---

## 9 · Referências

1. Johnson, D. S. “Approximation algorithms for combinatorial problems”. *JCSS*, 1974.
2. Feige, U. “A threshold of ln n for approximating set cover”. *JACM*, 1998.
3. Apostila “NP-Completude & Heurísticas”, Prof. Scalabrin, 2025.

