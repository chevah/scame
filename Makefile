all: run check
	

clean:
	rm -rf build

env:
	@if [ ! -d "build" ]; then virtualenv -p 3.9 build; fi


deps: env
	@build/bin/python -m pip install -Ue '.[dev]'


run:
	@build/bin/scame --progress scame/ README.rst release-notes.rst

check:
	@echo "========= pyflakes ================"
	@build/bin/pyflakes scame/
#	@echo "========= pycodestyle ============="
#	@build/bin/pycodestyle --ignore E501,E203,W503 scame/
#	@echo "========= bandit =================="
#	@build/bin/bandit -n 0 -f txt -r scame/
#	@echo "========= pylint ============="
#	@build/bin/pylint scame/
	@echo "========= black ==========="
	black --check scame/ setup.py

test: run
	@build/bin/nosetests scame/

coverage:
	@build/bin/coverage run --source=scame -m unittest discover
	@build/bin/coverage html
	xdg-open htmlcov/index.html
