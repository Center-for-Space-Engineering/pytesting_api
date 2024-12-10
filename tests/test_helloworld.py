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
    print(f" Group 1 params: {global_test_variables.tests_parameters_dict['group1']}")
    assert 1 + 1 == 2

@pytest.mark.group2
def test_other_test():
    '''
        Failed unit test
    '''
    print(f" Group 2 params: {global_test_variables.tests_parameters_dict['group2']}")
    assert 4 + 1 == 3

@pytest.mark.group3
def test_example_coms():
    '''
        Example of how to call the coms object
    '''
    assert global_test_variables.coms.get_test() == "testing"
