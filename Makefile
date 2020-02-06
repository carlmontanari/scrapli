DOCKER_COMPOSE_FILE=docker-compose.yaml
DOCKER_COMPOSE=docker-compose -f ${DOCKER_COMPOSE_FILE}

lint:
	python -m isort -rc -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	python -m mypy --strict nssh/
	find nssh -type f \( -iname "*.py" ! -iname "ptyprocess.py" \) | xargs darglint

cov:
	python -m pytest \
		--cov=nssh \
		--cov-report html \
		--cov-report term \
		tests/

cov_unit:
	python -m pytest \
		--cov=nssh \
		--cov-report html \
		--cov-report term \
		tests/unit/

cov_functional:
	python -m pytest \
		--cov=nssh \
		--cov-report html \
		--cov-report term \
		tests/functional/

test:
	python -m pytest tests/

test_unit:
	python -m pytest tests/unit/

test_functional:
	python -m pytest tests/functional/

test_iosxe:
	python -m pytest -v \
	tests/unit \
	tests/functional/driver/core/cisco_iosxe

test_nxos:
	python -m pytest -v \
	tests/unit \
	tests/functional/driver/core/cisco_nxos

test_iosxr:
	python -m pytest -v \
	tests/unit \
	tests/functional/driver/core/cisco_iosxr

test_eos:
	python -m pytest -v \
	tests/unit \
	tests/functional/driver/core/arista_eos

test_junos:
	python -m pytest -v \
	tests/unit \
	tests/functional/driver/core/juniper_junos

.PHONY: docs
docs:
	python -m pdoc \
	--html \
	--output-dir docs \
	nssh \
	--force

start_dev_env:
	${DOCKER_COMPOSE} \
		up -d \
		iosxe \
		nxos \
		junos \
		iosxr

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

start_dev_env_junos:
	${DOCKER_COMPOSE} \
		up -d \
		junos

start_dev_env_eos:
	${DOCKER_COMPOSE} \
		up -d \
		eos

stop_dev_env:
	${DOCKER_COMPOSE} \
		down