from flask import Flask, request, jsonify
import os
from elasticsearch import Elasticsearch
from data.dataLoader import make_index

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")


app = Flask(__name__)
es = Elasticsearch(ELASTICSEARCH_URL,basic_auth=[ELASTICSEARCH_USER,ELASTICSEARCH_PASSWORD],api_key=ELASTICSEARCH_API_KEY,ca_certs='cert.crt')


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
    make_index(es)
    print('Done')

@app.cli.command()
def check():
    result = es.search(index='workouts',query={
            'match': {
                'Title': {
                    'query': "Barbell Chest"
                }
            }
        }
    )
    print(result['hits']['hits'])
