import pytest
from unittest.mock import MagicMock, patch
import time

from pytesting_api import global_test_variables
from logging_system_display_python_api.messageHandler import messageHandler

@pytest.fixture
def patch_sleep():
    sleep_patch = patch('time.sleep')
    mock_sleep = sleep_patch.start()
    yield mock_sleep
    sleep_patch.stop()

@pytest.fixture
def patch_coms():
    mock_coms_obj = MagicMock(send_request=MagicMock(), get_return=MagicMock())
    yield mock_coms_obj

@pytest.mark.global_test_variables_tests
def test_get_last_idx(patch_sleep, patch_coms):
    # Immediate return
    patch_coms.send_request.return_value = 1
    patch_coms.get_return.return_value = 42

    tester = global_test_variables
    tester.coms = patch_coms

    result = tester.get_last_idx('Johnny')

    assert result == 42
    patch_coms.get_return.assert_called_once()

    # Return after sleep
    patch_coms.get_return.side_effect = [None, None, 42]

    result = tester.get_last_idx('Peter')

    assert patch_sleep.call_count == 2
    assert patch_coms.get_return.call_count == 4

@pytest.mark.global_test_variables_tests
def test_save_data_to_db(patch_coms):
    tester = global_test_variables
    tester.coms = patch_coms
    tester.db_name = "Kade"

    tester.save_data_to_db('Big Justin', ['data'], 'thread')
    patch_coms.send_request.assert_called_with('Kade', ['save_data_group', 'Big Justin', ['data'], 'thread'])

@pytest.mark.global_test_variables_tests
def test_get_data_from_data_base(patch_coms, patch_sleep):
    patch_coms.send_request.return_value = 2
    patch_coms.get_return.return_value = 69

    tester = global_test_variables
    tester.coms = patch_coms

    result = tester.get_data_from_data_base('Todd', 0, 100)

    assert result == 69
    patch_coms.get_return.assert_called_once()

    # Return after sleep
    patch_coms.get_return.side_effect = [None, None, 69]

    result = tester.get_data_from_data_base('Rowan', 3, 14)

    assert patch_sleep.call_count == 2
    assert patch_coms.get_return.call_count == 4
