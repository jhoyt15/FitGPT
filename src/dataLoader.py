import json
import csv

def make_json(data_path:str,json_path:str)->None:
     
    # create a dictionary
    data = {}
    
    # Open a csv reader called DictReader
    with open(data_path, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        
        # Convert each row into a dictionary 
        # and add it to data
        for rows in csvReader:
            
            # Assuming a column named 'No' to
            # be the primary key
            key = rows['id']
            data[key] = rows

    # Open a json writer, and use the json.dumps() 
    # function to dump data
    with open(json_path, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(data, indent=4))

def make_index()->None:
    '''Make/Update the ElasticSearch index using the data in the json file'''
    pass