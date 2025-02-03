from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from data.dataLoader import make_index, make_rag_index

load_dotenv()
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")


app = Flask(__name__)
CORS(app)
es = Elasticsearch(ELASTICSEARCH_URL,basic_auth=[ELASTICSEARCH_USER,ELASTICSEARCH_PASSWORD])


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

@app.cli.command()
def rag():
    make_rag_index()