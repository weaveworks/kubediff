FROM alpine:3.18.3
WORKDIR /

RUN apk update && \
   apk add python3 py3-pip curl && \
   curl -o /bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.21.5/bin/linux/amd64/kubectl && \
   chmod u+x /bin/kubectl

COPY . /tmp/kubediff/
RUN pip3 install /tmp/kubediff/
RUN pip3 install -r /tmp/kubediff/requirements.txt

COPY prom-run kubediff compare-images /
EXPOSE 80
ENTRYPOINT ["/prom-run"]

ARG revision
LABEL maintainer="Weaveworks <help@weave.works>" \
   org.opencontainers.image.title="kubediff" \
   org.opencontainers.image.source="https://github.com/weaveworks/kubediff" \
   org.opencontainers.image.revision="${revision}" \
   org.opencontainers.image.vendor="Weaveworks"
