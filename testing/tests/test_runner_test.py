import os
import pytest
from unittest.mock import MagicMock, patch
from itertools import cycle
import threading
import subprocess
import sys

from pytesting_api.test_runner import test_runner
from pytesting_api import global_test_variables
from pytesting_api import test_runner as test_runner_class
from logging_system_display_python_api.messageHandler import messageHandler

DEBUG = False

##### Setup #####
@pytest.fixture
def patch_os():
    mock_os_obj = MagicMock(path=MagicMock(exists=MagicMock(), join=MagicMock(return_value=''), getmtime=abs), makedirs=MagicMock(), remove=MagicMock())
    os_patcher = patch('pytesting_api.test_runner.os', mock_os_obj)
    mock_os_class = os_patcher.start()
    yield mock_os_class
    os_patcher.stop()

@pytest.fixture
def patch_coms():
    mock_coms_obj = MagicMock(send_request=MagicMock())
    global_test_var_patcher = patch.object(global_test_variables, 'coms', mock_coms_obj)
    global_test_var_patcher.start()
    yield mock_coms_obj
    global_test_var_patcher.stop()

@pytest.fixture
def patch_yaml():
    mock_yaml_obj = MagicMock(safe_load=MagicMock())
    yaml_patcher = patch('pytesting_api.test_runner.yaml', mock_yaml_obj)
    yield yaml_patcher.start()
    yaml_patcher.stop()

##### Tests #####
@pytest.mark.test_runner_tests
def test_init(patch_os, patch_coms, patch_yaml):
    # Basic use
    patch_os.path.exists.return_value = True

    runner = test_runner(failed_test_path='pytesting_api/testing/files/test_failed_file', passed_test_path='pytesting_api/testing/files/test_passed_file')
    
    patch_yaml.safe_load.assert_called_once()
    patch_coms.send_request.assert_called_with('', ['create_table_external', {'tests_record': [['test_run_time', 0, 'string'], ['pass_fail', 0, 'string'], ['session_ID', 0, 'string']]}])
    patch_os.makedirs.assert_not_called()

    # Failed/passed test folders don't already exist
    patch_os.path.exists.return_value = False

    runner = test_runner(failed_test_path='pytesting_api/testing/files/test_failed_file', passed_test_path='pytesting_api/testing/files/test_passed_file')
    
    assert patch_os.makedirs.call_count == 2
    assert patch_yaml.safe_load.call_count == 2
    
    #Yaml file is not opened
    with pytest.raises(FileNotFoundError) as excinfo:
        runner = test_runner(test_groups_file='file_dne.yaml')
    assert "'file_dne.yaml'" in str(excinfo.value)
    assert patch_yaml.safe_load.call_count == 2

@pytest.mark.test_runner_tests
def test_get_predefine_test_groups(patch_os, patch_coms):
    runner = test_runner(test_groups_file='pytesting_api/testing/files/tests_group.yaml')
    result = runner.get_predefine_test_groups()
    assert result == ['FBPI DAC Calibration', 'RAMI DAC Calibration', 'AOP 1 DAC Calibration', 'AOP 2 DAC Calibration', 'FBPI ADC Calibration']

@pytest.mark.test_runner_tests
@patch('pytesting_api.test_runner.time.time', side_effect=cycle([99.0, 100.0]))
@patch.object(test_runner, 'set_test_group')
@patch.object(test_runner, 'run_tests')
def test_run_predefined_test(mock_run_test, mock_set_test_group, mock_time, patch_coms, patch_os):
    # One test
    runner = test_runner(test_groups_file='pytesting_api/testing/files/tests_group.yaml')

    interval, description = runner.run_predefined_test('FBPI DAC Calibration')

    assert interval == 3599.0
    assert description == "FBPI DAC calibrations with keithly"
    mock_set_test_group.assert_called_once_with(['FBPI_DAC'])
    mock_run_test.assert_called_once()
    assert mock_time.call_count == 2
    assert global_test_variables.tests_parameters_dict['FBPI_DAC'] == ['-2', '2', '1', '1', '500']

    # Multiple tests
    global_test_variables.tests_parameters_dict = {}
    
    interval, description = runner.run_predefined_test('RAMI DAC Calibration')

    mock_set_test_group.assert_called_with(['SECOND_TEST'])
    assert mock_set_test_group.call_count == 3
    assert mock_run_test.call_count == 3
    assert global_test_variables.tests_parameters_dict == {'RAMI_DAC': ['-2', '2', '1', '1', '500'], 'SECOND_TEST': ['1', '-1']}

@pytest.mark.test_runner_tests
# In order to mock pytest.main, a subprocess must be created, because calling pytest triggers some other processes that don't like to be called in an existing pytest instance. Sorry for the headache.
def test_run_tests():
    imports = ("import pytest\n"
               "import os\n"
               "from unittest.mock import MagicMock, patch, mock_open\n"
               "from pytesting_api.test_runner import test_runner\n"
               "from pytesting_api import global_test_variables\n"
            )
    
    mock_make_html_report = "patch('pytesting_api.test_runner.test_runner.make_html_report')"
    mock_coms = "patch('pytesting_api.global_test_variables.coms', MagicMock(send_request=MagicMock()))"
    mock_os = "patch('pytesting_api.test_runner.os', MagicMock(path=MagicMock(exists=MagicMock(), join=MagicMock(return_value=''), getmtime=abs), makedirs=MagicMock(), remove=MagicMock(), devnull=os.devnull))"
    mock_yaml = "patch('pytesting_api.test_runner.yaml', MagicMock(safe_load=MagicMock()))"
    mock_pytest = "patch('pytesting_api.test_runner.pytest', MagicMock(main=MagicMock(return_value=0)))"
    mock_datetime = "patch('pytesting_api.test_runner.datetime', MagicMock(now=MagicMock(return_value=3)))"
    mock_open = "patch('builtins.open', mock_open(read_data='sbeve'))"
    mock_contextlib = "patch('pytesting_api.test_runner.contextlib', MagicMock(redirect_stdout=MagicMock(), redirect_stderr=MagicMock()))"

    run_test = (f"with ({mock_coms} as mock_coms, {mock_os} as mock_os, {mock_yaml} as mock_yaml, {mock_make_html_report} as mock_html, {mock_pytest} as mock_pytest, {mock_datetime} as mock_datetime, {mock_open} as mock_open, {mock_contextlib} as mock_contextlib):\n"
                "  runner = test_runner()\n"
                "  mock_lock = MagicMock(acquire=MagicMock(return_value=True))\n"
                "  runner._test_runner__test_group_lock = mock_lock\n"
                "  runner._test_runner__debug = True\n"
                "  runner.run_tests()\n"

                # Test with debug is True and no failed tests
                "  mock_pytest.main.assert_called_with([\n"
                "      '--html=',\n"
                "      '--no-summary',\n"
                "      '--quiet',\n"
                "      '--tb=no',\n"
                "      '--capture=no',\n"
                "      '--disable-warnings',\n"
                "      '--log-cli-level=INFO',\n"
                "      'pytesting_api/tests/',\n"
                "      '-m', \n"
                "      'group1',\n"
                "      ])\n"
                "  data = {\n"
                "       'test_run_time' : ['3'],\n"
                "        'pass_fail' : ['Pass'],\n"
                "        'session_ID' : ['']\n"
                "  }\n"
                "  mock_coms.send_request.assert_called_with('', ['save_data_group', 'tests_record', data, 'test_executor'])\n"

                # Test with debug is False and failed tests
                "  runner._test_runner__debug = False\n"
                "  mock_pytest.main.return_value = 798569\n"
                "  data['pass_fail'] = ['fail']\n"
                "  runner.run_tests()\n"

                "  mock_open.assert_called_with(os.devnull, 'w')\n"
                "  mock_coms.send_request.assert_called_with('', ['save_data_group', 'tests_record', data, 'test_executor'])\n"

                # Ensure lock is handled correctly
                "  mock_lock.acquire.return_value = False\n"
                "  with pytest.raises(RuntimeError) as excinfo:\n"
                "      runner.run_tests()\n"
                "  assert 'Could not acquire test group lock' in str(excinfo.value)\n"
               )

    result = subprocess.run(
        [sys.executable, "-c", imports + run_test],
        capture_output=True,
        text=True
    )

    if DEBUG:
        print(f"\n\n{result.stderr=}")
        print(f"\n\n{result.stdout=}")

    assert result.stderr == '', 'Turn on debug to see full stderr output'
    assert result.stdout == '', 'Turn on debug to see full stdout output'

#TODO
@pytest.mark.test_runner_tests
def test_make_html_report():
    pass

@pytest.mark.test_runner_tests
@patch('pytesting_api.test_runner.glob.glob')
def test_delete_old_files(mock_glob, patch_coms, patch_os, patch_yaml):
    # With no entries to remove
    runner = test_runner()
    mock_glob.return_value=[1, 2, 3]
    runner.delete_old_files('path/to/archived/files')
    patch_os.remove.assert_not_called()
    
    # Sorted list
    mock_glob.return_value = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    runner.delete_old_files('path/to/archived/files')

    assert patch_os.remove.call_count == 2
    patch_os.remove.assert_called_with(2)

    # With unsorted entries
    mock_glob.return_value=[13, 12, 11, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    runner.delete_old_files('path/to/archived/files')
    patch_os.remove.assert_called_with(3)

@pytest.mark.test_runner_tests
def test_set_test_group(patch_coms, patch_os, patch_yaml):
    runner = test_runner()
    mock_lock = MagicMock(acquire=MagicMock(return_value=True), release=MagicMock())
    runner._test_runner__test_group_lock = mock_lock

    runner.set_test_group(['path/to/folder'])
    
    assert runner._test_runner__test_group == 'path/to/folder'
    mock_lock.acquire.assert_called()
    
    # Failure to acquire lock
    mock_lock.acquire.return_value = False

    with pytest.raises(RuntimeError) as excinfo:
        runner.set_test_group(['new/path'])
    
    assert "Could not aquire test group lock" in str(excinfo.value)