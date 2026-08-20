clean:
	rm -rf dist/
	rm -rf pymonta.egg-info/

build: clean
	uv build