.PHONY: run
run: venv
	venv/bin/python ./run.py

.PHONY: venv
venv: requirements.txt
	virtualenv -p python venv
	venv/bin/pip3 install -r requirements.txt


.PHONY: clean
clean:
	find . -iname '*.pyc' | xargs rm -f
	rm -rf ./venv
