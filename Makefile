all: .uptodate

.uptodate: prom-run Dockerfile
	docker build -t weaveworks/kubediff .

prom-run: vendor/github.com/tomwilkie/prom-run/*.go
	GOOS=linux go build -o $@ ./vendor/github.com/tomwilkie/prom-run

clean:
	rm -f prom-run .uptodate
