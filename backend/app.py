from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from data.dataLoader import make_index, make_rag_index, get_embedding_model
from langchain_elasticsearch import ElasticsearchStore

load_dotenv()
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL","http://localhost:9200")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER","")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD","")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY","")


app = Flask(__name__)
CORS(app)
es = Elasticsearch(ELASTICSEARCH_URL)#,basic_auth=[ELASTICSEARCH_USER,ELASTICSEARCH_PASSWORD])
doc_store = ElasticsearchStore(es_connection=es,index_name='workouts_rag',embedding=get_embedding_model())


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/query",methods=['POST'])
def query_es():
    if request.method == 'POST':
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"Error":"Invalid Request"}),400
        query = data["query"]
        result = es.search(index='workouts',query={
            'match': {
                'Title': {
                    'query': query
                }
            }
        })
        return jsonify({'response':result['hits']['hits']})

@app.cli.command()
def reindex():
    make_index()
    print('Done')

@app.cli.command()
def check():
    result = es.search(index='workouts',query={
            'match': {
                'Title': {
                    'query': "Chest"
                }
            }
        }
    )
    print(result['hits']['hits'])
    print(result)

@app.cli.command("rag-reindex")
def rag_reindex():
    make_rag_index()

@app.cli.command("rag-check")
def rag_check():
    docs = doc_store.as_retriever().invoke("Chest")
    print(docs)