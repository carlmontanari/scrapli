.DEFAULT_GOAL := help

BLUE   := $(shell tput -Txterm setaf 4)
YELLOW := $(shell tput -Txterm setaf 3)
GREEN  := $(shell tput -Txterm setaf 2)
RESET  := $(shell tput -Txterm sgr0)

.PHONY: help

help:
	@echo ""
	@echo "${YELLOW}Usage:${RESET} make ${GREEN}<target>${RESET}"
	@echo ""
	@awk ' \
    	/^##@@/ { gsub(/^##@@ */, ""); printf "\n${BLUE}%s${RESET}\n", toupper($$0); next } \
    	/^##@/  { gsub(/^##@ */, ""); printf "  ${YELLOW}%s:${RESET}\n", $$0; next } \
    	/^## /   { gsub(/^## */, ""); msg = $$0; next } \
    	/^[a-zA-Z0-9_-]+:/ { \
    	    target = $$1; gsub(/:.*/, "", target); \
        	if (match($$0, /## */)) { \
        	    msg = substr($$0, RSTART + RLENGTH); \
            } \
           	if (msg != "") { \
           	    printf "    ${GREEN}%-18s${RESET} %s\n", target, msg; \
               	msg = ""; \
            } \
    	} \
	' $(MAKEFILE_LIST)
	@echo ""

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
lint: fmt
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
