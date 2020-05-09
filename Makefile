DOCKER_COMPOSE_FILE=docker-compose.yaml
DOCKER_COMPOSE=docker-compose -f ${DOCKER_COMPOSE_FILE}

lint:
	python -m isort -rc -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	python -m mypy --strict scrapli/

lint_full:
	python -m isort -rc -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	python -m mypy --strict scrapli/
	find scrapli -type f \( -iname "*.py" ! -iname "ptyprocess.py" \) | xargs darglint -x

cov:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/

cov_unit:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/unit/

cov_functional:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/functional/

cov_iosxe:
	rm -rf .coverage
	rm -rf htmlcov
	python -m pytest \
	--cov=scrapli \
	tests/unit
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	--cov-append \
	tests/functional -k "cisco_iosxe"

cov_nxos:
	rm -rf .coverage
	rm -rf htmlcov
	python -m pytest \
	--cov=scrapli \
	tests/unit
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	--cov-append \
	tests/functional -k "cisco_nxos"

cov_iosxr:
	rm -rf .coverage
	rm -rf htmlcov
	python -m pytest \
	--cov=scrapli \
	tests/unit
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	--cov-append \
	tests/functional -k "cisco_iosxr"

cov_eos:
	rm -rf .coverage
	rm -rf htmlcov
	python -m pytest \
	--cov=scrapli \
	tests/unit
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	--cov-append \
	tests/functional -k "arista_eos"

cov_junos:
	rm -rf .coverage
	rm -rf htmlcov
	python -m pytest \
	--cov=scrapli \
	tests/unit
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	--cov-append \
	tests/functional -k "juniper_junos"

cov_linux:
	rm -rf .coverage
	rm -rf htmlcov
	python -m pytest \
	--cov=scrapli \
	tests/unit
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	--cov-append \
	tests/functional -k "linux"

test:
	python -m pytest tests/
	python -m pytest examples/

test_unit:
	python -m pytest tests/unit/

test_functional:
	python -m pytest tests/functional/
	python -m pytest examples/

test_iosxe:
	python -m pytest \
	tests/unit \
	tests/functional -k "cisco_iosxe"

test_nxos:
	python -m pytest \
	tests/unit \
	tests/functional -k "cisco_nxos"

test_iosxr:
	python -m pytest \
	tests/unit \
	tests/functional -k "cisco_iosxr"

test_eos:
	python -m pytest \
	tests/unit \
	tests/functional -k "arista_eos"

test_junos:
	python -m pytest \
	tests/unit \
	tests/functional -k "juniper_junos"

test_linux:
	python -m pytest \
	tests/unit \
	tests/functional -k "linux"

test_examples:
	python -m pytest examples/

.PHONY: docs
docs:
	rm -rf docs/scrapli
	python -m pdoc \
	--html \
	--output-dir docs \
	scrapli \
	--force

start_dev_env:
	${DOCKER_COMPOSE} \
		up -d \
		iosxe \
		nxos \
		junos \
		iosxr \
		linux

start_dev_env_iosxe:
	${DOCKER_COMPOSE} \
		up -d \
		iosxe

start_dev_env_nxos:
	${DOCKER_COMPOSE} \
		up -d \
		nxos

start_dev_env_iosxr:
	${DOCKER_COMPOSE} \
		up -d \
		iosxr

start_dev_env_eos:
	${DOCKER_COMPOSE} \
		up -d \
		eos

start_dev_env_junos:
	${DOCKER_COMPOSE} \
		up -d \
		junos

start_dev_env_linux:
	${DOCKER_COMPOSE} \
		up -d \
		linux

stop_dev_env:
	${DOCKER_COMPOSE} \
		down

prepare_dev_env:
	python tests/functional/prepare_devices.py cisco_iosxe,cisco_nxos,cisco_iosxr,arista_eos,juniper_junos

prepare_dev_env_iosxe:
	python tests/functional/prepare_devices.py cisco_iosxe

prepare_dev_env_nxos:
	python tests/functional/prepare_devices.py cisco_nxos

prepare_dev_env_iosxr:
	python tests/functional/prepare_devices.py cisco_iosxr

prepare_dev_env_eos:
	python tests/functional/prepare_devices.py arista_eos

prepare_dev_env_junos:
	python tests/functional/prepare_devices.py juniper_junos