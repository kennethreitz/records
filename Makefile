testall:
	tox
test: init
	pipenv run pytest tests
init:
	pipenv install --skip-lock --dev
publish:
	python setup.py register
	python setup.py sdist upload
	python setup.py bdist_wheel --universal upload
	rm -fr build dist .egg records.egg-info
