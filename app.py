from flask import Flask
import os
from elasticsearch import Elasticsearch
from data.dataLoader import make_index

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

# Initialize Elasticsearch client
es = Elasticsearch("http://elasticsearch:9200")

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.cli.command()
def reindex():
    es = Elasticsearch(ELASTICSEARCH_URL,basic_auth=[ELASTICSEARCH_USER,ELASTICSEARCH_PASSWORD],api_key=ELASTICSEARCH_API_KEY,ca_certs='cert.crt')
    make_index(es)
    print('Done')

@app.cli.command()
def check():
    es = Elasticsearch(ELASTICSEARCH_URL,basic_auth=[ELASTICSEARCH_USER,ELASTICSEARCH_PASSWORD],api_key=ELASTICSEARCH_API_KEY,ca_certs='cert.crt')
    result = es.search(index='workouts',query={
            'match': {
                'Title': {
                    'query': "Barbell Chest"
                }
            }
        }
    )
    print(result['hits']['hits'])
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
    