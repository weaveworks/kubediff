from functools import partial
import collections
import json
import os
import subprocess
import yaml

from ._kube import (
  KubeObject,
  iter_files,
)


class Difference(object):
  """An observed difference."""

  def __init__(self, message, path, *args):
    self.message = message
    self.path = path
    self.args = args

  def to_text(self):
    message = self.message % self.args
    if self.path is None:
      return message
    return '%s: %s' % (self.path, message)


def different_lengths(path, want, have):
  return Difference("Unequal lengths: %d != %d", path, len(want), len(have))

missing_item = partial(Difference, "'%s' missing")
not_equal = partial(Difference, "'%s' != '%s'")


def diff_lists(path, want, have):
  if not len(want) == len(have):
    yield different_lengths(path, want, have)

  for i, (want_v, have_v) in enumerate(zip(want, have)):
     for difference in diff("%s[%d]" % (path, i), want_v, have_v):
       yield difference


def diff_dicts(path, want, have):
  for k, want_v in want.iteritems():
    key_path = "%s.%s" % (path, k)

    if k not in have:
      yield missing_item(path, k)
    else:
      for difference in diff(key_path, want_v, have[k]):
        yield difference


def diff(path, want, have):
  if isinstance(want, dict):
    for difference in diff_dicts(path, want, have):
      yield difference

  elif isinstance(want, list):
    for difference in diff_lists(path, want, have):
      yield difference

  else:
    if not want == have:
      yield not_equal(path, want, have)


def check_file(printer, path, kubeconfig=None):
  """Check YAML file 'path' for differences.

  :param printer: Where we report differences to.
  :param str path: The YAML file to test.
  :param str kubeconfig: Path to a Kubernetes configuration file.
      If None, we use the default.
  :return: Number of differences found.
  """
  with open(path, 'r') as stream:
    expected = yaml.load(stream)

  kube_obj = KubeObject.from_dict(expected)

  printer.add(path, kube_obj)

  try:
    running = kube_obj.get_from_cluster(kubeconfig=kubeconfig)
  except subprocess.CalledProcessError, e:
    printer.diff(path, Difference(e.output, None))
    return 0

  differences = 0
  for difference in diff("", expected, running):
    differences += 1
    printer.diff(kube_obj, difference)
  return differences


class StdoutPrinter(object):
  def add(self, _, kube_obj):
    print "Checking %s '%s'" % (kube_obj.kind, kube_obj.namespaced_name)

  def diff(self, _, difference):
    print " *** " + difference.to_text()

  def finish(self):
    pass


class JSONPrinter(object):
  def __init__(self):
    self.data = collections.defaultdict(list)

  def add(self, path, kube_obj):
    pass

  def diff(self, path, difference):
    self.data[path].append(difference.to_text())

  def finish(self):
    print json.dumps(self.data, sort_keys=True, indent=2, separators=(',', ': '))


def check_files(paths, printer, kubeconfig=None):
  """Check all files in 'paths' for differences to a Kubernetes cluster.

  :param printer: Where differences are reported to as they are found.
  :param str kubeconfig: Path to a kubeconfig file for the cluster to diff
      against.
  :return: True if there are differences, False otherwise.
  """
  differences = 0
  for path in iter_files(paths):
    _, extension = os.path.splitext(path)
    if extension != ".yaml":
      continue
    differences += check_file(printer, path, kubeconfig=kubeconfig)

  printer.finish()
  return bool(differences)
