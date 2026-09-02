import pytest
from binary_search import binary_search


def test_found_middle():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2


def test_found_start():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0


def test_found_end():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4


def test_not_found():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1


def test_not_found_middle():
    assert binary_search([1, 2, 3, 4, 5], 0) == -1


def test_empty_list():
    assert binary_search([], 1) == -1


def test_single_element_found():
    assert binary_search([5], 5) == 0


def test_single_element_not_found():
    assert binary_search([5], 3) == -1


def test_two_elements_found_first():
    assert binary_search([1, 2], 1) == 0


def test_two_elements_found_second():
    assert binary_search([1, 2], 2) == 1


def test_large_list():
    arr = list(range(1000))
    assert binary_search(arr, 500) == 500
    assert binary_search(arr, 999) == 999
    assert binary_search(arr, 0) == 0
    assert binary_search(arr, 1000) == -1


def test_negative_numbers():
    assert binary_search([-10, -5, 0, 5, 10], -5) == 1
    assert binary_search([-10, -5, 0, 5, 10], -10) == 0


def test_duplicates():
    arr = [1, 2, 2, 2, 3, 4]
    result = binary_search(arr, 2)
    assert result in [1, 2, 3]  # Any valid index of 2
    assert arr[result] == 2


def test_even_length():
    assert binary_search([1, 2, 3, 4], 2) == 1
    assert binary_search([1, 2, 3, 4], 3) == 2
