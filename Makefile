release:
	python setup.py sdist bdist_wheel upload

docs:
	cd docs && make html

.PHONY: docs
