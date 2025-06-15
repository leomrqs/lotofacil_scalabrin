# Makefile nao atualizado, leia readme.md

.PHONY: bench clean package

bench:
	python bench.py          # gera resultados/ + log + tar

clean:
	rm -rf resultados

package: clean bench
	tar -czf lotofacil_submission.tar.gz lotogen.py bench.py README.md REPORT.md Makefile
