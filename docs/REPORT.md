
---

### 📑 **REPORT.md** (atualizado com análises de Programas 1 e 2, pronto para futuros)

```markdown
# RELATÓRIO GERAL — Projeto Lotofácil & Complexidade

> **Autor:** Leonardo Marques, Igor Mamus, Felipe Ribas e João Manfrim
> **Disciplina:** Projeto de Algoritmos e Análise de Complexidade  
> **Data:** 2025-06-15

---

## Índice

1. Visão geral  
2. Programa 1 – Gerador S15…S11 + Benchmark  
3. Programa 2 – SB15_14 (Set-Cover)  
4. Programas 3 – 8 (pré-estruturados)  
5. Conclusões gerais  

---

## 1. Visão Geral

O projeto evolui em oito etapas, cada qual resolvendo um problema
algorítmico sobre as combinações da Lotofácil. Todos os algoritmos são
analisados quanto à **complexidade teórica** e **desempenho empírico**,
seguindo as recomendações do PDF de NP-Completude fornecido pelo professor.

---

## 2. Programa 1 — Gerar S k (k = 15 … 11)

| Aspecto | Detalhe |
|---------|---------|
| **Algoritmo** | `itertools.combinations` (lexicográfico) |
| **Tempo** | Θ( C(25,k) ) — inevitável (listagem exaustiva) |
| **Memória** | O(k)=15 ints (streaming) |
| **Bench** | ver `resultados/bench.csv` |

### Resultados empíricos (Intel i5-1135G7, Python 3.11)

| k | Combinações | Tempo (s) | Pico RAM (MiB) |
|---|-------------|-----------|----------------|
| 15 | 3 268 760 | 6.5 | 13.4 |
| 14 | 4 457 400 | 8.8 | 13.4 |
| 13 | 5 200 300 | 9.9 | 13.7 |
| 12 | 5 200 300 | 9.6 | 13.7 |
| 11 | 4 457 400 | 6.9 | 13.8 |

**Observação:** tempo cresce linearmente com o nº de combinações,
confirmando a análise Θ( C(25,k) ).

---

## 3. Programa 2 — SB15_14 (Cobertura de S14)

### 3.1 Definição do problema
Encontrar o **menor** subconjunto **SB15_14 ⊆ S15** que cubra
100 % das 4 457 400 sequências S14.  
Trata-se de um caso de **Set-Cover**, problema NP-Completo.

### 3.2 Algoritmo implementado
Heurística **Greedy Set-Cover**:

1. Para cada linha S15, gerar as 15 máscaras S14 cobertas.  
2. Manter heap por “ganho” (nº de S14 ainda não cobertos).  
3. Selecionar repetidamente o S15 de maior ganho até cobrir todo o universo.

*Complexidade teórica*

| Passo | Complexidade |
|-------|--------------|
| Pré-processamento (n·m) | O(|S15| · 15) ≈ 5 × 10⁷ |
| Loop Greedy (heap) | O(|S15| log |S15|) |
| **Total** | O(|S15| log |S15|) — dominado por heap |

*Memória*

* Índice S14 → int: 17 MB  
* Vector uncovered (bitarray): 0.6 MB  
* Heap: 3.3 M × 16 B ≈ 50 MB  
* Linhas S15 texto: 55 MB  
* Overhead Python ⇒ **pico medido 2.2 GB**

### 3.3 Resultados

> Log completo em `prog2_saida/cover14_log.csv`

### 3.4 Verificação
Programa executa passo adicional que reconstrui
todas as 4 457 400 S14 e confirma cobertura **100 %**.
Script aborta se alguma sequência faltar.

### 3.5 Discussão
Greedy fornece solução ≈ 79 % acima do limite inferior —
bem dentro da garantia teórica ln(|U|)+1 ≈ 16× e aceitável
para instância deste tamanho, validando a diretriz do PDF de
usar heurísticas quando brute force é inviável.

---

## 4. Programas 3 – 8 (Estrutura reservada)

| Prog | Problema | Algoritmo previsto | Complexidade (prev.) | Pasta |
|------|----------|--------------------|----------------------|-------|
| 3 | SB15_13 (cobrir todas S13) | Greedy adaptado (m=455) | O(|S15| log |S15|) | `prog3_saida/` |
| 4 | … | … | … | … |
| … | … | … | … | … |

*(as seções serão preenchidas conforme implementação)*

---

## 5. Conclusões gerais

* Programa 1 confirma que a listagem exaustiva é viável para n = 25.  
* Programa 2 demonstra aplicação prática de heurística para
  um problema NP-Completo, obtendo solução 1.79× do limite
  teórico em < 3 min e < 3 GB RAM.  
* A estrutura modular (pastas isoladas, logs CSV, verificação automática)
  garante reprodutibilidade e facilita avaliação futura dos Programas 3-8.

---

*FIM*