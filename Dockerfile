FROM alpine:3.5
MAINTAINER Weaveworks Inc <help@weave.works>
WORKDIR /

RUN apk update && \
   apk add py2-pip curl make && \
   curl -o /bin/kubectl https://storage.googleapis.com/kubernetes-release/release/v1.2.4/bin/linux/amd64/kubectl && \
   chmod u+x /bin/kubectl

COPY . /tmp/kubediff/
RUN pip install /tmp/kubediff/
RUN pip install -r /tmp/kubediff/requirements.txt

COPY prom-run kubediff compare-images /
EXPOSE 80
ENTRYPOINT ["/prom-run"]
