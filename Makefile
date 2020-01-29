lint:
	python -m isort -rc -w 100 -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	find nssh -type f \( -iname "*.py" ! -iname "ptyprocess.py" \) | xargs darglint

cov_unit:
	python -m pytest \
		--cov=nssh \
		--cov-report html \
		--cov-report term \
		tests/unit/