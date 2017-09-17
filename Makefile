test: init
	pipenv run py.test tests
init:
	pipenv install --skip-lock
publish:
	python setup.py register
	python setup.py sdist upload
	python setup.py bdist_wheel --universal upload
	rm -fr build dist .egg records.egg-info