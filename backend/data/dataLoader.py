import json
import csv
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain.docstore.document import Document
from langchain_community.vectorstores.elasticsearch import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings

load_dotenv()

FILE = os.getenv("FILE", 'data/exerciseData.json')
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

es_connection = Elasticsearch("http://elasticsearch:9200",verify_certs=False)

es_connection = Elasticsearch(ELASTICSEARCH_URL,verify_certs=False)

def make_json(data_path: str, json_path: str) -> None:
    # Create a dictionary
    data = []
    
    # Open a csv reader called DictReader
    with open(data_path, encoding='utf-8') as csvf:
        csvReader = csv.DictReader(csvf)
        data = []  
        for row in csvReader:
            row['Title'] = f"{row['Title']} {row['Equipment']} {row['Level']} {row['BodyPart']} {row['Type']}"
            data.append(row)
    
    # Open a json writer, and use the json.dumps() 
    # function to dump data
    with open(json_path, 'w', encoding='utf-8') as jsonf:
        jsonf.write(json.dumps(data, indent=4))

def make_index():
    es = Elasticsearch(
        ELASTICSEARCH_URL,
        verify_certs=False
    )
    
    # Define mapping for workout data
    workouts_mapping = {
        "mappings": {
            "properties": {
                "Title": {"type": "text"},
                "Description": {"type": "text"},
                "Type": {"type": "keyword"},
                "Equipment": {"type": "keyword"},
                "Level": {"type": "keyword"},
                "BodyPart": {"type": "keyword"}
            }
        }
    }
    
    # Define mapping for workout history
    history_mapping = {
        "mappings": {
            "properties": {
                "user_id": {"type": "keyword"},
                "workout_plan": {"type": "object"},
                "timestamp": {"type": "date"},
                "query": {"type": "text"}
            }
        }
    }
    
    # Create the workouts index with mapping
    try:
        es.indices.delete(index='workouts', ignore_unavailable=True)
    except Exception as e:
        print(f"Error deleting workouts index: {str(e)}")
    
    es.indices.create(index='workouts', body=workouts_mapping)
    
    # Create the workout_history index with mapping
    try:
        es.indices.delete(index='workout_history', ignore_unavailable=True)
    except Exception as e:
        print(f"Error deleting workout_history index: {str(e)}")
    
    es.indices.create(index='workout_history', body=history_mapping)
    
    # Load workout data from JSON file
    try:
        with open(FILE, 'rt') as file:
            workouts = json.loads(file.read())
            
            # Get unique equipment types
            equipment_types = set()
            for workout in workouts:
                equipment_types.add(workout.get('Equipment', ''))
            print("Available equipment types:", sorted(list(equipment_types)))
            
            # Index the workouts
            for workout in workouts:
                # Format the workout data
                formatted_workout = {
                    "Title": workout.get('Title', ''),
                    "Description": workout.get('Desc', ''),
                    "Type": workout.get('Type', ''),
                    "Equipment": workout.get('Equipment', ''),
                    "Level": workout.get('Level', ''),
                    "BodyPart": workout.get('BodyPart', '')
                }
                es.index(index='workouts', document=formatted_workout)
        
        # Refresh the indices
        es.indices.refresh(index='workouts')
        es.indices.refresh(index='workout_history')
        print(f"Successfully indexed {len(workouts)} workouts")
        print(f"Successfully created workout_history index")
        
    except Exception as e:
        print(f"Error loading workouts: {str(e)}")
        # Add some sample workouts as fallback
        workouts = [
            {
                "Title": "Push-up Workout",
                "Description": "Classic chest and triceps workout",
                "Type": "Strength",
                "Equipment": "Bodyweight",
                "Level": "Beginner",
                "BodyPart": "Chest"
            },
            {
                "Title": "Basic Chest Workout",
                "Description": "Fundamental chest exercises for beginners",
                "Type": "Strength",
                "Equipment": "Dumbbells",
                "Level": "Beginner",
                "BodyPart": "Chest"
            }
        ]
        
        # Index the sample workouts
        for workout in workouts:
            es.index(index='workouts', document=workout)
        
        # Refresh the indices
        es.indices.refresh(index='workouts')
        es.indices.refresh(index='workout_history')
        print("Indexed sample workouts as fallback")
        print("Created workout_history index")

def get_embedding_model():
    '''Initalizes the HuggingFace embedding model'''
    embedding = HuggingFaceEmbeddings(model_name="sentence-transformers/all-mpnet-base-v2")
    return embedding

def make_rag_index():
    """Create and populate the RAG-enabled index with comprehensive workout data"""
    embedding = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2"
    )
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

def new_rag_index():
    """Create and populate the RAG-enabled index with comprehensive workout data"""
    embedding = get_embedding_model()
    print('Initializing embedding model...')

    # Define the metadata keys we want to preserve
    metadata_keys = [
        "Equipment",
        "Variation",
        "Utility",
        "Mechanics",
        "Force",
        "Preparation",
        "Execution",
        "Target_Muscles",
        "Synergist_Muscles",
        "Stabilizer_Muscles",
        "Antagonist_Muscles",
        "Dynamic_Stabilizer_Muscles",
        "Main_muscle",
        "Difficulty (1-5)",
        "Secondary Muscles",
        "parent_id"
    ]

    # Load workout data from JSON file
    workouts = []
    with open('data/gym_exercise_dataset.json', 'rt') as file:
        for document in json.loads(file.read()):
            # Create a more detailed title that includes key information
            #enhanced_title = f"{document['Title']} - {document['Type']} workout for {document['Level']} level, targeting {document['BodyPart']} using {document['Equipment']}"
            
            workouts.append(
                Document(
                    page_content=document['Exercise Name'],
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
    new_rag_index()