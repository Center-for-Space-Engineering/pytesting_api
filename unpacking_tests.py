import pandas as pd
import openpyxl
import yaml
import re

class process_test_xlsx():
    def __init__(self, file_path:str, test_library_table_name:str, sheet_name:str, output_file_name = 'test_definition.yaml') -> None:
        self.__file_path = file_path
        self.__test_library_table_name = test_library_table_name
        self.__output = output_file_name

        self.__wb = openpyxl.load_workbook(self.__file_path, data_only=True)
        self.__sheet_name = sheet_name

        self.__sheet = self.__wb[self.__sheet_name]
        self.__test_library_table_name = self.__sheet.tables[self.__test_library_table_name]

        table_range = self.__test_library_table_name.ref

        data = self.__sheet[table_range]

        data_list = [[cell.value for cell in row] for row in data]

        self.__df_test = pd.DataFrame(data_list[1:], columns=data_list[0])

        with open(self.__output, 'w+') as file: 
            #Now that we have collected our tables, lets actual build packets
            for index, test in self.__df_test.iterrows():
                test_dict = {
                    'Procedures' : test['Procedures'],
                    'Parameters' : self.split_string_to_dict(test['Parameters']),
                    'Description' : test['Description'],
                    'Period' : test['Period'],
                }

                output_dict = {
                    test['Test Name'] : test_dict
                }

                yaml.dump(output_dict, file)
    def split_string_to_dict(self, s):
        # Use regular expressions to capture the key and the corresponding list
        pattern = r'([^\[]+):\[(.*?)\]'

        
        # Find all matches of the pattern
        matches = re.findall(pattern, s)
        
        # Create the dictionary from the matches
        result = {key: [item.strip() for item in value.split(',')] for key, value in matches}
        
        return result

def main():
    with open("main.yaml", "r") as file:
        config_data = yaml.safe_load(file)
    test_library_table_name = config_data.get('test_library_table_name', "")
    sheet_name = config_data.get('sheet_name', "")
    file_path = config_data.get('file_path', "")
    output_file_name = config_data.get('output_file_name', "")


    pdict = process_test_xlsx(file_path=file_path, test_library_table_name=test_library_table_name, sheet_name=sheet_name, output_file_name=output_file_name)
    
if __name__ == '__main__':
    main()