# Targets for Linux/OCF. On Windows, see README.md for the equivalent commands.
.PHONY: run venv build-css test clean

venv: pyproject.toml
	python3 -m venv venv
	venv/bin/pip install -e ".[dev]"

run:
	venv/bin/python run.py

# Requires the standalone Tailwind CLI (see README). The compiled app.css is
# committed, so this only needs to run after editing templates or input.css.
build-css:
	./tailwindcss -i tasa_website/static/css/input.css -o tasa_website/static/css/app.css --minify

test:
	venv/bin/python -m pytest tests/ -q

clean:
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./venv
