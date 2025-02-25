from flask import Flask, request, jsonify, make_response, Response
from flask_cors import CORS
import os
from elasticsearch import Elasticsearch
from data.dataLoader import make_index, make_rag_index
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_elasticsearch import ElasticsearchStore
from langchain_huggingface import HuggingFaceEmbeddings
import click

app = Flask(__name__)
CORS(app)
es = Elasticsearch("http://elasticsearch:9200")

# Initialize the embedding model and vector store
embedding_model = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-mpnet-base-v2"
)
vector_store = ElasticsearchStore(
    es_connection=es,
    index_name="workouts_rag",
    embedding=embedding_model
)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/query", methods=['POST'])
def query_es():
    if request.method == 'POST':
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"Error":"Invalid Request"}), 400
        
        user_query = data["query"]
        print(f"Received query: {user_query}")  # Debug print
        
        try:
            # Search for relevant workouts based on user input
            results = vector_store.similarity_search(
                user_query,
                k=5  # Number of relevant workouts to retrieve
            )
            print(f"Found {len(results)} results")  # Debug print
            
            # Format the results
            formatted_results = []
            for doc in results:
                workout = {
                    "_source": {
                        "Title": doc.page_content,
                        "Description": doc.metadata.get("Desc", ""),
                        "Type": doc.metadata.get("Type", ""),
                        "Equipment": doc.metadata.get("Equipment", ""),
                        "Level": doc.metadata.get("Level", ""),
                        "BodyPart": doc.metadata.get("BodyPart", "")
                    }
                }
                formatted_results.append(workout)
            
            print(f"Formatted {len(formatted_results)} results")  # Debug print
            return jsonify({'response': formatted_results})
        except Exception as e:
            print(f"Error in query_es: {str(e)}")  # Debug print
            return jsonify({"Error": str(e)}), 500

@app.cli.command("init-db")
@click.command('init-db')
def init_db():
    """Initialize the database with workout data and create RAG index"""
    print("Starting database initialization...")
    try:
        make_index()  # Create regular index
        print("Basic index created")
        make_rag_index()  # Create RAG-enabled index
        print("RAG index created")
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise e

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)