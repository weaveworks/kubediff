#!/usr/bin/env python

from builtins import map
from builtins import object
from future.utils import viewitems
import attr
import json
import optparse
import os
from pprint import pformat
import sys
import yaml

from ._kube import (
  KubeObject,
  iter_files,
)


def load_config(*paths):
  """Load configuration for a Kubernetes environment from disk.

  :return: a dict mapping KubeObjects to data.
  """
  objects = {}
  for path in iter_files(paths):
    _, extension = os.path.splitext(path)
    if extension not in [".yaml", ".yml"]:
      continue
    with open(path, 'r') as stream:
      data = yaml.safe_load(stream)
    kube_obj = KubeObject.from_dict(data)
    objects[kube_obj] = data
  return objects


class InvalidImageName(Exception):
  """Raised when there's an invalid image name in configuration."""


@attr.s
class Image(object):
  """A Docker image name."""
  name = attr.ib()
  label = attr.ib()

  @classmethod
  def parse(cls, image_name):
    try:
      [name, label] = image_name.split(':', 1)
    except ValueError:
      name = image_name
      label = "latest"
    return cls(name, label)


def get_differing_images(source_env, target_env):
  """Return the images that differ between Kubernetes environments.

  :param Dict[KubeObject, Dict] source_env: The Kubernetes objects in the
      source environment.
  :param Dict[KubeObject, Dict] target_env: The Kubernetes objects in the
      target environment.
  :return: A dictionary mapping image names to source label and target label.
  :rtype: Dict[str, (str, str)]
  """
  source_objs = frozenset(source_env)
  target_objs = frozenset(target_env)
  # XXX: What about missing objects?
  diffs = {}
  for obj in source_objs & target_objs:
    source_images = list(map(Image.parse, sorted(iter_images(source_env[obj]))))
    target_images = list(map(Image.parse, sorted(iter_images(target_env[obj]))))
    while source_images and target_images:
      source, target = source_images[0], target_images[0]
      if source.name == target.name:
        if source.label != target.label:
          diffs[source.name] = (source.label, target.label)
        source_images, target_images = source_images[1:], target_images[1:]
      elif source.name < target.name:
        # XXX: What about images that are in the source env but not in the
        # target env?
        source_images, target_images = source_images[1:], target_images
      else:
        # XXX: What about images that are in the target env but not in the
        # source env?
        source_images, target_images = source_images, target_images[1:]
  return diffs


def iter_images(data):
  """Yield the names of all the images in 'data'.

  Expects 'data' to be Kubernetes object.
  """
  if isinstance(data, dict):
    for (key, value) in viewitems(data):
      if key == 'image':
        yield value
      else:
        for image in iter_images(value):
          yield image
  elif isinstance(data, list):
    for item in data:
      for image in iter_images(item):
        yield image
  else:
    pass
