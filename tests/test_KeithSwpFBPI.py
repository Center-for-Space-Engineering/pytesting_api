import pytest #pylint: disable=w0611
import time
import numpy as np
from datetime import datetime, timezone
import requests
import traceback

from pytesting_api import global_test_variables # pylint: disable=e0401
from logging_system_display_python_api.logger import loggerCustom
import system_constants # pylint: disable=e0401

######################################################
BoardPi = 'pi_two' #choose pi_one for SWP and pi_two for AUX
TableName = 'FBPI' #The table we want to pull from for index book-keeping (change to RIC)
stopPackets = '3F' #Leave everything else on (fill up buffer fast)
mode = 'FF' #80 for AOP, 40 for FBPI. Turns off other packets during collection to reduce noise.
StartCurrent = '-5e-6' #Keithely start current (A)
EndCurrent = '5e-6' #Keithely end current (A)
CurrentSteps = '5' #Number of steps to take
StepDelay = '20' #Keithley step hold time (s)
Gain = '1' #Only valid for SLP and AOP channels. 1 is low gain, 0 is high gain
flushTime = 10 #Timer for database flush
######################################################

logger = loggerCustom("logs/KeithSwpFBPI.txt")

@pytest.fixture(scope="session", autouse=True)
def setup_before_all_tests():

   #get system varibles
   coms = global_test_variables.coms
   database = global_test_variables.db_name
   hostname = global_test_variables.pi_config_dict[f'{BoardPi}']['host_name']
   port = global_test_variables.pi_config_dict[f'{BoardPi}']['connection_port']

   #Turn packets on
   requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/{mode}/local_code=501', timeout=10)
   requests.get(f'http://{hostname}:{port}/command_AOPDAC_config/AOPGS_config/{Gain}/{Gain}/local_code=501', timeout=10)

@pytest.mark.KeithSwpFBPI #MAKE SURE TO ADD THE TEST GROUP (PROCEDURE)
def test_keithley_sweeping_FBPI(): #MAKE SURE TO HAVE test_ in front of this!
   try :
      logger.send_log(f'Running FBPI with Start Current: {StartCurrent} and End Current: {EndCurrent}')
      
      coms = global_test_variables.coms #not used right now but you may need it in the future
      database = global_test_variables.db_name #not used right now but you may need it in the future
      hostname = global_test_variables.pi_config_dict[f'{BoardPi}']['host_name']
      port = global_test_variables.pi_config_dict[f'{BoardPi}']['connection_port']

      #get the start idx for my sweep
      instrument_dict = global_test_variables.instruments
      
      #requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/{mode}/local_code=501', timeout=10)
      instrument_dict['keithley6221'].write(['*RST']) #reset machine
      instrument_dict['keithley6221'].write([f"SOUR:CURR {StartCurrent}"]) #Bias current 
      instrument_dict['keithley6221'].write(['SOUR:CURR:COMP 10']) #10V output compliance
      instrument_dict['keithley6221'].write(['SOUR:SWE:SPAC LIN']) #Setup the sweep to be lin space
      instrument_dict['keithley6221'].write([f"SOUR:CURR:STAR {StartCurrent}"]) #Start step
      instrument_dict['keithley6221'].write([f"SOUR:CURR:STOP {EndCurrent}"]) #Stop step
      instrument_dict['keithley6221'].write([f"SOUR:SWE:POIN {CurrentSteps}"]) #Number of steps
      instrument_dict['keithley6221'].write([f"SOUR:DEL {StepDelay}"]) #Time at each step
      instrument_dict['keithley6221'].write(['SOUR:SWE:RANG BEST']) #Best ranging 
      instrument_dict['keithley6221'].write(['SOUR:SWE:COUN 1']) #Sweeps 1 time
      instrument_dict['keithley6221'].write(['SOUR:SWE:CAB OFF']) #Disable compliance abort
      instrument_dict['keithley6221'].write(['SOUR:SWE:ARM']) #Arms the sweep with the above parameters
      instrument_dict['keithley6221'].write(['INIT']) #Triggers the sweep to start

      idx_db_start = global_test_variables.get_last_idx(TableName) + 1
      time.sleep(float(CurrentSteps)*float(StepDelay)) #The number of steps we do times the duration of each step

      #requests.get(f'http://{hostname}:{port}/command_from_file/send_mode_packet/{stopPackets}/local_code=501', timeout=10)
      #remember, stop packets includes other stuff so the buffer flushes faster.

      idx_db_last = global_test_variables.get_last_idx(f'{TableName}')

      logger.send_log(f"Start Index: {idx_db_start}. End Index: {idx_db_last}.")
      instrument_dict['keithley6221'].write(['OUTP OFF'])
   except Exception as e:
      logger.send_log(traceback.format_exc())