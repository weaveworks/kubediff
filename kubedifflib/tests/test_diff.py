import copy

import random

from hypothesis import given
from hypothesis.strategies import integers, lists, text

from kubedifflib._diff import diff_lists, list_subtract


@given(path=text(), xs=lists(integers()))
def test_diff_lists_equal(path, xs):
    """No difference between a list and itself."""
    assert list(diff_lists(path, xs, xs)) == []


@given(path=text(), xs=lists(integers()))
def test_same_list_shuffled_is_not_different(path, xs):
    """No difference between two lists with same values in different order."""
    ys = list(xs)
    random.shuffle(ys)
    assert list(diff_lists(path, xs, ys)) == []


@given(path=text(), xs=lists(lists(integers())))
def test_same_list_shuffled_is_not_different_nested(path, xs):
    """No difference between two lists with same values in different order.

    This variant is for when there are nested lists, to catch loop / mutation
    issues.
    """
    ys = copy.deepcopy(xs)
    random.shuffle(ys)
    assert list(diff_lists(path, xs, ys)) == []


@given(path=text(), base=lists(integers()), extension=lists(integers()))
def test_added_items_appear_in_diff(path, base, extension):
    xs = list(base)
    xs.extend([None] * len(extension))
    ys = list(base)
    ys.extend(extension)
    assert len(list(diff_lists(path, xs, ys))) == len(extension)


@given(xs=lists(integers()))
def test_list_subtract_same_list(xs):
    assert list(list_subtract(xs, xs)) == []
    ys = list(xs)
    random.shuffle(ys)
    assert list(list_subtract(xs, ys)) == []


@given(xs=lists(integers()), ys=lists(integers()))
def test_list_subtract_recover(xs, ys):
    missing = list_subtract(xs, ys)
    zs = list(ys)
    zs.extend([xs[i] for i in missing])
    assert list(list_subtract(xs, zs)) == []


def two_lists_of_same_size(generator):
    """Generate two lists of the same length."""
    return lists(generator).map(split_list)


def split_list(xs):
    """Split a list into two lists of equal length."""
    midpoint, remainder = divmod(len(xs), 2)
    if remainder:
        xs = xs[:-1]
    return xs[:midpoint], xs[midpoint:]


@given(path=text(), items=two_lists_of_same_size(integers()))
def test_diff_lists_doesnt_mutate_inputs(path, items):
    xs, ys = items
    orig_xs = list(xs)
    orig_ys = list(ys)
    diff_lists(path, xs, ys)
    assert xs == orig_xs and ys == orig_ys


@given(path=text(), items=two_lists_of_same_size(lists(integers())))
def test_diff_lists_doesnt_mutate_inputs_nested_lists(path, items):
    xs, ys = items
    orig_xs = copy.deepcopy(xs)
    orig_ys = copy.deepcopy(ys)
    diff_lists(path, xs, ys)
    assert xs == orig_xs and ys == orig_ys


@given(items=two_lists_of_same_size(integers()))
def test_two_lists_of_same_size_generator(items):
    """two_lists_of_same_size returns two lists of the same length."""
    xs, ys = items
    assert len(xs) == len(ys)
