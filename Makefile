.PHONY: run
run: venv
	venv/scripts/python ./run.py

.PHONY: venv
venv: requirements.txt
	virtualenv -p python3 venv
	venv/scripts/pip3 install -r requirements.txt


.PHONY: clean
clean:
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./venv
