import pytest
from unittest.mock import MagicMock, patch
import time

from pytesting_api import global_test_variables
from logging_system_display_python_api.messageHandler import messageHandler

@pytest.fixture
def patch_sleep():
    sleep_patch = patch('time.sleep')
    sleep_patch.start()
    yield
    sleep_patch.stop()

@pytest.fixture
def patch_coms():
    get_return_patch = patch.object(messageHandler, 'get_return')
    send_request_patch = patch.object(messageHandler, 'send_request')
    get_return_patch.start()
    send_request_patch.start()
    yield
    get_return_patch.stop()
    send_request_patch.stop()

@pytest.fixture
def setup_mocks(patch_sleep, patch_coms):
    yield

@pytest.mark.global_test_variables_tests
def test_get_last_idx(setup_mocks):
    # Immediate return
    mock_coms = messageHandler()
    mock_coms.send_request.return_value = 1
    mock_coms.get_return.return_value = 42

    tester = global_test_variables
    tester.coms = mock_coms

    result = tester.get_last_idx('Johnny')

    assert result == 42
    mock_coms.get_return.assert_called_once()

    # Return after sleep
    mock_coms.get_return.side_effect = [None, None, 42]

    result = tester.get_last_idx('Peter')

    assert time.sleep.call_count == 2
    assert mock_coms.get_return.call_count == 4

@pytest.mark.global_test_variables_tests
def test_save_data_to_db(setup_mocks):
    mock_coms = messageHandler()
    tester = global_test_variables
    tester.coms = mock_coms
    tester.db_name = "Kade"

    tester.save_data_to_db('Big Justin', ['data'], 'thread')
    mock_coms.send_request.assert_called_with('Kade', ['save_data_group', 'Big Justin', ['data'], 'thread'])

@pytest.mark.global_test_variables_tests
def test_get_data_from_data_base(setup_mocks):
    mock_coms = messageHandler()
    mock_coms.send_request.return_value = 2
    mock_coms.get_return.return_value = 69

    tester = global_test_variables
    tester.coms = mock_coms

    result = tester.get_data_from_data_base('Todd', 0, 100)

    assert result == 69
    mock_coms.get_return.assert_called_once()

    # Return after sleep
    mock_coms.get_return.side_effect = [None, None, 69]

    result = tester.get_data_from_data_base('Rowan', 3, 14)

    assert time.sleep.call_count == 2
    assert mock_coms.get_return.call_count == 4
