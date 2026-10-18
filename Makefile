.PHONY: generate load dbt mine all clean

PYTHON = python
PIPELINE = pipeline/run_pipeline.py

generate:
	$(PYTHON) $(PIPELINE) --only generate

load:
	$(PYTHON) $(PIPELINE) --only load

dbt:
	$(PYTHON) $(PIPELINE) --only dbt

mine:
	$(PYTHON) $(PIPELINE) --only mine

all:
	$(PYTHON) $(PIPELINE)

clean:
	$(PYTHON) -c "import shutil; from pathlib import Path; [shutil.rmtree(p) for p in [Path('dbt_project/target'), Path('dbt_project/logs')] if p.exists()]"
