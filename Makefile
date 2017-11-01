all: run
	

clean:
	rm -rf build

env:
	@if [ ! -d "build" ]; then virtualenv build; fi


deps: env
	@build/bin/pip install -Ue '.[dev]'
	@build/bin/pip install bandit scame nose
	@build/bin/python -m pip install -Ue '.[dev]'


run:
	@build/bin/scame --progress --pycodestyle scame/ README.rst release-notes.rst

check:
	@echo "========= pyflakes ================"
	@build/bin/pyflakes scame/
	@echo "========= pycodestyle ============="
	@build/bin/pycodestyle scame/
	@echo "========= bandit =================="
	#@build/bin/bandit -n 0 -f txt -r scame/
	@echo "========= pylint ============="
	#@build/bin/pylint scame/

test: run check
	@build/bin/nosetests --with-id scame/
