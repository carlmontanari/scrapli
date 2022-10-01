.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

lint:  ## Run linters
	python -m isort .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	python -m mypy --strict scrapli/

darglint:  ## Run darglint (docstring/arg checker)
	find scrapli -type f \( -iname "*.py" \) | xargs darglint -x

test:  ## Run all tests
	python -m pytest \
	tests/

cov:  ## Run all tests with term and html coverage report
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/

test_unit:  ## Run all unit tests
	python -m pytest \
	tests/unit/

cov_unit:  ## Run all unit tests with term and html coverage report
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/unit/

test_integration:  ## Run integration tests
	python -m pytest \
	tests/integration/

cov_integration:  ## Run integration with term and html coverage report
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/integration/

test_functional:  ## Run functional tests
	python -m pytest \
	tests/functional/

cov_functional:  ## Run functional tests with term and html coverage report
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/functional/

.PHONY: docs
docs:  ## Regenerate docs
	python docs/generate.py

test_docs:  ## Run doc testing
	mkdocs build --clean --strict
	htmltest -c docs/htmltest.yml -s
	rm -rf tmp

deploy_docs:  ## Deploy docs to github
	mkdocs gh-deploy

deploy_clab: ## Deploy functional clab test topology
	cd .clab && sudo clab deploy -t topo-full.yaml

destroy_clab: ## Destroy functional clab test topology
	cd .clab && sudo clab destroy -t topo-full.yaml

prepare_dev_env: ## Prepare a running clab environment with base configs for testing
	python tests/prepare_devices.py cisco_iosxe,cisco_nxos,cisco_iosxr,arista_eos,juniper_junos
