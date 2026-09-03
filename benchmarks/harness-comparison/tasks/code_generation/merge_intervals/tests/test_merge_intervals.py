import pytest
from solution import merge_intervals


def test_basic_merge():
    assert merge_intervals([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]


def test_touching_intervals():
    assert merge_intervals([[1, 4], [4, 5]]) == [[1, 5]]


def test_empty():
    assert merge_intervals([]) == []


def test_single():
    assert merge_intervals([[1, 4]]) == [[1, 4]]


def test_all_overlap():
    assert merge_intervals([[1, 10], [2, 6], [3, 5]]) == [[1, 10]]


def test_no_overlap():
    assert merge_intervals([[1, 2], [3, 4], [5, 6]]) == [[1, 2], [3, 4], [5, 6]]


def test_negative_numbers():
    assert merge_intervals([[-5, -2], [-3, 0], [1, 3]]) == [[-5, 0], [1, 3]]


def test_unsorted_input():
    assert merge_intervals([[8, 10], [1, 3], [2, 6], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]


def test_contained_interval():
    assert merge_intervals([[1, 10], [3, 5]]) == [[1, 10]]


def test_large_numbers():
    assert merge_intervals([[1000000, 2000000], [1500000, 3000000]]) == [[1000000, 3000000]]
