lint:
	python -m isort .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	python -m mypy --strict scrapli/

darglint:
	find scrapli -type f \( -iname "*.py" \) | xargs darglint -x

test:
	python -m pytest \
	tests/

cov:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/

test_unit:
	python -m pytest \
	tests/unit/

cov_unit:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/unit/

test_integration:
	python -m pytest \
	tests/integration/

cov_integration:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/integration/

test_functional:
	python -m pytest \
	tests/functional/

cov_functional:
	python -m pytest \
	--cov=scrapli \
	--cov-report html \
	--cov-report term \
	tests/functional/

.PHONY: docs
docs:
	python docs/generate/generate_docs.py

test_docs:
	mkdocs build --clean --strict
	htmltest -c docs/htmltest.yml -s
	rm -rf tmp

deploy_docs:
	mkdocs gh-deploy

DOCKER_COMPOSE_FILE=docker-compose.yaml
DOCKER_COMPOSE=docker-compose -f ${DOCKER_COMPOSE_FILE}

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

prepare_dev_env:
	python tests/prepare_devices.py cisco_iosxe,cisco_nxos,cisco_iosxr,arista_eos,juniper_junos

prepare_dev_env_iosxe:
	python tests/prepare_devices.py cisco_iosxe

prepare_dev_env_nxos:
	python tests/prepare_devices.py cisco_nxos

prepare_dev_env_iosxr:
	python tests/prepare_devices.py cisco_iosxr

prepare_dev_env_eos:
	python tests/prepare_devices.py arista_eos

prepare_dev_env_junos:
	python tests/prepare_devices.py juniper_junos
