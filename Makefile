FLAKE8 := flake8
FLAKE8_CONFIG := .github/linters/.flake8  # Change this to the path of your .flake8 configuration file

all: compile test checkstyle

compile:
	python3 -m py_compile *.py

test:
	python3 -m doctest *.py

checkstyle:
	$(FLAKE8) --config=$(FLAKE8_CONFIG) *.py

clean:
	rm -rf __pycache__
	rm -f *.pyc
