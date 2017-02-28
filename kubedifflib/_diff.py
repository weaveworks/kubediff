from functools import partial
import collections
import difflib
import json
import os
import subprocess
import sys
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


def diff_not_equal(path, want, have):
  want_lines, have_lines = want.splitlines(), have.splitlines()
  diff = "\n".join(difflib.unified_diff(want_lines, have_lines, fromfile=path, tofile="running", lineterm=""))
  return Difference("Diff:\n%s", path, diff)


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


def normalize(value):
  if isinstance(value, int):
    return str(value)
  if value == [] or value == {}:
    return None
  return value


def diff(path, want, have):
  want = normalize(want)
  have = normalize(have)
  if isinstance(want, dict) and isinstance(have, dict):
    for difference in diff_dicts(path, want, have):
      yield difference

  elif isinstance(want, list) and isinstance(have, list):
    for difference in diff_lists(path, want, have):
      yield difference

  elif isinstance(want, basestring) and isinstance(have, basestring):
    if want != have:
      if "\n" in want:
        yield diff_not_equal(path, want, have)
      else:
        yield not_equal(path, want, have)

  elif want != have:
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
    expected = yaml.load_all(stream)

    differences = 0
    for data in expected:
      kube_obj = KubeObject.from_dict(data)

      printer.add(path, kube_obj)

      try:
        running = kube_obj.get_from_cluster(kubeconfig=kubeconfig)
      except subprocess.CalledProcessError, e:
        printer.diff(path, Difference(e.output, None))
        differences += 1
        continue


      for difference in diff("", data, running):
        differences += 1
        printer.diff(path, difference)
  return differences


class StdoutPrinter(object):
  def add(self, _, kube_obj):
    print "Checking %s '%s'" % (kube_obj.kind, kube_obj.namespaced_name)

  def diff(self, _, difference):
    print " *** " + difference.to_text()

  def finish(self):
    pass


class QuietTextPrinter(object):
  """Only output if there's a difference."""

  def __init__(self, stream=None):
    self._stream = stream if stream else sys.stdout
    self._current = None

  def _write(self, msg, *args):
    self._stream.write(msg % args)
    self._stream.write('\n')
    self._stream.flush()

  def add(self, _, kube_obj):
    self._current = kube_obj

  def diff(self, _, difference):
    if self._current:
      self._write('## %s (%s)', self._current.namespaced_name, self._current.kind)
    else:
      self._write('## UNKNOWN')
    self._write('')
    self._write(difference.to_text())

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
