lint:
	python -m isort -rc -w 100 -y .
	python -m black .
	python -m pylama .
	python -m pydocstyle .
	find nssh -type f \( -iname "*.py" ! -iname "ptyprocess.py" \) | xargs darglint
