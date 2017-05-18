.PHONY: all clean lint
.DEFAULT_GOAL := all

all: .uptodate

IMAGE_VERSION := $(shell ./tools/image-tag)

.uptodate: prom-run Dockerfile
	docker build -t weaveworks/kubediff .
	docker tag weaveworks/kubediff:latest weaveworks/kubediff:$(IMAGE_VERSION)
	docker tag weaveworks/kubediff:$(IMAGE_VERSION) quay.io/weaveworks/kubediff:$(IMAGE_VERSION)
	docker tag weaveworks/kubediff:latest quay.io/weaveworks/kubediff:latest

prom-run: vendor/github.com/tomwilkie/prom-run/*.go
	CGO_ENABLED=0 GOOS=linux go build ./vendor/github.com/tomwilkie/prom-run

lint:
	flake8 kubediff

test:
	py.test

clean:
	rm -f prom-run .uptodate
