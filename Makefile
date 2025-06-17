# -------------------------------------------------
#  Projeto Lotofácil – Makefile (versão 2025‑06‑16)
# -------------------------------------------------
# Alvos rápidos:
#   make bench     – gera S15…S11 + bench.csv
#   make sb14/sb13/sb12/sb11  – executa Programas 2‑5
#   make verify    – valida todos os SB de uma vez
#   make logs      – exibe todos os logs CSV em prog*_saida/
#   make reset     – apaga *apenas* resultados & logs
#   make package   – cria lotofacil_submission.zip via package.py
#   make distclean – reset + remove lotofacil_submission.zip
# -------------------------------------------------

PY      ?= python
RESULTS = resultados

# Arquivos gerados pelo bench
S15 = $(RESULTS)/S15.csv
S14 = $(RESULTS)/S14.csv
S13 = $(RESULTS)/S13.csv
S12 = $(RESULTS)/S12.csv
S11 = $(RESULTS)/S11.csv

# Saídas Greedy
OUT2 = prog2_saida/SB15_14.csv
OUT3 = prog3_saida/SB15_13.csv
OUT4 = prog4_saida/SB15_12.csv
OUT5 = prog5_saida/SB15_11.csv

# -------------------------------------------------
.PHONY: help bench sb14 sb13 sb12 sb11 verify logs reset package distclean

help:
	@echo "\nAlvos disponíveis:";
	@echo "  bench     – gerar tabelas S15…S11 + bench.csv";
	@echo "  sb14      – gerar SB15_14 (cobre S14)";
	@echo "  sb13      – gerar SB15_13 (cobre S13)";
	@echo "  sb12      – gerar SB15_12 (cobre S12)";
	@echo "  sb11      – gerar SB15_11 (cobre S11)";
	@echo "  verify    – rodar verify_all.py (requer todos SB)";
	@echo "  logs      – mostrar todos os *_log.csv dentro de prog*_saida";
	@echo "  reset     – remover pastas de saída (mantém código)";
	@echo "  package   – gerar lotofacil_submission.zip";
	@echo "  distclean – reset + remove lotofacil_submission.zip";

# ----------------------
# Etapa 1: Benchmark
# ----------------------
$(S15):
	$(PY) bench.py

bench: $(S15)
	@echo "✔ Benchmark concluído – veja resultados/bench.csv"

# ----------------------
# Programas Greedy
# ----------------------

sb14: $(OUT2)
$(OUT2): $(S15) $(S14)
	$(PY) programa2.py

sb13: $(OUT3)
$(OUT3): $(S15) $(S13)
	$(PY) programa3.py

sb12: $(OUT4)
$(OUT4): $(S15) $(S12)
	$(PY) programa4.py

sb11: $(OUT5)
$(OUT5): $(S15) $(S11)
	$(PY) programa5.py

# ----------------------
# Verificação em lote
# ----------------------
verify: $(OUT2) $(OUT3) $(OUT4) $(OUT5)
	$(PY) verify_all.py

# ----------------------
# Exibir logs
# ----------------------
logs:
	@echo "\n### Conteúdo dos logs em prog*_saida/*.csv ###";
	@for f in prog*_saida/*_log.csv ; do \
		if [ -f $$f ]; then echo "\n--- $$f ---"; cat $$f; fi ; \
	done
	@for f in prog7_saida/*.csv ; do \
		if [ -f $$f ]; then echo "\n--- $$f ---"; cat $$f; fi ; \
	done

# ----------------------
# Limpeza / Reset
# ----------------------
RESET_DIRS = resultados prog2_saida prog3_saida prog4_saida prog5_saida prog7_saida

reset:
	rm -rf $(RESET_DIRS)
	@echo "🗑️  Pastas de resultados removidas."

distclean: reset
	rm -f lotofacil_submission.zip
	@echo "🧹 Repositório limpo (sem artefatos)."

# ----------------------
# Empacotamento final
# ----------------------
package: verify
	$(PY) package.py
	@echo "✔ lotofacil_submission.zip pronto para envio."
