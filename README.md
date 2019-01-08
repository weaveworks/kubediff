# Kubediff

Kubediff is a tool for Kubernetes to show you the differences between your
running configuration and your version controlled configuration.

Kubediff can be run from the command line:

    $ ./kubediff
    Usage: kubediff [options] <dir/file>...

    Compare yaml files in <dir> to running state in kubernetes and print the
    differences.  This is useful to ensure you have applied all your changes to the
    appropriate environment.  This tools runs kubectl, so unless your
    ~/.kube/config is configured for the correct environment, you will need to
    supply the kubeconfig for the appropriate environment.

    Options:
      -h, --help            show this help message and exit
      --kubeconfig=KUBECONFIG
                            path to kubeconfig
      --namespace=NAMESPACE
                            the namespace to assume for objects where it's not
                            specified (default = Kubernetes default for current
                            context)
      -j, --json            output in json format
      --no-error-on-diff    don't exit with 2 if diff exists

For example:

    $ ./kubediff k8s
    Checking ReplicationController 'kubediff'
     *** .spec.template.spec.containers[0].args[0]: '-repo=https://github.com/weaveworks/kubediff' != '-repo=https://github.com/<your github repo>'
    Checking Secret 'kubediff-secret'
    Checking Service 'kubediff'

Make sure the dependencies are installed first:

    $ pip install -r requirements.txt

Kubediff can also be run as a service on Kubernetes, periodically downloading the
latest configuration from Github, comparing it to the running configuration.  In
this mode Kubediff will also offers a very simple UI showing the output and
export the result to Prometheus, all courtesy to [prom-run](https://github.com/tomwilkie/prom-run).

To deploy to Kubernetes, you much first make a copy of the YAML files in `k8s`
and update the following fields:

- `kubediff-rc.yaml` the first argument to git-sync must be the location of
  the config repo, and the last argument to kubediff must the the location
  in this repo of your config.
- `kubediff-secret.yaml` the username and password must be set to valid
  [github OAuth token](https://developer.github.com/guides/managing-deploy-keys/#https-cloning-with-oauth-tokens).

Once you have updated the config, the following commands should bring up
the service:

    $ kubectl create -f k8s
    replicationcontroller "kubediff" created
    secret "kubediff-secret" created
    service "kubediff" created

And to view the UI, run the follow command and go to http://localhost:4040

    $ kubectl port-forward $(kubectl get pod --selector=name=kubediff -o jsonpath={.items..metadata.name}) 4040:80

![Kubediff Screenshot](/imgs/screenshot.png)

This service exports the exit code of the kubediff as a Prometheus metric;
a suitable alert can be setup for persistent differences:

    ALERT Kubediff
      IF          max(command_exit_code{job="kubediff"}) != 0
      FOR         2h
      LABELS      { severity="warning" }
      ANNOTATIONS {
        summary = "Kubediff has detected a difference in running config.",
        description = "Kubediff has detected a difference in running config.",
      }

These alerts can be sent to Slack, for example:

![Slack Alert](/imgs/alert.png)

## compare-images

To quickly see how two sets of configurations differ, purely in terms of
images:

```
$ ./compare-images ../service-conf/k8s/dev/ ../service-conf/k8s/prod/
Image                          dev                   prod
-----------------------------  --------------------  --------------------
quay.io/weaveworks/grafana     master-0fc7cc2        master-08fd09d
quay.io/weaveworks/prometheus  master-0fc7cc2        master-4fb2aed
quay.io/weaveworks/ui-server   master-2899c36        master-45d67b3
tomwilkie/prometheus           frankenstein-8a5ec1b  frankenstein-ebe5808
weaveworks/scope               master-1a1021c        master-14d0e4e
```

## Build

```
mkdir -p $GOPATH/src/github.com/prometheus && cd "$_"
git clone git@github.com:prometheus/client_golang.git
mkdir -p $GOPATH/src/github.com/weaveworks && cd "$_"
git clone git@github.com:weaveworks/kubediff.git
cd kubediff
make
```

## <a name="help"></a>Getting Help

If you have any questions about, feedback for or problems with `kubediff`:

- Invite yourself to the <a href="https://slack.weave.works/" target="_blank">Weave Users Slack</a>.
- Ask a question on the [#general](https://weave-community.slack.com/messages/general/) slack channel.
- [File an issue](https://github.com/weaveworks/kubediff/issues/new).

Your feedback is always welcome!
