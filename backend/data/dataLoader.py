import json
import csv
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, NotFoundError
from langchain.docstore.document import Document
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface import HuggingFaceEmbeddings

load_dotenv()

FILE = os.getenv("FILE", 'data/exerciseData.json')
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API")

es_connection = Elasticsearch("http://elasticsearch:9200")


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

def make_index():
    es = Elasticsearch("http://elasticsearch:9200")
    
    # Define mapping for workout data
    mapping = {
        "mappings": {
            "properties": {
                "Title": {"type": "text"},
                "Description": {"type": "text"},
                "Type": {"type": "keyword"},
                "Difficulty": {"type": "keyword"}
            }
        }
    }
    
    # Create the index with mapping
    es.indices.create(index='workouts', body=mapping, ignore=400)
    
    # Sample workout data
    workouts = [
        {
            "Title": "Push-up Workout",
            "Description": "Classic chest and triceps workout",
            "Type": "Strength",
            "Difficulty": "Beginner"
        },
        {
            "Title": "Basic Chest Workout",
            "Description": "Fundamental chest exercises for beginners",
            "Type": "Strength",
            "Difficulty": "Beginner"
        },
        {
            "Title": "Advanced Chest Training",
            "Description": "Intense chest workout for experienced athletes",
            "Type": "Strength",
            "Difficulty": "Advanced"
        }
    ]
    
    # Index the workouts
    for workout in workouts:
        es.index(index='workouts', document=workout)
    
    # Refresh the index
    es.indices.refresh(index='workouts')

def get_embedding_model()->HuggingFaceEmbeddings:
    '''Initalizes the HuggingFace embedding model'''
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    return embedding

def make_rag_index():
    """Create and populate the RAG-enabled index with comprehensive workout data"""
    embedding = get_embedding_model()
    print('Initializing embedding model...')

    # Define the metadata keys we want to preserve
    metadata_keys = [
        "id", "Desc", "Type", "BodyPart", "Equipment", 
        "Level", "Rating", "RatingDesc"
    ]

    # Load workout data from JSON file
    workouts = []
    with open(FILE, 'rt') as file:
        for document in json.loads(file.read()):
            # Create a more detailed title that includes key information
            enhanced_title = f"{document['Title']} - {document['Type']} workout for {document['Level']} level, targeting {document['BodyPart']} using {document['Equipment']}"
            
            workouts.append(
                Document(
                    page_content=enhanced_title,
                    metadata={key: document.get(key) for key in metadata_keys}
                )
            )
    
    # Delete existing index if it exists
    es_connection.indices.delete(index='workouts_rag', ignore_unavailable=True)

    # Create new index with the workout documents
    ElasticsearchStore.from_documents(
        documents=workouts,
        es_connection=es_connection,
        index_name='workouts_rag',
        embedding=embedding
    )
    print('RAG index created successfully')

if __name__ == "__main__":
    make_rag_index()