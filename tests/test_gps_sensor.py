import pytest
from pytesting_api import global_test_variables # pylint: disable=e0401


def test_example():
    assert 1 + 1 == 2

def test_example2():
    assert 1 + 1 == 3

def test_fixture():
    assert global_test_variables.coms.get_test() == "testing"