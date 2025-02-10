import json
import csv
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain.docstore.document import Document
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

FILE = os.getenv("FILE",'data/exerciseData.json')
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL","http://localhost:9200")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER","")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD","")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API","")

es_connection = Elasticsearch(ELASTICSEARCH_URL)#,basic_auth=[ELASTICSEARCH_USER,ELASTICSEARCH_PASSWORD])


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

def make_index()->None:
    '''Make/Update the ElasticSearch index using the data in the json file'''

    es_connection.indices.delete(index='workouts',ignore_unavailable=True)
    es_connection.indices.create(index='workouts')

    operations = []
    with open(FILE,'rt') as file:
        documents = json.loads(file.read())
    for document in documents:
        operations.append({'index':{'_index':'workouts'}})
        operations.append(document)
    es_connection.bulk(operations=operations)


def get_embedding_model():
    '''Initalizes the HuggingFace embedding model'''
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    return embedding

def make_rag_index()->None:
    embedding = get_embedding_model()
    print('Got Model')

    metadata_keys = ["id","Desc","Type","BodyPart","Equipment","Level","Rating","RatingDesc"]
    workouts = []
    with open(FILE,'rt') as file:
        for document in json.loads(file.read()):
            workouts.append(
                Document(page_content=document["Title"],
                metadata={key: document.get(key) for key in metadata_keys})
            )
    
    es_connection.indices.delete(index='workouts_rag',ignore_unavailable=True)

    ElasticsearchStore.from_documents(
        documents=workouts,
        es_connection=es_connection,
        index_name='workouts_rag',
        embedding=embedding
    )
    print('Done')