from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from elasticsearch import Elasticsearch
from data.dataLoader import make_index
import firebase_admin
from firebase_admin import credentials, auth
from src.workout_generator import generate_workout_plan
from src.workout_history import get_workout_history, save_workout_history, clear_workout_history

# Initialize Firebase Admin
cred = credentials.Certificate('fitgpt-32ad7-firebase-adminsdk-fbsvc-0557ed928e.json')
firebase_admin.initialize_app(cred)

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

# Initialize Elasticsearch client
es = Elasticsearch("http://elasticsearch:9200")

# Initialize Flask app
app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": ["http://localhost:3000"]}}, supports_credentials=True)

def verify_token():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split('Bearer ')[1]
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Token verification error: {str(e)}")
        return None

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/auth/google", methods=['POST'])
def google_auth():
    try:
        data = request.get_json()
        token = data.get('token')
        if not token:
            return jsonify({'status': 'error', 'message': 'No token provided'}), 400

        # Verify the Firebase token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token['uid']
        email = decoded_token.get('email')
        name = decoded_token.get('name')
        picture = decoded_token.get('picture')

        # Here you would typically:
        # 1. Check if user exists in your database
        # 2. Create/update user if needed
        # 3. Create a session or JWT for your backend

        user_data = {
            'uid': uid,
            'email': email,
            'name': name,
            'profile_pic': picture
        }

        return jsonify({
            'status': 'success',
            'user': user_data
        })

    except Exception as e:
        print(f"Error in google_auth: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/auth/logout", methods=['GET'])
def logout():
    # Here you would typically:
    # 1. Clear any backend session
    # 2. Invalidate any backend tokens
    return jsonify({'status': 'success'})

@app.route("/user/workout-history", methods=['GET', 'DELETE'])
def workout_history():
    try:
        decoded_token = verify_token()
        if not decoded_token:
            return jsonify({'status': 'error', 'message': 'Invalid or missing token'}), 401

        uid = decoded_token['uid']
        
        if request.method == 'DELETE':
            # Clear workout history
            clear_workout_history(uid)
            return jsonify({
                'status': 'success',
                'message': 'Workout history cleared successfully'
            })
        else:
            # Get workout history
            history = get_workout_history(uid)
            return jsonify({
                'status': 'success',
                'history': history
            })
    except Exception as e:
        print(f"Error with workout history: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/query", methods=['POST'])
def query():
    try:
        decoded_token = verify_token()
        if not decoded_token:
            return jsonify({'status': 'error', 'message': 'Invalid or missing token'}), 401

        data = request.get_json()
        query_text = data.get('query')
        if not query_text:
            return jsonify({'status': 'error', 'message': 'No query provided'}), 400

        # Generate workout plan
        workout_plan = generate_workout_plan(query_text)
        
        # Save to history
        uid = decoded_token['uid']
        save_workout_history(uid, workout_plan, query_text)

        return jsonify({
            'status': 'success',
            'workout_plan': workout_plan
        })
    except Exception as e:
        print(f"Error generating workout: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.cli.command()
def reindex():
    # Using the local ES instance without authentication
    from data.dataLoader import make_index
    make_index()
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