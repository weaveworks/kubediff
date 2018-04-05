import attr
import os
import subprocess
import yaml


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
      for root, _dirs, filenames in os.walk(path):
        for filename in filenames:
          yield os.path.join(root, filename)


@attr.s
class KubeObject(object):
  """A Kubernetes object."""

  namespace = attr.ib()
  kind = attr.ib()
  name = attr.ib()

  @classmethod
  def from_dict(cls, data):
    """Construct a 'KubeObject' from a dictionary of Kubernetes data.

    'data' might be obtained from a Kubernetes cluster, or decoded from a YAML
    config file.
    """
    kind = data["kind"]
    name = data["metadata"]["name"]
    namespace = data["metadata"].get("namespace", "")
    return cls(namespace, kind, name)

  @property
  def namespaced_name(self):
    return "%s/%s" % (self.namespace, self.name)

  def get_from_cluster(self, kubeconfig=None, context=None, namespace=None):
    """Fetch data for this object from a Kubernetes cluster.

    :param str kubeconfig: Path to a Kubernetes configuration file. If None,
        fetches data from the default cluster.
    :param str context: Name of Kubernetes context to use. If None,
        fetches data from the default context.
    :param str namespace: Name of Kubernetes namespace to use. If None,
        fetches data from the default context's namespace.
    :return: A dict of data for this Kubernetes object.
    """
    args = ["--namespace=%s" % self.namespace, "-o=yaml"]
    if kubeconfig is not None:
      args.append("--kubeconfig=%s" % kubeconfig)
    if context is not None:
      args.append("--context=%s" % context)
    if namespace is not None:
      args.append("--namespace=%s" % namespace)

    running = subprocess.check_output(["kubectl", "get"] + args + [self.kind, self.name], stderr=subprocess.STDOUT)
    return yaml.load(running)
