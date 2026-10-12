# Local operation on the Mac (where Ollama lives). `make help` lists targets.
PY      ?= .venv/bin/python
WEEK    ?= $(shell date -u +%G-W%V)
PLIST    = ~/Library/LaunchAgents/ai.k25x.weekly-roundup.plist

help:            ## this list
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  %-16s %s\n", $$1, $$2}'

setup:           ## create .venv and install dependencies
	python3 -m venv .venv && $(PY) -m pip install -q -r requirements.txt && echo "ok: .venv ready"

test:            ## offline test suite (no keys, no network)
	$(PY) -m pytest -q tests

ollama-check:    ## is Ollama up, which models are installed, does the configured one answer?
	$(PY) scripts/ollama_check.py

extract-test:    ## tag the sample week with the local model and score it against the watchlist (no API key)
	$(PY) scripts/test_extraction.py

ingest:          ## station 1 only, for this week
	$(PY) run_pipeline.py ingest --week $(WEEK)

weekly:          ## stations 1-2: collect, radar, Arabic script → output/$(WEEK)/script.md (needs ANTHROPIC_API_KEY)
	$(PY) run_pipeline.py all --week $(WEEK)

video:           ## station 3 after you approved script.md
	$(PY) run_pipeline.py video --week $(WEEK)

install-launchd: ## run `make weekly` every Saturday 10:00 local time (macOS)
	sed "s#__DIR__#$(CURDIR)#g" scripts/launchd.plist > $(PLIST) && launchctl unload $(PLIST) 2>/dev/null; launchctl load $(PLIST) && echo "installed: $(PLIST)"

uninstall-launchd: ## stop the Saturday job
	launchctl unload $(PLIST) && rm -f $(PLIST) && echo "removed"
