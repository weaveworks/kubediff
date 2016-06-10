FROM alpine
MAINTAINER Weaveworks Inc <help@weave.works>
RUN apk update && \
   apk add py-yaml curl && \
   curl -o /bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.2.4/bin/linux/amd64/kubectl && \
   chmod u+x /bin/kubectl
WORKDIR /
COPY vendor/github.com/tomwilkie/prom-run/prom-run /
EXPOSE 80
ENTRYPOINT ["/prom-run"]
