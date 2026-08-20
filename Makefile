clean:
	rm -rf dist/
	rm -rf pycut.egg-info/

build: clean
	uv build