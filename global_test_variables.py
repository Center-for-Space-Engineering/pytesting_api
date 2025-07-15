'''
This file contatins the nesccary constants for the unit test to run. Mainly the coms object so the unit test can talk tot the rest of teh system. 
'''
import time

coms = None #this is how our test will be able  to talk to everything running on our system. 
db_name = "" #this is the data base name this is so the test can save things into the database. 
session_id = "" # This variable is so the test know what session the are currently running under this will allow us to correlate testing conditions with test. 

#instruments dict
instruments = {}

#test parameters
tests_parameters_dict = {}

#pi's config dictionary
pi_config_dict = {}

def get_last_idx(table_name):
    '''
        This function get the last index from the database with a give table name. 
    '''
    request_id = coms.send_request(db_name, ['get_last_idx', table_name])

    return_val = coms.get_return(db_name, request_id)

    while return_val is None:
        time.sleep(0.1)
        return_val = coms.get_return(db_name, request_id)

    return return_val

def save_data_to_db(table_name, data, thread_name):
    '''Saves data into the data base'''
    coms.send_request(db_name, ['save_data_group', table_name, data, thread_name])

def get_data_from_data_base(table_name, starting_idx, max_num_lines):
    '''
        pulls data from the database
    '''
    request_id = coms.send_request(db_name, [ 'get_data_large',table_name, starting_idx, max_num_lines])

    return_val = coms.get_return(db_name, request_id)

    while return_val is None:
        time.sleep(0.1)
        return_val = coms.get_return(db_name, request_id)

    return return_val
