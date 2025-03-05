import os
import sys
from flask import stream_template_string
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from langchain_elasticsearch import ElasticsearchStore
from langchain_mistralai import ChatMistralAI
from fuzzywuzzy import process
from jinja2 import Template
from langchain_elasticsearch import ElasticsearchChatMessageHistory

basedir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(f"{basedir}/../")
from data.dataLoader import get_embedding_model


load_dotenv()
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL","http://localhost:9200")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER","")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD","")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY","")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

if not MISTRAL_API_KEY:
    sys.exit("Please put the Mistral API key in the .env file!")

es = Elasticsearch(ELASTICSEARCH_URL)
doc_store = ElasticsearchStore(es_connection=es,index_name='workouts_rag',embedding=get_embedding_model())

llm = ChatMistralAI(model_name="mistral-small-latest",api_key=MISTRAL_API_KEY)

def prompt_llm(question:str,session_id:int):
    '''Prompts the LLM and Elasticsearch with the users question and returns a response'''
    #Get chat history
    chat_history = get_chat_history('workouts_rag',session_id)
    if(len(chat_history.messages) > 0):
        with open("./src/templates/condensed_question.txt") as file:
            condensed_template = file.read()
        question = Template(condensed_template).render(chat_history) #Condense chat history down to one question to reduce input size


    documents = []
    workout_split = get_workout_split(question)
    if workout_split:
        split_days = workout_split["days"]
        for day,muscle_groups in split_days.items():
            for muscle in muscle_groups:
                documents.extend(doc_store.similarity_search(muscle,k=2))
        
    with open("./src/templates/rag_prompt.txt") as file:
        template = file.read()
    template = Template(template)

    full_rag_question = template.render(question=question,documents=documents,workout_split=workout_split)

    answer = llm.invoke(full_rag_question)

    chat_history.add_user_message(question)
    chat_history.add_ai_message(answer)

    return answer.content

def get_chat_history(index_name:str,session_id:int):
    return ElasticsearchChatMessageHistory(es_connection=es,index=index_name,session_id=session_id)


def get_workout_split(question:str)->dict:
    '''Gets the muscle groups trained each day in a named workout split'''
    WORKOUT_SPLITS = {
        "arnold": {
            "name": "Arnold Split",
            "days": {
                "Day 1": ["Chest", "Back"],
                "Day 2": ["Shoulders", "Bicep","Tricep"],
                "Day 3": ["Legs"],
                "Day 4": ["Chest", "Back"],
                "Day 5": ["Shoulders","Bicep","Tricep"],
                "Day 6": ["Legs"]
            }
        },
        "push pull legs": {
            "name": "Push Pull Legs",
            "days": {
                "Day 1": ["Chest", "Shoulders", "Triceps"],
                "Day 2": ["Back", "Biceps"],
                "Day 3": ["Legs"],
                "Day 4": ["Chest", "Shoulders", "Triceps"],
                "Day 5": ["Back", "Biceps"],
                "Day 6": ["Legs"]
            }
        },
        "upper lower": {
            "name": "Upper Lower Split",
            "days": {
                "Day 1": ["Chest","Shoulders","Bicep","Tricep","Back"],
                "Day 2": ["Legs","Hips"],
                "Day 3": ["Chest","Shoulders","Bicep","Tricep","Back"],
                "Day 4": ["Legs","Hips"]
            }
        },
        "full body": {
            "name": "Full Body",
            "days": {
                "Day 1": ["Chest","Shoulders","Bicep","Tricep","Back","Legs"],
                "Day 2": ["Chest","Shoulders","Bicep","Tricep","Back","Legs"],
                "Day 3": ["Chest","Shoulders","Bicep","Tricep","Back","Legs"]
            }
        },
        "bro":{
            "name": "Bro Split",
            "days": {
                "Day 1": ["Chest"],
                "Day 2:": ["Back"],
                "Day 3:": ["Shoulders"],
                "Day 4:": ["Arms"],
                "Day 5:": ["Legs"]
            }
        }
    }

    splits = list(WORKOUT_SPLITS.keys())
    match,score = process.extractOne(question,splits)

    if score > 80:
        return WORKOUT_SPLITS[match]
    else:
        return None
    
#prompt_llm("Give me an workout plan using the push pull legs split")