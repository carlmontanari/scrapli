.DEFAULT_GOAL := help

## Show this help
help:
	@awk -f util/makefile-doc.awk $(MAKEFILE_LIST)

##@ Development
## Format all python files
fmt:
	python -m isort setup.py noxfile.py scrapli/ examples/ tests/
	python -m black setup.py noxfile.py scrapli/ examples/ tests/

## Format all python files in check mode (for ci)
fmt-check:
	python -m isort --check --diff setup.py noxfile.py scrapli/ examples/ tests/
	python -m black --check --diff setup.py noxfile.py scrapli/ examples/ tests/

## Run linters
lint:
	python -m ruff check
	python -m mypy --strict setup.py noxfile.py scrapli/ examples/

##@ Testing
## Run unit tests
test:
	python -m pytest tests/unit/ -v

## Run all tests with term and html coverage report
test-cov:
	python -m pytest tests/unit/ -v \
	--cov=scrapli \
	--cov-report html

## Run functional tests
test-functional:
	python -m pytest tests/functional/ -v

## Run functional tests against "ci" test topology
test-functional-ci:
	python -m pytest tests/functional/ -v $(ARGS)

##@ Test Environment
## Runs the clab functional testing topo; uses the clab launcher to run nicely on darwin
run-clab:
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
		ghcr.io/scrapli/scrapli_clab/launcher:0.0.7

## Runs the clab functional testing topo with the ci specific topology - omits ceos
run-clab-ci:
	mkdir .clab || true
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
        --privileged \
        --pid=host \
        --stop-signal=SIGINT \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v /run/netns:/run/netns \
        -v "$$(pwd):$$(pwd)" \
        -e "WORKDIR=$$(pwd)/.clab" \
        -e "HOST_ARCH=$$(uname -m)" \
        -e "CLAB_TOPO=topo.ci.$$(uname -m).yaml" \
        ghcr.io/scrapli/scrapli_clab/launcher:0.0.7

##@ Docs
## Serve docs locally.
.PHONY: docs
docs:
	python -m mkdocs serve --clean --strict
