"""Routines for comparing Kubernetes deployments and config."""

from ._diff import (
  check_files,
  JSONPrinter,
  StdoutPrinter
)

__all__ = [
  check_files,
  JSONPrinter,
  StdoutPrinter
]
