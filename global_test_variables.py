'''
This file contatins the nesccary constants for the unit test to run. Mainly the coms object so the unit test can talk tot the rest of teh system. 
'''

coms = None #this is how our test will be able  to talk to everything running on our system. 
db_name = "" #this is the data base name this is so the test can save things into the database. 
session_id = "" # This variable is so the test know what session the are currently running under this will allow us to correlate testing conditions with test. 
