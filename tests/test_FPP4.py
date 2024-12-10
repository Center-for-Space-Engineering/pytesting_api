import pytest #pylint: disable=w0611
import time
import numpy as np
from datetime import datetime, timezone
import requests


from pytesting_api import global_test_variables # pylint: disable=e0401
from logging_system_display_python_api.logger import loggerCustom
import system_constants # pylint: disable=e0401


logger = loggerCustom("logs/ffp4_test.txt")

@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
   '''
      Example to send request to GPS_board to listen to it
   '''
   #get system varibles
   coms = global_test_variables.coms
   database = global_test_variables.db_name

   #make table structure
   table_structure = {
      f'calibration_FPP4' : [['ref_voltage', 0, 'string'], ['V1S', 0, 'string'], ['V2S', 0, 'string'], ['V3S', 0, 'string'],['V4S', 0, 'string']],
   }

   #ask database to make table
   coms.send_request(database, ['create_table_external', table_structure])

   #Turn off all packets on board
   hostname = global_test_variables.pi_config_dict['pi_one']['host_name']
   port = global_test_variables.pi_config_dict['pi_one']['connection_port']

   requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)



@pytest.mark.FPP4 #MAKE SURE TO ADD THE TEST GROUP (PROCEDURE)
def test_test():
   #get system varibles
   coms = global_test_variables.coms #not used right now but you may need it in the future
   database = global_test_variables.db_name #not used right now but you may need it in the future
   hostname = global_test_variables.pi_config_dict['pi_one']['host_name']
   port = global_test_variables.pi_config_dict['pi_one']['connection_port']

   logger.send_log(f"pi host name {hostname} connection_port {port}")

   #get the last saved idx
   idx_db_last = global_test_variables.get_last_idx('FPP4')
   logger.send_log(f"Starting idx: {idx_db_last}")

   data = {
         'ref_voltage': [],
         'V1S': [],
         'V2S' : [], 
         'V3S' : [],
         'V4S' : [],
      }
   
   #grab the instruments 
   #NOTE: The try catch statement is just in here for an example for you guys of how to debug the test if code has an error.
   logger.send_log('Running test')
   try :
      instrument_dict = global_test_variables.instruments
   except Exception as e:
      logger.send_log(f'Error: {e}')


   logger.send_log('Got instruments')

   instrument_dict['digital_powersupply_RS'].write(['*RST']) #reset machine
   instrument_dict['digital_voltmeter_keithley'].write(['*RST']) #reset machine

   logger.send_log('Wrote reset to instruments')

   # get parameters out of file
   vmin = float(global_test_variables.tests_parameters_dict['FPP4'][0])
   vmax = float(global_test_variables.tests_parameters_dict['FPP4'][1])
   step_size = float(global_test_variables.tests_parameters_dict['FPP4'][2])

   logger.send_log(f"vmin {vmin} vmax {vmax} step_size {step_size}")

   number_of_steps = int(((vmax - vmin) // step_size) + 1) # plus 1 to include end point

   #set sweep based on parameters 
   setVoltage = np.linspace(vmin,vmax,number_of_steps) # start voltage, max voltage, number of points
   current_limit = '0.01'
   transient_delay = 3

   logger.send_log(f'voltages: {setVoltage} current {current_limit} transient {transient_delay}')

   for voltage in setVoltage:
      # set the voltage
      
      instrument_dict['digital_powersupply_RS'].write([f'INST OUT1 \nAPPLY \"{voltage},{current_limit}" \nOUTP ON']) #reset machine
      logger.send_log(f"Set RS to {voltage},{current_limit}")
   
      
      #delay for transient
      time.sleep(transient_delay)

      #send command to turn on fpp4 packet
      requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/1000/local_code=501', timeout=10)

      #sleep so we sample voltage at middle of packet 
      time.sleep(0.5)

      # read the voltage
      read_voltage = instrument_dict['digital_voltmeter_keithley'].write_read(['MEAS:VOLT?']).replace('\n', '')
      logger.send_log(read_voltage)

      # add read voltage to list of data to save
      data['ref_voltage'].append(f"{read_voltage}")

      #wait for more data to come in.
      idx_db = global_test_variables.get_last_idx('FPP4')
      while idx_db == idx_db_last: # wait for next idx to come in for board
         idx_db = global_test_variables.get_last_idx('FPP4') # NOTE: We dont need a sleep statement here because the get_last_idx has that already.       
      logger.send_log(f"Last saved idx: {idx_db}")

      sample_idx = idx_db_last + 1
      logger.send_log(f"Staring idx {sample_idx}")
      


      # Turn off packets after we get data
      requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)

      #wait for data to flush out of pi's buffer and the gs buffer (5 seconds each) then add a few seconds for processing delay.
      time.sleep(15) #may need to be more time but well start here
      idx_db_last = global_test_variables.get_last_idx('FPP4')

      #pull packet out of database
      data_db_fpp4 = global_test_variables.get_data_from_data_base(table_name = 'FPP4', starting_idx = sample_idx, max_num_lines = 100)

      for line in data_db_fpp4:
         if line in data.keys():
            column = data_db_fpp4[line]

            # Convert the column to a list of strings
            data_list = column.astype(str).tolist()

            # Join the strings with a comma
            result_str = ','.join(data_list)

            #put data in the dict to save later
            data[line].append(result_str)
            


   global_test_variables.save_data_to_db(table_name='calibration_FPP4', data=data, thread_name='FPP4_calibration')
   logger.send_log("sent save command")

   logger.send_log("Finished Test")





