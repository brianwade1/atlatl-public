PYTHON ?= uv run python

.PHONY: simple_test cnn_test clean

simple_test:
	$(PYTHON) simple_demo.py
	$(PYTHON) testdir/read_demo.py simple

cnn_test:
	$(PYTHON) cnn_demo.py
	$(PYTHON) testdir/read_demo.py cnn

clean:
	rm -rf __pycache__ models testdir/__pycache__
