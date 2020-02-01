lint:
	python -m isort -rc -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
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
	tests/functional/cisco_iosxe

test_nxos:
	python -m pytest -v \
	tests/unit \
	tests/functional/cisco_nxos

test_iosxr:
	python -m pytest -v \
	tests/unit \
	tests/functional/cisco_iosxr

test_eos:
	python -m pytest -v \
	tests/unit \
	tests/functional/arista_eos

test_junos:
	python -m pytest -v \
	tests/unit \
	tests/functional/juniper_junos

.PHONY: docs
docs:
	python -m pdoc \
	--html \
	--output-dir docs \
	nssh \
	--force