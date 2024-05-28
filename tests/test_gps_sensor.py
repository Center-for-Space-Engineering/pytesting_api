'''
    dummy unit tests
'''

import pytest #pylint: disable=w0611
from pytesting_api import global_test_variables # pylint: disable=e0401


def test_example():
    '''
        Simple example
    '''
    assert 1 + 1 == 2

def test_example2():
    '''
        Failed unit test
    '''
    assert 1 + 1 == 3

def test_fixture():
    '''
        Example of how to call the coms object
    '''
    assert global_test_variables.coms.get_test() == "testing"
