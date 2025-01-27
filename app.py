from flask import Flask
from elasticsearch import Elasticsearch

# Initialize Elasticsearch client
es = Elasticsearch("http://elasticsearch:9200")

# Initialize Flask app
app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)