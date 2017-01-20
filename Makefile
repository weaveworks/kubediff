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
	go get ./vendor/github.com/tomwilkie/prom-run
	CGO_ENABLED=0 GOOS=linux go build -ldflags "-s" -a -installsuffix cgo -o $@ ./vendor/github.com/tomwilkie/prom-run

lint:
	flake8 kubediff

clean:
	rm -f prom-run .uptodate
