'''
 This models is tasked with setting up the global variables, the collecting and running all the unit test on the system. 
 Then it creates a report for the server to use. 
'''
#prebuilt imports
import os
import glob
from bs4 import BeautifulSoup
import pytest
from datetime import datetime
import contextlib
import threading
import yaml
import time

#custom imports
from pytesting_api import global_test_variables # pylint: disable=e0401
from logging_system_display_python_api.logger import loggerCustom


class test_runner:
    '''
        This module is is how we call and run our unit test. Make sure to give it the coms object. 
    '''
    def __init__(self, name:str = 'test_executor', failed_test_path:str = '', passed_test_path:str = '', max_files_passed:int = 10, debug:bool = False, test_groups_file='pytesting_api/tests.yaml'):
        # Define the directory path where the HTML report should be saved
        self.__name = name
        self.__REPORTS_DIRECTORY = 'templates'
        self.__debug = debug
        
        self.__failed_test_path = failed_test_path
        self.__passed_test_path = passed_test_path
        self.__test_group = 'group1'
        self.__test_group_lock = threading.Lock()
        # Make sure the folder exist and create them if they don't 
        if not os.path.exists(self.__failed_test_path):
            os.makedirs(self.__failed_test_path)
            print(f"Created directory: {self.__failed_test_path}")

        if not os.path.exists(self.__passed_test_path):
            os.makedirs(self.__passed_test_path)
            print(f"Created directory: {self.__passed_test_path}")

        self.__max_files_passed = max_files_passed
        self.__table_name = 'tests_record'
        self.__table_structure = {
            self.__table_name : [['test_run_time', 0, 'string'], ['pass_fail', 0, 'string'], ['session_ID', 0, 'string']],
        }
        global_test_variables.coms.send_request(global_test_variables.db_name, ['create_table_external', self.__table_structure])

        # Load the YAML file
        with open(test_groups_file, "r") as file:
            self.__tests_group = yaml.safe_load(file)

        self.__logger = loggerCustom('logs/test_runner.txt')
        
        
    def get_predefine_test_groups(self):
        '''
            This returns a list of the predefined test groups
        '''
        return list(self.__tests_group.keys())
    def run_predefined_test(self, test_name):
        '''
            This function runs a predefined test group
        '''
        #get the test group information
        test_group = self.__tests_group[test_name]

        test_period = int(test_group['Period'])

        start_time = time.time()


        #now we want to loop though each test in order
        tests = test_group['Procedures'].split(',')

        self.__logger.send_log(f"tests: {tests}")

        for test in tests:
            #set test group
            global_test_variables.tests_parameters_dict[test] = test_group['Parameters'][test]
            
            self.set_test_group([test])

            #run test
            self.run_tests()
        
        end_time = time.time()

        return test_period - (end_time - start_time), test_group['Description']
    def run_tests(self):
        '''
            This function runs all the test then creates an html report. 
        '''
        # Define the path for the HTML report
        report_path = os.path.join(self.__REPORTS_DIRECTORY, 'testing_report.html')

        if self.__test_group_lock.acquire(timeout=1):
            test_group = self.__test_group
            self.__test_group_lock.release()
        else :
            raise RuntimeError("Could not acquire test group lock")

        # Define the arguments for pytest
        self.__logger.send_log(f"Running test: {test_group}")
        pytest_args = [
            '--html=' + report_path,
            '--no-summary',
            '--quiet',
            '--tb=no',
            '--capture=no',
            '--disable-warnings',
            '--log-cli-level=INFO',
            'pytesting_api/tests/',
            '-m', 
            test_group,
        ]

        if not self.__debug:
            # Run pytest programmatically with output suppressed
            with open(os.devnull, 'w') as devnull:
                with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                    exit_code = pytest.main(pytest_args)# Run pytest programmatically
        else : 
            exit_code = pytest.main(pytest_args)# Run pytest programmatically, changed to read gps hat

        # Check if there were failed tests
        if exit_code == 0:
            #if not save one copy of the test
            self.make_html_report(report_path=report_path)
            data = {
                'test_run_time' : [str(datetime.now())],
                'pass_fail' : ['Pass'],
                'session_ID' : [global_test_variables.session_id]
            }
        else:
            #otherwise save multiple copies of the tests. 
            self.make_html_report(report_path=report_path, failed=True)
            data = {
                'test_run_time' : [str(datetime.now())],
                'pass_fail' : ['fail'],
                'session_ID' : [global_test_variables.session_id]
            }
        
        global_test_variables.coms.send_request(global_test_variables.db_name,['save_data_group', self.__table_name, data, self.__name])       
    def make_html_report(self, report_path, failed = False):
        '''
            this function takes the html report generated by pytest, then writes a html file for our system to use and saves it
        '''
        #Now lets fix the generated html file
        # Read the HTML file
        with open(report_path, 'r') as file:
            html_content = file.read()

        # Create a BeautifulSoup object
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the head tag
        head = soup.head

        # Add CSS link
        css_link = soup.new_tag('link', rel='stylesheet', href="{{ url_for('static', filename='styles.css') }}")
        head.append(css_link)

        # Add JavaScript script tag
        script_tag = soup.new_tag('script', src='page_manigure.js')
        head.append(script_tag)

        # 1. Add tables to the start of the file. 
        tab_container = soup.new_tag('div', attrs={'class': 'tab-container'})
        
        tab1 = soup.new_tag('div', attrs={'class': 'tab', 'onclick': "open_tab('Data Stream')"})
        tab1.string = 'Data Stream'
        tab_container.append(tab1)

        
        tab2 = soup.new_tag('div', attrs={'class': 'tab', 'onclick': "open_tab('Command')"})
        tab2.string = 'Command'
        tab_container.append(tab2)

        
        tab3 = soup.new_tag('div', attrs={'class': 'tab', 'onclick': "open_tab('Sensor')"})
        tab3.string = 'Sensor'
        tab_container.append(tab3)

        
        tab4 = soup.new_tag('div', attrs={'class': 'tab', 'onclick': "open_tab('Status Report')"})
        tab4.string = 'Status Report'
        tab_container.append(tab4)

        tab5 = soup.new_tag('div', attrs={'class': 'tab', 'onclick': "open_tab('unit_testing')"})
        tab5.string = 'Passed Unit test'
        tab_container.append(tab5)


        tab6 = soup.new_tag('div', attrs={'class': 'tab', 'onclick': "open_tab('failed_test')"})
        tab6.string = 'failed_test'
        tab_container.append(tab6)
        

        # Insert the tab container at the beginning of the <body> section
        soup.body.insert(0, tab_container)

        # 2. Change the link href attribute
        # Find the link tag
        link_tag = soup.find('link', href='assets/style.css')
        # Change the href attribute
        link_tag['href'] = os.path.join(self.__REPORTS_DIRECTORY, 'assets/style.css')  # Change it to the new link

        # Save the report HTML content
        if failed:
            with open(self.__failed_test_path + f"/failed_test_{datetime.now()}.html", 'w+') as file:
                file.write(soup.prettify())
        else : 
            with open(self.__passed_test_path + f"/passed_test_{datetime.now()}.html", 'w+') as file:
                file.write(soup.prettify())
            self.delete_old_files(self.__passed_test_path)    
    def delete_old_files(self, folder_path):
        '''
            This function makes sure the archive folder doesn't exceed a certain number of files  
        '''
        files = glob.glob(os.path.join(folder_path, "*_test_*.html"))
        if len(files) > self.__max_files_passed:
            files.sort(key=os.path.getmtime)
            files_to_delete = files[:len(files) - self.__max_files_passed]
            for file_to_delete in files_to_delete:
                os.remove(file_to_delete)
    def set_test_group(self, args):
        '''
            This function sets the test group to run
            
            ARGS:
                args[0] = test_group (path to folder that has the test for this test group)
        '''
        if self.__test_group_lock.acquire(timeout=1):
            self.__test_group = args[0]
            self.__test_group_lock.release()
        else :
            raise RuntimeError("Could not aquire test group lock")
