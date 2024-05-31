'''
    dummy unit tests
'''

import pytest #pylint: disable=w0611
from pytesting_api import global_test_variables # pylint: disable=e0401

@pytest.mark.group1
def test_not_this_test():
    '''
        Simple example
    '''
    print('Hello world')
    assert 2 + 2 == 4

@pytest.mark.group2
def test_other_test():
    '''
        Failed unit test
    '''
    assert 1 + 1 == 3

@pytest.mark.group3
def test_example_coms():
    '''
        Example of how to call the coms object
    '''
    assert global_test_variables.coms.get_test() == "testing"
