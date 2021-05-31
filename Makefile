all: run check
	

clean:
	rm -rf venv

env:
	@if [ ! -d "venv" ]; then virtualenv -p 3.9 venv; fi


deps: env
	@venv/bin/python -m pip install -Ue '.[dev]'


run:
	@venv/bin/scame --progress scame/ README.rst release-notes.rst

check:
	@echo "========= pyflakes ================"
	@venv/bin/pyflakes scame/
	@echo "========= isort ==========="
	@venv/bin/isort --profile black scame
	@echo "========= black ==========="
	@venv/bin/black scame/ setup.py


test: run
	@venv/bin/nosetests scame/

coverage:
	@venv/bin/coverage run --source=scame -m unittest discover
	@venv/bin/coverage html
	xdg-open htmlcov/index.html

release:
	@venv/bin/python setup.py bdist_wheel upload -r chevah
