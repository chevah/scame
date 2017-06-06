all: run
	

clean:
	rm -rf build

env:
	@if [ ! -d "build" ]; then virtualenv build; fi


deps: env
	# For leaderboard
	@build/bin/pip install -Ue '.[dev]'
	@build/bin/pip install bandit pocketlint nose


run:
	@build/bin/pocketlint pocketlint/

check:
	@echo "========= pyflakes ================"
	@build/bin/pyflakes pocketlint/
	@echo "========= pycodestyle ============="
	@build/bin/pycodestyle pocketlint/
	@echo "========= bandit =================="
	@build/bin/bandit -n 0 -f txt -r pocketlint/
	@echo "========= pylint ============="
	@build/bin/pylint pocketlint/

test: lint
	@build/bin/nosetest pocketlint/
