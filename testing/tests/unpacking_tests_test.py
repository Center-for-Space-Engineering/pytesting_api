import pytest
import yaml
from unittest.mock import patch

from pytesting_api.unpacking_tests import process_test_xlsx, main

@pytest.mark.unpacking_tests
def test_init():
    test_processor = process_test_xlsx(file_path='pytesting_api/testing/files/test_input.xlsx', test_library_table_name='SWP2_Testing_Library', sheet_name='Sheet1', output_file_name='pytesting_api/testing/files/test_output.yaml')
    with open('pytesting_api/testing/files/test_output.yaml') as file:
        output = yaml.safe_load(file)

        for test in output:
            assert output[test]['Procedures']
            assert output[test]['Parameters']
            assert output[test]['Description']
            assert output[test]['Period']

        assert output['FBPI DAC Calibration']['Procedures'] == 'FBPI_DAC'
        assert output['FBPI DAC Calibration']['Parameters']['FBPI_DAC'] == ['-2', '2', '1', '1', '500']
        assert output['FBPI DAC Calibration']['Description'] == 'FBPI DAC calibrations with keithly'
        assert output['FBPI DAC Calibration']['Period'] == 3600

@pytest.mark.unpacking_tests
def test_split_string_to_dict():
    test_processor = process_test_xlsx(file_path='pytesting_api/testing/files/test_input.xlsx', test_library_table_name='SWP2_Testing_Library', sheet_name='Sheet1', output_file_name='pytesting_api/testing/files/test_output.yaml')
    result = test_processor.split_string_to_dict('key:[val1, val2, val3]')
    assert result == {'key': ['val1', 'val2', 'val3']}

    result = test_processor.split_string_to_dict('k[ey:[vals]')
    assert result == {'ey': ['vals']}

    result = test_processor.split_string_to_dict('key:[val1, [val2], secretval]')
    assert result == {'key': ['val1', '[val2']}
    
    result = test_processor.split_string_to_dict('this is not a key/value pair')
    assert result == {}


@pytest.mark.unpacking_tests
@patch('yaml.safe_load')
@patch('pytesting_api.unpacking_tests.process_test_xlsx')
def test_main(mock_process_test_xlsx, mock_yaml_safe_load):
    # Typical case
    mock_config = {
        'file_path': '/path/to/my_tests.xlsx',
        'test_library_table_name': 'MyTestTable',
        'sheet_name': 'TestSuite1',
        'output_file_name': 'output.yaml'
    }
    mock_yaml_safe_load.return_value = mock_config
    
    main()

    mock_yaml_safe_load.assert_called_once()
    mock_process_test_xlsx.assert_called_once_with(
        file_path='/path/to/my_tests.xlsx',
        test_library_table_name='MyTestTable',
        sheet_name='TestSuite1',
        output_file_name='output.yaml'
    )

    # Bad yaml
    mock_yaml_safe_load.return_value = None

    with pytest.raises(AttributeError) as excinfo:
        main()

    assert "'NoneType' object" in str(excinfo.value)