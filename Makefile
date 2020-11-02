.PHONY: run
run: venv
	venv/bin/python ./run.py

.PHONY: venv
venv: requirements.txt
	virtualenv -p python3 venv
	venv/bin/pip install -r requirements.txt


.PHONY: clean
clean:
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./venv
