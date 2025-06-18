.DEFAULT_GOAL := help

help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

fmt: ## Run formatters
	python -m isort setup.py noxfile.py scrapli/ tests/
	python -m black setup.py noxfile.py scrapli/ tests/

fmt-check:
	python -m isort --check --diff setup.py noxfile.py scrapli/ tests/
	python -m black --check --diff setup.py noxfile.py scrapli/ tests/

lint: ## Run linters
	python -m ruff check
	python -m mypy --strict setup.py noxfile.py scrapli/

test: ## Run unit tests
	python -m pytest tests/unit/ -v

test-cov:  ## Run all tests with term and html coverage report
	python -m pytest tests/unit/ -v \
	--cov=scrapli \
	--cov-report html

test-functional: ## Run functional tests
	python -m pytest tests/functional/ -v

test-functional-ci: ## Run functional tests against "ci" test topology
	python -m pytest tests/functional/ -v $(ARGS)

run-clab: ## Runs the clab functional testing topo; uses the clab launcher to run nicely on darwin
	rm -r .clab/* || true
	docker network rm clab || true
	docker network create \
		--driver bridge \
		--subnet=172.20.20.0/24 \
		--gateway=172.20.20.1 \
		--ipv6 \
		--subnet=2001:172:20:20::/64 \
		--gateway=2001:172:20:20::1 \
		--opt com.docker.network.driver.mtu=65535 \
		--label containerlab \
		clab
	docker run \
		-d \
		--rm \
		--name clab-launcher \
		--platform=linux/arm64 \
		--privileged \
		--pid=host \
		--stop-signal=SIGINT \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v /run/netns:/run/netns \
		-v "$$(pwd):$$(pwd)" \
		-e "WORKDIR=$$(pwd)/.clab" \
		-e "HOST_ARCH=$$(uname -m)" \
		ghcr.io/scrapli/scrapli_clab/launcher:0.0.3
