import copy

import random

from hypothesis import given, example
from hypothesis.strategies import integers, lists, text, fixed_dictionaries, sampled_from, none, one_of

from kubedifflib._diff import diff_lists, list_subtract, Difference
from kubedifflib._kube import KubeObject


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


def kube_spec():
    """Generate a random kubernetes spec."""
    return fixed_dictionaries({
        "name": text()
    })


def kube_obj():
    """Generate a random Kubernetes object."""
    return fixed_dictionaries({
        "apiVersion": sampled_from(["v1", "v1beta1", "extensions/v1"]),
        "kind": sampled_from(["Namespace", "Pod", "Job", "CronJob", "Deployment"]),
        "metadata": fixed_dictionaries({
            "name": text()
        }),
        "spec": one_of(none(), kube_spec())
    })


def kube_list():
    """Generate a Kubernetes List type with a set of objects."""
    return fixed_dictionaries({
        "apiVersion": sampled_from(["v1", "v1beta1"]),
        "kind": sampled_from(["List"]),
        "items": lists(kube_obj(), min_size=1)
    })


@given(data=kube_list())
def test_from_dict_kubernetes_list_type(data):
    """KubeObject.from_dict parses kubernetes lists by returning each of the
    items in the list."""
    assert [kube_obj.data for kube_obj in KubeObject.from_dict(data)] == data['items']


@given(data=kube_obj())
def test_from_dict_kubernetes_obj_type(data):
    """KubeObject.from_dict parses regular kubernetes objects."""
    assert [kube_obj.data for kube_obj in KubeObject.from_dict(data)] == [data]


@given(path=text(), kind=text())
def test_difference_no_args(path, kind):
    """Difference.to_text works as expected when no args passed."""
    d = Difference("Message", path)
    assert d.to_text(kind) == path + ": Message"


@given(path=text(), kind=text(), arg1=text(), arg2=one_of(text(), none()))
@example("somepath", "Secret", "foo", None)
def test_difference_two_args(path, kind, arg1, arg2):
    """Difference.to_text works when two args passed, that may be 'none'."""
    d = Difference("Message %s %s", path, arg1, arg2)
    assert d.to_text(kind) != ""
