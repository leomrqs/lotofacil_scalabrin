# Projeto Lotofácil — Algoritmos & Complexidade

Este repositório contém **oito programas** (Programas 1-8), cada um resolvendo
um cenário incremental do trabalho de Complexidade & NP-Completude.

| Programa | Cenário | Diretório de saída | Arquivo‐chave gerado |
|----------|---------|--------------------|----------------------|
| 1 `bench.py / lotogen.py` | gerar S15…S11 + benchmark | `resultados/` | `S15.csv`, … |
| 2 `programa2.py` | encontrar SB15_14 (cobre todo S14) | `prog2_saida/` | `SB15_14.csv` |
| 3 | _(reserva)_ | `prog3_saida/` | — |
| 4 | … | … | … |
| 5 | … | … | … |
| 6 | … | … | … |
| 7 | … | … | … |
| 8 | … | … | … |

> Cada programa grava **seus próprios resultados em uma pasta isolada** para
> evitar conflito de arquivos e facilitar correção.

---

## 1. Requisitos

* Python ≥ 3.8  
* Bibliotecas: `psutil`, `bitarray` *(opcional, mas acelera verificaç.*)*

```bash
pip install psutil bitarray
