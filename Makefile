.PHONY: all clean lint test clean-deps deps
.DEFAULT_GOAL := all

all: .uptodate lint test

IMAGE_VERSION := $(shell ./tools/image-tag)

# Python-specific stuff
VIRTUALENV_DIR ?= .env
VIRTUALENV_BIN = $(VIRTUALENV_DIR)/bin
DEPS_UPTODATE = $(VIRTUALENV_DIR)/.deps-uptodate

VIRTUALENV := $(shell command -v virtualenv 2> /dev/null)
PIP := $(shell command -v pip 2> /dev/null)

JUNIT_XML := "junit.xml"

.ensure-virtualenv: .ensure-pip
ifndef VIRTUALENV
	$(error "virtualenv is not installed. Install with `pip install [--user] virtualenv`.")
endif
	touch .ensure-virtualenv

.ensure-pip:
ifndef PIP
	$(error "pip is not installed. Install with `python -m [--user] ensurepip`.")
endif
	touch .ensure-pip

$(VIRTUALENV_BIN)/pip: .ensure-virtualenv
	virtualenv $(VIRTUALENV_DIR)

$(DEPS_UPTODATE): setup.py $(VIRTUALENV_BIN)/pip requirements.txt dev-requirements.txt
	$(VIRTUALENV_BIN)/pip install -e .
	$(VIRTUALENV_BIN)/pip install -r requirements.txt
	$(VIRTUALENV_BIN)/pip install -r dev-requirements.txt
	touch $(DEPS_UPTODATE)

deps: $(DEPS_UPTODATE)

$(VIRTUALENV_BIN)/flake8 $(VIRTUALENV_BIN)/py.test: $(DEPS_UPTODATE)

.uptodate: prom-run Dockerfile
	docker build -t weaveworks/kubediff .
	docker tag weaveworks/kubediff:latest weaveworks/kubediff:$(IMAGE_VERSION)
	docker tag weaveworks/kubediff:$(IMAGE_VERSION) quay.io/weaveworks/kubediff:$(IMAGE_VERSION)
	docker tag weaveworks/kubediff:latest quay.io/weaveworks/kubediff:latest

prom-run: vendor/github.com/tomwilkie/prom-run/*.go
	CGO_ENABLED=0 GOOS=linux go build ./vendor/github.com/tomwilkie/prom-run

lint: $(VIRTUALENV_BIN)/flake8
	$(VIRTUALENV_BIN)/flake8 kubediff

test: $(VIRTUALENV_BIN)/py.test
	$(VIRTUALENV_BIN)/py.test --junitxml=$(JUNIT_XML)

clean:
	rm -f prom-run .uptodate $(DEPS_UPTODATE)
	rm -rf kubedifflib.egg-info
	find . name '*.pyc' | xargs rm -f

clean-deps:
	rm -rf $(VIRTUALENV_DIR)
	rm -f $(DEPS_UPTODATE)
