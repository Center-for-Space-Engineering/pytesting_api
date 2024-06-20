import pytest #pylint: disable=w0611
import copy
from datetime import datetime, timezone
import threading
from pytesting_api import global_test_variables # pylint: disable=e0401

data_buf = None
data_buf_lock = threading.Lock()

@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
    '''
        Example to send request to GPS_board to listen to it
    '''
    global_test_variables.coms.send_request('gps_board', ['create_tap', set_data, 'gps_test'])
    
    
def set_data(data, _):
    '''
        Example of tapping data from GPS data stream
    '''
    global data_buf
    global data_buf_lock

    if data_buf_lock.acquire(timeout=1):
        data_buf = copy.deepcopy(data)
        data_buf_lock.release()
    else:
        raise RuntimeError('cannot acquire data_buf_lock')
    

@pytest.mark.gps_hat
def test_gps_day():
    '''
        testing the GPS day against server day
    '''
    global data_buf
    global data_buf_lock
    # Get the current UTC datetime
    current_utc_datetime = datetime.now(timezone.utc)

    # Get the current UTC date
    current_utc_date = current_utc_datetime.date()

    #print(f"Current UTC datetime: {current_utc_datetime}")
    print(f"Current UTC date: {current_utc_date}")
    print(f"Current UTC datetime: {current_utc_datetime}")


    if data_buf_lock.acquire(timeout=1):
        data_buf_copy = copy.deepcopy(data_buf)
        data_buf_lock.release()
    else:
        raise RuntimeError('cannot acquire data_buf_lock')
    
    print(f"Data_copy: {data_buf_copy}")
    

    assert current_utc_date == data_buf_copy['day'][-1]





