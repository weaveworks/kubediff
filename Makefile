all: .uptodate

IMAGE_VERSION := $(shell git rev-parse --abbrev-ref HEAD)-$(shell git rev-parse --short HEAD)

.uptodate: prom-run Dockerfile
	docker build -t weaveworks/kubediff .
	docker tag weaveworks/kubediff:latest weaveworks/kubediff:$(IMAGE_VERSION)

prom-run: vendor/github.com/tomwilkie/prom-run/*.go
	go get ./vendor/github.com/tomwilkie/prom-run
	GOOS=linux go build -o $@ ./vendor/github.com/tomwilkie/prom-run

clean:
	rm -f prom-run .uptodate
