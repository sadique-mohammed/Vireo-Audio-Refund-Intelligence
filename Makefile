PYTHON ?= python3

.PHONY: run run-live smoke test clean

run:
	$(PYTHON) -m src.vireo.pipeline --mode cache

run-live:
	$(PYTHON) -m src.vireo.pipeline --mode live

smoke:
	$(PYTHON) scripts/smoke_live.py

test:
	$(PYTHON) -m pytest -q

clean:
	rm -f outputs/*.csv outputs/*.json outputs/*.md
