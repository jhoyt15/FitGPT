from flask import Flask, request
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
        query = request.form['query']
        result = es.search(index='workouts',query={
            'match': {
                'Title': {
                    'query': query
                }
            }
        })
        return {'response':result['hit']['hit']}

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
