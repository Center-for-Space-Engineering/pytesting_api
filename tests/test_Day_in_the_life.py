import pytest #pylint: disable=w0611
import time
from datetime import datetime, timezone
import pytz
import requests
import traceback

from pytesting_api import global_test_variables # pylint: disable=e0401
from logging_system_display_python_api.logger import loggerCustom
import system_constants # pylint: disable=e0401

class state_control():
   def __init__(self):
      self.last_state_packets = 0
      self.pre_voltage = 0
      self.table_name = f"day_in_the_life"



logger = loggerCustom("logs/day_life.txt")
state_control_obj = state_control()


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
      state_control_obj.table_name: [['packets', 0, 'string'], ['current_voltage', 0, 'string'], ['time_utc', 0, 'string']],
   }

   #ask database to make table
   coms.send_request(database, ['create_table_external', table_structure])

   #Turn off all packets on board
   hostname = global_test_variables.pi_config_dict['pi_one']['host_name']
   port = global_test_variables.pi_config_dict['pi_one']['connection_port']

   requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)



@pytest.mark.DayLife #MAKE SURE TO ADD THE TEST GROUP (PROCEDURE)
def test_packets_on_off():
   try :
      #get system varibles
      coms = global_test_variables.coms #not used right now but you may need it in the future
      database = global_test_variables.db_name #not used right now but you may need it in the future
      hostname = global_test_variables.pi_config_dict['pi_one']['host_name']
      port = global_test_variables.pi_config_dict['pi_one']['connection_port']

      logger.send_log(f"pi host name {hostname} connection_port {port}")

      data = {
            'packets': [],
            'current_voltage': [],
            'time_utc' : [],
         }
      
      #grab the instruments 
      #NOTE: The try catch statement is just in here for an example for you guys of how to debug the test if code has an error.
      logger.send_log('Running test')
      try :
         instrument_dict = global_test_variables.instruments
      except Exception as e:
         logger.send_log(f'Error: {e}')
      logger.send_log('Got instruments')



      # get parameters out of file
      total_steps_packets = float(global_test_variables.tests_parameters_dict['DayLife'][0])
      on_steps = float(global_test_variables.tests_parameters_dict['DayLife'][1])
      vmin = float(global_test_variables.tests_parameters_dict['DayLife'][2])
      vmax = float(global_test_variables.tests_parameters_dict['DayLife'][3])
      step_size = float(global_test_variables.tests_parameters_dict['DayLife'][4])

      #set sweep based on parameters 
      current_limit = '0.01'

      choice = True
      
      choice = True if state_control_obj.last_state_packets < on_steps else False

      if choice : 

         requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/ffff/local_code=501', timeout=10)

         voltage = state_control_obj.pre_voltage + step_size if state_control_obj.pre_voltage < vmax else vmin
         instrument_dict['digital_powersupply_RS'].write([f'INST OUT1 \nAPPLY \"{voltage},{current_limit}" \nOUTP ON'])
         instrument_dict['digital_powersupply_RS'].write([f'INST OUT2 \nAPPLY \"{voltage},{current_limit}" \nOUTP ON'])
         state_control_obj.pre_voltage = voltage
      else : 
         requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)
      

      state_control_obj.last_state_packets = state_control_obj.last_state_packets + 1 if state_control_obj.last_state_packets < total_steps_packets else 0

      data['packets'].append("on" if choice else "off")
      data['current_voltage'].append(str(state_control_obj.pre_voltage))
      # Get current UTC time
      utc_time = datetime.now(pytz.UTC)

      # Convert to timestamp string
      timestamp_str = utc_time.strftime('%Y-%m-%d %H:%M:%S %Z')
      data['time_utc'].append(timestamp_str)



      global_test_variables.save_data_to_db(table_name=state_control_obj.table_name, data=data, thread_name='day_in_the_life')
      logger.send_log("sent save command")

      logger.send_log("Finished Test")
   except Exception as e:
      print("ERROR!!!")
      print(e)
      print(traceback.format_exc())




