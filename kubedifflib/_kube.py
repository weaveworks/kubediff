# -*- coding: utf-8 -*-

from __future__ import (division, absolute_import, print_function,
                        unicode_literals)
import logging
import yaml
import subprocess
import os
import attr
from builtins import object


def iter_files(paths):
    """Yield absolute paths to all the files in 'paths'.

    'paths' is expected to be an iterable of paths to files or directories.
    Paths to files are yielded as is, paths to directories are recursed into.

    Equivalent to ``find "$paths[@]" -type f``.
    """
    # XXX: Copied from service/monitoring/lint
    for path in paths:
        if os.path.isfile(path):
            yield path
        else:
            for root, _, filenames in os.walk(path):
                for filename in filenames:
                    yield os.path.join(root, filename)


@attr.s
class KubeObject(object):
    """A Kubernetes object."""

    namespace = attr.ib()
    kind = attr.ib()
    name = attr.ib()
    data = attr.ib()

    @classmethod
    def from_dict(cls, data, namespace=""):
        """Construct a 'KubeObject' from a dictionary of Kubernetes data.

        :param dict data: Kubernetes object data; might be obtained from a Kubernetes cluster,
            or decoded from a YAML config file.
        :param str namespace: the namespace to use if it's not defined in the object definition
        """

        try:
            kind = data["kind"]
            if kind.lower().endswith("list"):
                for obj in data["items"]:
                    for kube_obj in KubeObject.from_dict(obj, namespace=namespace):
                        yield kube_obj
            else:
                # Transform from e.g. "apps/v1" to what kubectl expects, e.g. "deployment.v1.apps"
                # From https://kubernetes.io/docs/reference/generated/kubectl/kubectl-commands#get:
                # "To use a specific API version, fully-qualify the resource,
                # version, and group (for example: 'jobs.v1.batch/myjob')."
                api_version_parts = data["apiVersion"].split("/")
                api_version_parts.reverse()
                if len(api_version_parts) < 2:
                    api_version_parts.append("")  # top-level group is blank
                kind = kind + "." + ".".join(api_version_parts)
                name = data["metadata"]["name"]
                namespace = data["metadata"].get("namespace", namespace)
                yield cls(namespace, kind, name, data)
        except KeyError as e:
            logging.error("Failed to parse Kubernetes object: {0}".format(data))
            logging.error("Missing key: {0}".format(e))

    @property
    def namespaced_name(self):
        return "%s/%s" % (self.namespace, self.name)

    def get_from_cluster(self, kubeconfig=None, context=None):
        """Fetch data for this object from a Kubernetes cluster.

        :param str kubeconfig: Path to a Kubernetes configuration file. If None,
            fetches data from the default cluster.
        :return: A dict of data for this Kubernetes object.
        """
        args = ["--namespace=%s" % self.namespace, "-o=yaml"]
        if kubeconfig is not None:
            args.append("--kubeconfig=%s" % kubeconfig)
        if context is not None:
            args.append("--context=%s" % context)

        running = subprocess.check_output(["kubectl", "get"] + args + [self.kind, self.name], stderr=subprocess.STDOUT)
        return yaml.safe_load(running)
