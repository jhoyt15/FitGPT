import json
import csv
import os
import time
from elasticsearch import Elasticsearch, NotFoundError
from langchain.docstore.document import Document
from langchain_elasticsearch import ElasticsearchStore

FILE = os.getenv("FILE",'data/exerciseData.json')
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API = os.getenv("ELASTICSEARCH_API")


def make_json(data_path:str,json_path:str)->None:
     
    # create a dictionary
    data = {}
    
    # Open a csv reader called DictReader
    with open(data_path, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        data = []
        for row in csvReader:
            row['Title'] = row['Title'] + ' ' + row['Equipment'] + ' ' + row['Level'] + ' ' + row['BodyPart'] + ' ' +row['Type']
            data.append(row)
        

    # Open a json writer, and use the json.dumps() 
    # function to dump data
    with open(json_path, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(data, indent=4))

def make_index(es:Elasticsearch)->None:
    '''Make/Update the ElasticSearch index using the data in the json file'''

    es.indices.delete(index='workouts',ignore_unavailable=True)
    es.indices.create(index='workouts')

    operations = []
    with open(FILE,'rt') as file:
        documents = json.loads(file.read())
    for document in documents:
        operations.append({'index':{'_index':'workouts'}})
        operations.append(document)
    es.bulk(operations=operations)
