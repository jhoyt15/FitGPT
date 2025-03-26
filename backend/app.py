from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from elasticsearch import Elasticsearch
from data.dataLoader import make_index
import firebase_admin
from firebase_admin import credentials, auth
from src.workout_generator import generate_workout_plan
from src.workout_history import get_workout_history, save_workout_history, clear_workout_history
from functools import wraps

# Load environment variables from .env file
load_dotenv()

# Initialize Firebase Admin
FIREBASE_CRED_PATH = os.getenv('FIREBASE_CRED_PATH')
if not FIREBASE_CRED_PATH:
    raise ValueError("FIREBASE_CRED_PATH environment variable is not set. Please set it to your Firebase service account JSON file path.")

if not os.path.exists(FIREBASE_CRED_PATH):
    raise FileNotFoundError(f"Firebase credentials file not found at {FIREBASE_CRED_PATH}. Please ensure the file exists and the path is correct.")

cred = credentials.Certificate(FIREBASE_CRED_PATH)
firebase_admin.initialize_app(cred)

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")
ELASTICSEARCH_USER = os.getenv("ELASTICSEARCH_USER")
ELASTICSEARCH_PASSWORD = os.getenv("ELASTICSEARCH_PASSWORD")
ELASTICSEARCH_API_KEY = os.getenv("ELASTICSEARCH_API_KEY")

# Initialize Elasticsearch client
es = Elasticsearch("http://elasticsearch:9200")

# Initialize Flask app
app = Flask(__name__)

# Custom decorator for CORS
def add_cors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            resp = app.make_response("")
            resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
            resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
            resp.headers['Access-Control-Allow-Credentials'] = 'true'
            return resp
        
        # Get response from the actual endpoint function
        response = f(*args, **kwargs)
        
        # Handle both tuple responses (data, status_code) and direct response objects
        if isinstance(response, tuple):
            resp, status_code = response
            if isinstance(resp, dict):
                resp = jsonify(resp)
                resp.status_code = status_code
            else:
                # Already a response object
                pass
        else:
            resp = response
            
        # Add CORS headers
        if isinstance(resp, str):
            resp = app.make_response(resp)
            
        resp.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
        resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        resp.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept'
        resp.headers['Access-Control-Allow-Credentials'] = 'true'
        
        return resp
    return decorated_function

# Apply CORS to all routes
@app.after_request
def add_cors_headers(response):
    # Always add these headers to every response
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# Handle OPTIONS requests globally
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    response = jsonify({'status': 'success'})
    return response, 200

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
@add_cors
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/auth/google", methods=['POST', 'OPTIONS'])
@add_cors
def google_auth():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'success'}), 200
            
        print("Google auth request received")
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
        else:
            # Handle form submission
            data = request.form.to_dict()
        
        if not data:
            print("No data received in Google auth request")
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
            
        token = data.get('token')
        if not token:
            print("No token provided in Google auth request")
            return jsonify({'status': 'error', 'message': 'No token provided'}), 400

        # Verify the Firebase token
        try:
            print("Verifying Firebase token")
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            print(f"Token verified successfully for user {uid}")
        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Token verification failed: {str(e)}'}), 401

        # Get user data - prefer from request body but fallback to token
        email = data.get('email') or decoded_token.get('email')
        name = data.get('name') or decoded_token.get('name')
        picture = data.get('profile_pic') or decoded_token.get('picture')

        # Here you would typically:
        # 1. Check if user exists in your database
        # 2. Create/update user if needed
        # 3. Create a session or JWT for your backend
        print(f"Creating user data for {email}")
        user_data = {
            'id': uid,
            'email': email,
            'name': name,
            'profile_pic': picture
        }

        print("Google auth completed successfully")
        
        # For form submissions, return HTML instead of JSON
        if not request.is_json:
            return f"""
            <html>
            <body>
                <script>
                    window.parent.postMessage({{'status': 'success', 'userId': '{uid}'}}, '*');
                </script>
                <p>Authentication successful</p>
            </body>
            </html>
            """
        
        return jsonify({
            'status': 'success',
            'user': user_data
        })

    except Exception as e:
        print(f"Error in google_auth: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/auth/logout", methods=['GET', 'OPTIONS'])
@add_cors
def logout():
    if request.method == 'OPTIONS':
        return jsonify({'status': 'success'}), 200
    
    # Here you would typically:
    # 1. Clear any backend session
    # 2. Invalidate any backend tokens
    return jsonify({'status': 'success'})

@app.route("/auth/delete-account", methods=['DELETE', 'GET', 'OPTIONS', 'POST'])
@add_cors
def delete_account():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'success'}), 200
            
        print("Delete account request received via", request.method)
        
        # Get token from query params or request body
        if request.method == 'GET':
            token = request.args.get('token')
        else:
            # For POST or DELETE with body (beacon sends as POST)
            try:
                data = request.get_json(silent=True)
                if data:
                    token = data.get('token')
                else:
                    # Try to get from form data
                    token = request.form.get('token')
                    if not token:
                        # Last resort, try query params
                        token = request.args.get('token')
            except Exception as e:
                print(f"Error parsing request data: {str(e)}")
                token = request.args.get('token')  # Fallback
        
        if not token:
            print("No token provided in delete account request")
            return jsonify({'status': 'error', 'message': 'No token provided'}), 400
        
        # Verify the Firebase token
        try:
            decoded_token = auth.verify_id_token(token)
            uid = decoded_token['uid']
            print(f"Token verified successfully for user {uid}")
        except Exception as e:
            print(f"Token verification failed: {str(e)}")
            return jsonify({'status': 'error', 'message': f'Token verification failed: {str(e)}'}), 401
        
        # Delete user data from Elasticsearch
        try:
            print(f"Deleting workout history for user {uid}")
            es.delete_by_query(
                index='workout_history',
                query={'match': {'user_id': uid}},
                refresh=True
            )
            print("Workout history deleted successfully")
        except Exception as e:
            print(f"Error deleting workout history: {str(e)}")
            # Continue even if ES deletion fails
        
        # Delete the Firebase user - commented out to prevent accidental deletion during testing
        # auth.delete_user(uid)
        
        print("Account deletion completed successfully")
        return jsonify({
            'status': 'success',
            'message': 'Account deleted successfully'
        })
    except Exception as e:
        print(f"Error deleting account: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route("/auth/delete-account-silent", methods=['POST', 'OPTIONS'])
@add_cors
def delete_account_silent():
    try:
        if request.method == 'OPTIONS':
            return jsonify({'status': 'success'}), 200
            
        print("Silent delete account request received")
        
        # Parse the request body as text and then as JSON
        try:
            body = request.get_data(as_text=True)
            data = {}
            if body:
                import json
                try:
                    data = json.loads(body)
                except:
                    print("Failed to parse JSON body, continuing anyway")
            
            token = data.get('token')
            
            if token:
                try:
                    # Verify the token
                    decoded_token = auth.verify_id_token(token)
                    uid = decoded_token['uid']
                    
                    # Delete user data from Elasticsearch
                    try:
                        es.delete_by_query(
                            index='workout_history',
                            query={'match': {'user_id': uid}},
                            refresh=True
                        )
                        print(f"Successfully deleted workout history for user {uid}")
                    except Exception as e:
                        print(f"Error deleting workout history: {str(e)}")
                        # Continue even if deletion fails
                except Exception as e:
                    print(f"Token verification failed in silent endpoint: {str(e)}")
                    # Continue even if verification fails
        except Exception as e:
            print(f"Error processing silent deletion request: {str(e)}")
            # Continue even if processing fails
        
        # Always return success to prevent console errors
        response = app.make_response("OK")
        response.status_code = 200
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'  # Allow all origins for this endpoint
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        return response
        
    except Exception as e:
        print(f"Unexpected error in silent endpoint: {str(e)}")
        # Still return success to prevent console errors
        response = app.make_response("OK")
        response.status_code = 200
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

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