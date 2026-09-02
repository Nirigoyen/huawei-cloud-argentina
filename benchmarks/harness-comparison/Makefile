.PHONY: setup verify docker run run-quality run-speed analyze rank report all clean dry-run help

PYTHON ?= python3
CONFIG ?= config/maas.yaml

help:
	@echo "Benchmark targets:"
	@echo "  setup        Install and configure all harnesses (scripts/setup_harnesses.sh)"
	@echo "  verify       Check MaaS endpoints respond (scripts/verify_maas.py)"
	@echo "  docker       Build all Docker images (docker/)"
	@echo "  run          Run full benchmark with default config"
	@echo "  run-quality  Run with quality model profile (deepseek-v4-pro)"
	@echo "  run-speed    Run with speed model profile (deepseek-v4-flash)"
	@echo "  analyze      Aggregate results and compute statistics"
	@echo "  rank         Compute Bradley-Terry rankings"
	@echo "  report       Generate HTML dashboard"
	@echo "  all          setup -> verify -> docker -> run -> analyze -> rank -> report"
	@echo "  clean        Remove results/ and logs/"
	@echo "  dry-run      2 harnesses x 5 tasks x 1 rep for validation"
	@echo ""
	@echo "Variables:"
	@echo "  PYTHON=$(PYTHON)  CONFIG=$(CONFIG)"

setup:
	./scripts/setup_harnesses.sh

verify:
	$(PYTHON) scripts/verify_maas.py

docker:
	docker build -f docker/Dockerfile.python -t bench-python docker/
	docker build -f docker/Dockerfile.node   -t bench-node   docker/
	docker build -f docker/Dockerfile.go     -t bench-go     docker/
	docker build -f docker/Dockerfile.rust   -t bench-rust   docker/
	docker build -f docker/Dockerfile.java   -t bench-java   docker/
	docker build -f docker/Dockerfile.multi   -t bench-multi  docker/

run:
	$(PYTHON) runners/run_benchmark.py --config $(CONFIG)

run-quality:
	$(PYTHON) runners/run_benchmark.py --config $(CONFIG) --model-profile quality

run-speed:
	$(PYTHON) runners/run_benchmark.py --config $(CONFIG) --model-profile speed

analyze:
	$(PYTHON) analysis/aggregate.py

rank:
	$(PYTHON) analysis/bradley_terry.py

report:
	$(PYTHON) analysis/generate_report.py

all: setup verify docker run analyze rank report

clean:
	rm -rf results/raw/* results/aggregated/* results/reports/* logs/*

dry-run:
	$(PYTHON) runners/run_benchmark.py --config $(CONFIG) \
		--harnesses aider,openhands --max-tasks 5 --repetitions 1
