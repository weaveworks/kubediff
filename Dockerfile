FROM alpine:3.9
WORKDIR /

RUN apk update && \
   apk add py2-pip curl && \
   curl -o /bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.13.3/bin/linux/amd64/kubectl && \
   chmod u+x /bin/kubectl

COPY . /tmp/kubediff/
RUN pip install /tmp/kubediff/
RUN pip install -r /tmp/kubediff/requirements.txt

COPY prom-run kubediff compare-images /
EXPOSE 80
ENTRYPOINT ["/prom-run"]

ARG revision
LABEL maintainer="Weaveworks <help@weave.works>" \
      org.opencontainers.image.title="kubediff" \
      org.opencontainers.image.source="https://github.com/weaveworks/kubediff" \
      org.opencontainers.image.revision="${revision}" \
      org.opencontainers.image.vendor="Weaveworks"
