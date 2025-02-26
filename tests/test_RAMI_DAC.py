import pytest #pylint: disable=w0611
import time
import numpy as np
from datetime import datetime, timezone
import requests
import traceback
import math

from pytesting_api import global_test_variables # pylint: disable=e0401
from logging_system_display_python_api.logger import loggerCustom
import system_constants # pylint: disable=e0401


logger = loggerCustom("logs/RIC_DAC_Calibration.txt")

@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():
   '''
      Set up table in database
   '''
   #get system varibles
   coms = global_test_variables.coms
   database = global_test_variables.db_name

   #make table structure
   table_structure = {
      f'calibration_RAMI_DAC' : [['DAC_WORD', 0, 'string'], ['V_DAC', 0, 'string']],
   }

   #ask database to make table
   coms.send_request(database, ['create_table_external', table_structure])

   #Turn off all packets on board
   hostname = global_test_variables.pi_config_dict['pi_two']['host_name']
   port = global_test_variables.pi_config_dict['pi_two']['connection_port']

   requests.get(f'http://{hostname}:{port}/command_from_file/send_idle_packet/local_code=501', timeout=10)
   requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/80/local_code=501', timeout=10)




@pytest.mark.RAMI_DAC #MAKE SURE TO ADD THE TEST GROUP (PROCEDURE)
def test_test():
   #get system varibles
   coms = global_test_variables.coms #not used right now but you may need it in the future
   database = global_test_variables.db_name #not used right now but you may need it in the future
   hostname = global_test_variables.pi_config_dict['pi_two']['host_name']
   port = global_test_variables.pi_config_dict['pi_two']['connection_port']

   logger.send_log(f"pi host name {hostname} connection_port {port}")

   data = {
         'DAC_WORD': [],
         'V_DAC': [],
      }
   
   #grab the instruments 
   #NOTE: The try catch statement is just in here for an example for you guys of how to debug the test if code has an error.
   logger.send_log('Running test')
   try :
      instrument_dict = global_test_variables.instruments
   except Exception as e:
      logger.send_log(f'Error collecting instruments: {e}')


   logger.send_log('Got instruments')

   instrument_dict['digital_voltmeter_keithley'].write(['*RST']) #reset machine

   logger.send_log('Wrote reset to instruments')

   # get parameters out of file
   vmin = float(global_test_variables.tests_parameters_dict['RAMI_DAC'][0])
   vmax = float(global_test_variables.tests_parameters_dict['RAMI_DAC'][1])
   step_size = float(global_test_variables.tests_parameters_dict['RAMI_DAC'][2])
   settling_time = float(global_test_variables.tests_parameters_dict['RAMI_DAC'][3])
   over_sample_num = int(global_test_variables.tests_parameters_dict['RAMI_DAC'][4])
   
   v_ref = 4.096

   logger.send_log(f"vmin {vmin} vmax {vmax} step_size {step_size} settling_time {settling_time}")

   number_of_steps = int(((vmax - vmin) // step_size) + 1) # plus 1 to include end point

   #set sweep based on parameters 
   setVoltage = np.linspace(vmin,vmax,number_of_steps) # start voltage, max voltage, number of points

   try :
      for voltage in setVoltage:
         # set the voltage
         dac_word = int(((voltage + v_ref) * 32768) / v_ref)
         data['DAC_WORD'].append(dac_word)
         requests.get(f'http://{hostname}:{port}/command_AOPDAC_config/AOPDAC_config/32768/32768/{dac_word}/local_code=501', timeout=10)
         logger.send_log(f"voltage {voltage} dac_word {dac_word}")

         #delay for transient
         time.sleep(settling_time)

         # read the voltage (over sample then avg)
         max_tries = 10
         read_voltage = 0
         for _ in range(over_sample_num):
            valid = False
            count = 0
            
            while not valid:
               sample = instrument_dict['digital_voltmeter_keithley'].write_read(['MEAS:VOLT?']).replace('\n', '')
               sample = float(sample)
               valid = not math.isnan(sample)
               count += 1
               if count >= max_tries:
                  logger.send_log("Could not sample from the Keithley check network connection.")
                  raise RecursionError("Could not sample from the Keithley check network connection.")

            read_voltage += sample

         read_voltage /= over_sample_num

         # add read voltage to list of data to save
         data['V_DAC'].append(f"{read_voltage}")
         logger.send_log(f'Finished sampling read_voltage {read_voltage}')

      global_test_variables.save_data_to_db(table_name='calibration_RAMI_DAC', data=data, thread_name='RIC_dac_calibration')
      logger.send_log("sent save command")

      logger.send_log("Finished Calibration")
   except Exception as e:
      print(traceback.format_exc())





