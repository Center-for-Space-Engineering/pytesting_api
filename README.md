# Architecture overview:
The pytesting framework is set up to provide an easy and simple way for users to set up unit test on the CSE framework. The basic structure is to define files, then test in those files and assign them to groups. This document has two main section. The first describes the how to build test on the CSE framework, the second just gives some general information on pytest.  

NOTE: It is often useful to set the `DEBUG_UNIT_TEST` variable to `TRUE` because it will allow the unit test to output to the terminal. When actually running them set it to false as to not over load the screen. 

# HOW TO build unit test
In the cse framework all unit test must be located in the `pytesting_api/tests`. There are no exception to this. In side this folder you can create files that start with `test_`. The number and names of these files (outside of the aforementioned prefix) does not matter. I would recommend creating files for types of unit test. Then inside those files fall the following to create a unit test: 

1. Use the correct imports:
   ```python
      import pytest #pylint: disable=w0611
      import copy
      from datetime import datetime, timezone
      import threading
      from pytesting_api import global_test_variables # pylint: disable=e0401
   ```

   NOTE: 
      - pytest is used to group our tests (and other things if needed). 
      - global_test_variables is used to give the test access to the coms object and the database name.
2. Lets create a test group to assign our test too. In the `pytesting_api/pytest.ini` under `markers =` add a new test group.
   Example:
   ```python
   [pytest]
   markers =
      group1 : 'test group 1'
      group2 : 'test group 2'
      group3 : 'test group 3'
   ```
   This creates 3 groups they are group1, group2, group3.
3. Many if not all test will want to use a set up function to get data for a sensor, or something you wish to test. Here is an example of how to do so. 
   Example:
   ```python
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
   ```
   Note: This example creates a request to the `gps_board` so that we can listen to its data and then process it. The way this works is the `setup` function makes a tap to the `gps_board`, the `gps_board` will then call the `set_data` function to store the data in the `data_buff` variable.

4. Now lets build a unit test. first consider the following example:
   ```python
   @pytest.mark.group3
   def test_example_coms():
      '''
         Example of how to call the coms object
      '''
      assert global_test_variables.coms.get_test() == "testing"
   ```
   - Consider the first line: `@pytest.mark.group3` this line tell `pytest` and 'marks' it as being in `group3` that we created earlier. 
   - Next consider the function declaration: `def test_example_coms():` notice that this starts with `test_` this tells `pytest` that this function is a test and needs to be run. In other words, ALL your functions need to start with `test_`. If they don't then your test will not run.
   - Finally consider `global_test_variables.coms.get_test()` this is how you can call function in the coms object. Which means you can make request to other threads just like we do in other places in the CSE framework. 
   Example:
   ```python
   self.__table_name = 'tests_record'
   self.__table_structure = {
      self.__table_name : [['test_run_time', 0, 'string'], ['pass_fail', 0, 'string'], ['session_ID', 0, 'string']],
   }
   global_test_variables.coms.send_request(global_test_variables.db_name, ['create_table_external', self.__table_structure])
   ```
NOTE: These lines of code are used in the test_runner, to create a table in the database to store testing information. However, they give an example of how to use the `global_test_variables.coms.send_request`. 

Also consider how to get the data for processing:
```python
   @pytest.mark.gps_hat
   def test_gps_day():
      '''
         testing the GPS day against server day
      '''
      global data_buf
      global data_buf_lock

      if data_buf_lock.acquire(timeout=1):
         data_buf_copy = copy.deepcopy(data_buf)
         data_buf_lock.release()
      else:
         raise RuntimeError('cannot acquire data_buf_lock')
      
      # Get the current UTC datetime
      current_utc_datetime = datetime.now(timezone.utc)

      # Get the current UTC date
      current_utc_date = current_utc_datetime.date()

      assert current_utc_date == data_buf_copy['day'][-1]
```

Note: That in order to get the data for processing we make a copy of it, using the following lines. 
```python
   global data_buf
   global data_buf_lock

   if data_buf_lock.acquire(timeout=1):
      data_buf_copy = copy.deepcopy(data_buf)
      data_buf_lock.release()
   else:
      raise RuntimeError('cannot acquire data_buf_lock')
```
It is important make sure you can copy the data so that you don't run into threading problems. 



# Using pytest: Fixtures and Parameters

pytest is a powerful testing framework for Python that makes it easy to write simple and scalable tests. In this guide, we'll explore how to use pytest fixtures and parameters to set up test environments and run tests with different inputs.

## Fixtures

Fixtures in pytest are functions that provide setup and teardown logic for tests. They allow you to define reusable setup code that can be shared across multiple test functions. Here's how to use fixtures in pytest:

1. **Defining Fixtures:**
   ```python
   import pytest

   @pytest.fixture
   def setup_data():
       # Setup logic: create test data
       data = [1, 2, 3]
       yield data  # Provide the setup data to the test function
       # Teardown logic: clean up resources (optional)
   ```

2. **Using Fixtures in Tests:**
   ```python
   def test_example(setup_data):
       # Test function that uses the setup_data fixture
       assert len(setup_data) == 3
   ```

3. **Fixture Scope:**
   Fixtures can have different scopes (`function`, `class`, `module`, `session`), which determine when they are set up and torn down. The default scope is `function`, which means the fixture is invoked once per test function.

4. **Fixture Dependencies:**
   Fixtures can depend on other fixtures, allowing you to build a hierarchy of setup logic. When a test function requests a fixture as an argument, pytest automatically resolves and invokes the required fixtures in the correct order.

## Parameters

Parameterization in pytest allows you to run the same test function with different inputs. It's useful for testing multiple scenarios with varying data. Here's how to use parameters in pytest:

1. **Defining Parameters:**
   ```python
   @pytest.mark.parametrize("input, expected", [(1, 2), (2, 4), (3, 6)])
   def test_multiply_by_two(input, expected):
       assert input * 2 == expected
   ```

2. **Using Parameters in Tests:**
   The `@pytest.mark.parametrize` decorator allows you to specify input values and expected outcomes for each test case.

3. **Dynamic Parameters:**
   Parameters can be dynamically generated using fixtures or other logic, allowing for more flexible test scenarios.

## Examples

Here are some examples demonstrating the usage of fixtures and parameters in pytest:

1. **Using Fixtures:**
   ```python
   @pytest.fixture
   def setup_data():
       data = [1, 2, 3]
       yield data
   ```

2. **Using Parameters:**
   ```python
   @pytest.mark.parametrize("input, expected", [(1, 2), (2, 4), (3, 6)])
   def test_multiply_by_two(input, expected):
       assert input * 2 == expected
   ```

---

This document provides a basic overview of how to use pytest fixtures and parameters to create reusable setup logic and run tests with varying inputs. Experiment with fixtures and parameters to build robust and flexible test suites for your Python projects.