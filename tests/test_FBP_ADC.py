import pytest #pylint: disable=w0611
import time
import numpy as np
from datetime import datetime, timezone
import requests
import traceback

from pytesting_api import global_test_variables # pylint: disable=e0401
from logging_system_display_python_api.logger import loggerCustom
from command_packets.functions import FBP_calibrated_dac_code

import system_constants # pylint: disable=e0401


logger = loggerCustom("logs/FBP_adc_calibration_test.txt")

granule_count = 100

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
      f'calibration_FBP_ADC_low' : [['DAC_word', 0, 'string'], ['measured_voltage', 0, 'string'], ['set_current', 0, 'string'], ['measured_current', 0, 'string'], ['gain', 0, 'string'], ['variance_c', 0, 'string'], ['sigma_c', 0, 'string'], ['starting_line', 0, 'string'], ['ending_line', 0, 'string']],
   }


   #ask database to make table
   coms.send_request(database, ['create_table_external', table_structure])

   #Turn off all packets on board
   hostname = global_test_variables.pi_config_dict['pi_one']['host_name']
   port = global_test_variables.pi_config_dict['pi_one']['connection_port']

   requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)



@pytest.mark.FBP_ADC #MAKE SURE TO ADD THE TEST GROUP (PROCEDURE)
def test_low_gain():
   try :
      #get system varibles
      coms = global_test_variables.coms #not used right now but you may need it in the future
      database = global_test_variables.db_name #not used right now but you may need it in the future
      hostname = global_test_variables.pi_config_dict['pi_one']['host_name']
      port = global_test_variables.pi_config_dict['pi_one']['connection_port']

      logger.send_log(f"pi host name {hostname} connection_port {port}")

      #get the last saved idx
      idx_db_last = global_test_variables.get_last_idx('FBP')
      logger.send_log(f"Starting idx: {idx_db_last}")

      data = {
            'DAC_word': [],
            'measured_voltage': [],
            'set_current' : [], 
            'measured_current' : [],
            'gain' : [],
            'variance_c' : [],
            'sigma_c' : [],
            'starting_line' : [],
            'ending_line' : []
         }
      
      #grab the instruments 
      #NOTE: The try catch statement is just in here for an example for you guys of how to debug the test if code has an error.
      logger.send_log('Running test')
      try :
         instrument_dict = global_test_variables.instruments
      except Exception as e:
         logger.send_log(f'Error: {e}')


      logger.send_log('Got instruments')

      instrument_dict['digital_voltmeter_keithley'].write(['*RST']) #reset machine
      instrument_dict['keithley6221'].write(['*RST']) #reset machine
      logger.send_log('Wrote reset to instruments')

      # instrument_dict['keithley6221'].write(['OUTP OFF']) #set guard mode
      # instrument_dict['keithley6221'].write(['OUTP:ISH GUAR']) #set guard mode
      # instrument_dict['keithley6221'].write(['OUTP:LTE OFF']) #set guard mode

      # lte = instrument_dict['keithley6221'].write_read(['OUTP:LTE?'])
      # ish = instrument_dict['keithley6221'].write_read(['OUTP:ISH?'])
      # logger.send_log(f'Set guard mode, reported configs are guard {ish} LTEarth {lte}')


      # get parameters out of file
      cmin_l = float(global_test_variables.tests_parameters_dict['FBP_ADC'][0])
      cmax_l = float(global_test_variables.tests_parameters_dict['FBP_ADC'][1])
      c_step_count = int(global_test_variables.tests_parameters_dict['FBP_ADC'][2])
      vmin = float(global_test_variables.tests_parameters_dict['FBP_ADC'][3])
      vmax = float(global_test_variables.tests_parameters_dict['FBP_ADC'][4])
      v_step_size = float(global_test_variables.tests_parameters_dict['FBP_ADC'][5])

      logger.send_log(f"cmin_l {cmin_l} cmax_l {cmax_l} c_step_count {c_step_count} vmin {vmin} vmax {vmax} v_step_size {v_step_size}")

      number_of_steps = int(((vmax - vmin) // v_step_size) + 1) # plus 1 to include end point

      #set sweep based on parameters 
      setVoltage = np.linspace(vmin,vmax,number_of_steps) # start voltage, max voltage, number of points
      setCurrentLow = np.linspace(cmin_l,cmax_l,c_step_count) # start voltage, max voltage, number of points

      transient_delay = 7

      logger.send_log(f'Calibrations Parameters:\n\tvoltages: {setVoltage}\n\ttransient {transient_delay}\n\tsetCurrentLow {setCurrentLow}')

      # Turn on auto ranging for the keithley
      instrument_dict['keithley6221'].write(["CURR:RANG:AUTO ON"])


      for voltage in setVoltage:
         # set the voltage
         dac_word = FBP_calibrated_dac_code(voltage=voltage) # call calibrated dac word conversion. 
         requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/F800/local_code=501', timeout=10)
         requests.get(f'http://{hostname}:{port}/command_SWP_config/cfgFBP/0/{dac_word}/local_code=501', timeout=10)
         requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)

         logger.send_log(f"voltage {voltage} dac_word {dac_word}")
         for current in setCurrentLow:
            # Turn on auto ranging for the keithley
            instrument_dict['keithley6221'].write(["CURR:RANG:AUTO ON"])
            instrument_dict['keithley6221'].write(["OUTP OFF"])
            time.sleep(0.5)

            instrument_dict['keithley6221'].write([f"SOUR:CURR {current}"])
            instrument_dict['keithley6221'].write(["OUTP ON"])

            logger.send_log(f"current {current} command sent SOUR:CURR {current}")
            
            time.sleep(transient_delay)

            sample = instrument_dict['digital_voltmeter_keithley'].write_read(['MEAS:VOLT?']).replace('\n', '')

            logger.send_log(f"Sampled Voltage: {sample}")

            # add the data we have right now
            data['DAC_word'].append(str(dac_word))
            data['measured_voltage'].append(str(sample))
            data['set_current'].append(str(current))

            #send command to turn on fpp4 and FBP packets 
            requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/F800/local_code=501', timeout=10)

      
            #wait for more data to come in.
            idx_db_last = global_test_variables.get_last_idx('FBP')
            idx_db = idx_db_last
            total_liens = granule_count * 10
            while idx_db < (idx_db_last + total_liens): # wait for next idx to come in for board
               idx_db = global_test_variables.get_last_idx('FBP') # NOTE: We dont need a sleep statement here because the get_last_idx has that already.       
            logger.send_log(f"Last saved idx: {idx_db}")

            sample_idx = idx_db_last + 1 if idx_db_last != 0 else sample_idx # igrone first point 
            logger.send_log(f"Staring idx {sample_idx}")

            data['starting_line'].append(sample_idx)
            data['ending_line'].append(sample_idx + total_liens)
            
            # Turn off packets after we get data
            requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/0000/local_code=501', timeout=10)

            #wait for data to flush out of pi's buffer and the gs buffer (5 seconds each) then add a few seconds for processing delay.
            time.sleep(15) #may need to be more time but well start here
            idx_db_last = global_test_variables.get_last_idx('FBP')

            #pull packet out of database
            data_db_FBP = global_test_variables.get_data_from_data_base(table_name = 'FBP', starting_idx = sample_idx, max_num_lines = total_liens - 1)
            data['gain'].append('1')

            data['measured_current'].append(str(np.mean(data_db_FBP['DCP'])))
            data['variance_c'].append(str(np.var(data_db_FBP['DCP'])))
            data['sigma_c'].append(str(np.std(data_db_FBP['DCP'])))

      global_test_variables.save_data_to_db(table_name='calibration_FBP_ADC_low', data=data, thread_name='FBP_gain_calibration')
      logger.send_log("sent save command")

      logger.send_log("Finished low Calibration")
   except Exception as e:
      print(traceback.format_exc())
