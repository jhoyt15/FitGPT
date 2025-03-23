from flask import Flask, request, jsonify, make_response, Response, stream_with_context
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from google.oauth2 import id_token
from google.auth.transport import requests
from elasticsearch import Elasticsearch
from data.dataLoader import make_index, make_rag_index
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_elasticsearch import ElasticsearchStore
from langchain_community.embeddings import HuggingFaceEmbeddings
import click
import sys
from src.chat import prompt_llm
from advisors.mistral_advisor import MistralWorkoutAdvisor
import time
import json
import re
from models import User, WorkoutHistory
import os

app = Flask(__name__)
CORS(app, 
     resources={r"/*": {
         "origins": ["http://localhost:3000"],  # Frontend URL
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"],
         "supports_credentials": True
     }})

app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')  # Change this in production

# Initialize Elasticsearch client with specific settings
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
es = Elasticsearch(
    ELASTICSEARCH_URL,
    verify_certs=False,
    request_timeout=30,
    headers={"Content-Type": "application/json"}
)

# Google OAuth config
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    # Fetch user from Elasticsearch
    try:
        user_doc = es.get(index='users', id=user_id)
        return User.from_dict(user_doc['_source'])
    except:
        return None

# Create indices for users and workout history if they don't exist
user_index_settings = {
    "mappings": {
        "properties": {
            "email": {"type": "keyword"},
            "name": {"type": "text"},
            "profile_pic": {"type": "text"}
        }
    }
}

workout_history_index_settings = {
    "mappings": {
        "properties": {
            "user_id": {"type": "keyword"},
            "workout_plan": {"type": "object"},
            "created_at": {"type": "date"}
        }
    }
}

try:
    if not es.indices.exists(index='users'):
        es.indices.create(index='users', body=user_index_settings)
    if not es.indices.exists(index='workout_history'):
        es.indices.create(index='workout_history', body=workout_history_index_settings)
except Exception as e:
    print(f"Error creating indices: {str(e)}")

# Initialize the embedding model
try:
    embedding_model = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-mpnet-base-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
except Exception as e:
    print(f"Error initializing embedding model: {str(e)}")
    embedding_model = None

# Initialize vector store only if embedding model is available
if embedding_model:
    try:
        vector_store = ElasticsearchStore(
            es_connection=es,
            index_name="workouts",
            embedding=embedding_model
        )
        print("Vector store initialized successfully")
    except Exception as e:
        print(f"Error initializing vector store: {str(e)}")
        vector_store = None
else:
    vector_store = None
    print("Vector store not initialized because embedding model failed to load")

# Initialize Mistral advisor
if not os.getenv('MISTRAL_API_KEY'):
    raise EnvironmentError("MISTRAL_API_KEY environment variable is not set")
mistral_advisor = MistralWorkoutAdvisor()

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
        print(f"\n=== New Search Request ===")
        print(f"Raw user query: {user_query}")
        
        try:
            # First, check if we have any data in the index
            count_response = es.count(index="workouts")
            print(f"\nIndex stats:")
            print(f"Total documents in index: {count_response.body.get('count', 0)}")
            
            # Get index mapping to verify our field structure
            mapping = es.indices.get_mapping(index="workouts")
            print(f"\nIndex mapping:")
            print(json.dumps(mapping.body, indent=2))
            
            # Use Mistral to understand the query
            query_messages = [
                {
                    "role": "system",
                    "content": "Analyze this workout request and extract the key details in JSON format. Return ONLY the JSON object, no explanations or additional text."
                },
                {
                    "role": "user",
                    "content": f"""
                    Request: {user_query}
                    
                    Return a JSON object with these fields:
                    - body_parts: list of target body parts (use standard names like "Abdominals", "Chest", "Quadriceps", etc.)
                    - equipment: list of required equipment (use standard names like "Body Only", "Dumbbell", "Barbell", etc.)
                    - level: skill level ("Beginner", "Intermediate", or "Advanced")
                    - workout_type: type of workout ("Strength", "Cardio", "Stretching", etc.)
                    - days_per_week: number of workout days per week (integer)
                    - minutes_per_session: number of minutes per workout session (integer)
                    
                    Return ONLY the JSON object, no explanations or additional text.
                    """
                }
            ]
            
            # Get structured understanding of the query
            try:
                print("\nSending request to Mistral API...")
                response = mistral_advisor.client.chat.complete(
                    model="mistral-tiny",
                    messages=query_messages,
                    temperature=0.7,
                    max_tokens=300
                )
                parsed_query = response.choices[0].message.content.strip()
                print("\nMistral parsing result:")
                print(f"Raw parsed query: {parsed_query}")
            except Exception as e:
                print(f"\nError calling Mistral API: {str(e)}")
                print(f"Error type: {type(e)}")
                # Fallback to a simple query if Mistral fails
                print("\nFalling back to simple query structure...")
                query_details = {
                    "body_parts": ["Chest"],
                    "equipment": ["Dumbbell"],
                    "level": "Beginner",
                    "workout_type": "Strength"
                }
                print(f"Using fallback query details: {json.dumps(query_details, indent=2)}")
            else:
                try:
                    # Try to extract just the JSON part using regex
                    json_match = re.search(r'\{.*\}', parsed_query, re.DOTALL)
                    if json_match:
                        parsed_query = json_match.group()
                    
                    print(f"Cleaned parsed query: {parsed_query}")
                    
                    # Parse the JSON response
                    query_details = json.loads(parsed_query)
                    print("\nParsed query details:")
                    print(json.dumps(query_details, indent=2))
                except Exception as e:
                    print(f"\nError parsing Mistral response: {str(e)}")
                    print(f"Error type: {type(e)}")
                    # Fallback to a simple query if parsing fails
                    print("\nFalling back to simple query structure...")
                    query_details = {
                        "body_parts": ["Chest"],
                        "equipment": ["Dumbbell"],
                        "level": "Beginner",
                        "workout_type": "Strength"
                    }
                    print(f"Using fallback query details: {json.dumps(query_details, indent=2)}")
            
            # Update equipment mapping with more comprehensive options
            if query_details.get("equipment"):
                equipment_mapping = {
                    # No equipment variations
                    "Basic Equipment": "Body Only",
                    "Bodyweight": "Body Only",
                    "None": "Body Only",
                    "No Equipment": "Body Only",
                    "Just Body": "Body Only",
                    
                    # Basic equipment variations
                    "Mat": "Other",
                    "Yoga Mat": "Other",
                    "Exercise Mat": "Other",
                    "Foam Roller": "Other",
                    
                    # Resistance bands variations
                    "Band": "Bands",
                    "Resistance Band": "Bands",
                    "Elastic Band": "Bands",
                    
                    # Dumbbell variations
                    "Dumbbells": "Dumbbell",
                    "Hand Weights": "Dumbbell",
                    "Free Weights": "Dumbbell",
                    
                    # Barbell variations
                    "Bar": "Barbell",
                    "Olympic Bar": "Barbell",
                    "Weight Bar": "Barbell",
                    
                    # Cable variations
                    "Cables": "Cable",
                    "Cable Machine": "Cable",
                    "Pulley": "Cable",
                    
                    # Kettlebell variations
                    "Kettle Bell": "Kettlebell",
                    "KB": "Kettlebell",
                    
                    # Machine variations
                    "Exercise Machine": "Machine",
                    "Gym Machine": "Machine",
                    "Weight Machine": "Machine"
                }
                
                mapped_equipment = []
                for e in query_details["equipment"]:
                    # Try exact match first
                    mapped = equipment_mapping.get(e)
                    if mapped:
                        mapped_equipment.append(mapped)
                    else:
                        # Try case-insensitive match
                        e_lower = e.lower()
                        for key, value in equipment_mapping.items():
                            if key.lower() == e_lower:
                                mapped_equipment.append(value)
                                break
                        else:
                            # If no match found, keep original
                            mapped_equipment.append(e)
                
                query_details["equipment"] = mapped_equipment
                print("\nMapped equipment:")
                print(query_details["equipment"])
            
            # Construct Elasticsearch query based on LLM understanding
            query = {
                "size": 20,
                "query": {
                    "bool": {
                        "should": [],
                        "minimum_should_match": 1
                    }
                }
            }
            
            # Add body part filter if specified
            if query_details.get("body_parts"):
                query["query"]["bool"]["should"].append({
                    "terms": {
                        "BodyPart.keyword": query_details["body_parts"],
                        "boost": 2.0
                    }
                })
            
            # Add equipment filter if specified
            if query_details.get("equipment"):
                # Special handling for "Body Only" to exclude other equipment types
                if "Body Only" in query_details["equipment"]:
                    query["query"]["bool"]["should"].append({
                        "bool": {
                            "must": [
                                {"term": {"Equipment.keyword": "Body Only"}}
                            ],
                            "boost": 2.0
                        }
                    })
                else:
                    query["query"]["bool"]["should"].append({
                        "terms": {
                            "Equipment.keyword": query_details["equipment"],
                            "boost": 2.0
                        }
                    })
            
            # Add level filter if specified
            if query_details.get("level"):
                query["query"]["bool"]["should"].append({
                    "match": {
                        "Level": {
                            "query": query_details["level"],
                            "boost": 1.5,
                            "fuzziness": "AUTO"
                        }
                    }
                })
            
            # Add workout type filter if specified
            if query_details.get("workout_type"):
                query["query"]["bool"]["should"].append({
                    "match": {
                        "Type": {
                            "query": query_details["workout_type"],
                            "boost": 1.5,
                            "fuzziness": "AUTO"
                        }
                    }
                })
            
            # Add general relevance matching with higher boost
            query["query"]["bool"]["should"].append({
                "multi_match": {
                    "query": user_query,
                    "fields": [
                        "Title^3",
                        "Description^2",
                        "Type^2",
                        "Level^2",
                        "Equipment^1.5",
                        "BodyPart^1.5"
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "boost": 1.0
                }
            })
            
            # Add function score to boost matches based on equipment compatibility
            if query_details.get("equipment") and "Body Only" in query_details["equipment"]:
                query["query"] = {
                    "function_score": {
                        "query": query["query"],
                        "functions": [
                            {
                                "filter": {"term": {"Equipment.keyword": "Body Only"}},
                                "weight": 3
                            },
                            {
                                "filter": {"terms": {"Equipment.keyword": ["Other", "Bands"]}},
                                "weight": 2
                            }
                        ],
                        "score_mode": "sum",
                        "boost_mode": "multiply"
                    }
                }
            
            print("\nFinal Elasticsearch query:")
            print(json.dumps(query, indent=2))
            
            # Execute search
            response = es.search(
                index="workouts",
                body=query
            )
            print("\nElasticsearch response:")
            print(json.dumps(response.body, indent=2))
            
            # If no results, try a simpler query to verify data access
            if response.body['hits']['total']['value'] == 0:
                print("\nNo results found, trying a simple match_all query...")
                simple_response = es.search(
                    index="workouts",
                    body={"query": {"match_all": {}}}
                )
                print("\nSimple query response:")
                print(json.dumps(simple_response.body, indent=2))
            
            # Format results and get AI recommendations
            formatted_results = []
            all_exercises = response.body['hits']['hits']
            
            # Get the number of days per week from query_details
            days_per_week = int(query_details.get('days_per_week', 3))
            
            # Create a workout plan structure
            workout_plan = {
                "days_per_week": days_per_week,
                "minutes_per_session": int(query_details.get('minutes_per_session', 30)),
                "level": query_details.get('level', 'Beginner'),
                "workout_days": []
            }
            
            # Organize exercises by day
            exercises_per_day = max(3, len(all_exercises) // days_per_week)
            remaining_exercises = len(all_exercises) % days_per_week
            
            current_exercise = 0
            for day in range(days_per_week):
                day_exercises = []
                exercises_this_day = exercises_per_day + (1 if day < remaining_exercises else 0)
                
                # Ensure we don't exceed available exercises
                exercises_this_day = min(exercises_this_day, len(all_exercises) - current_exercise)
                
                for _ in range(exercises_this_day):
                    if current_exercise >= len(all_exercises):
                        break
                        
                    hit = all_exercises[current_exercise]
                    source = hit['_source']
                    workout_data = {
                        "Type": source.get('Type', ''),
                        "Equipment": source.get('Equipment', ''),
                        "Level": source.get('Level', ''),
                        "BodyPart": source.get('BodyPart', '')
                    }
                    
                    # Get AI recommendations for this workout
                    try:
                        ai_advice = mistral_advisor.generate_advice(workout_data, source.get('Title', ''))
                    except Exception as e:
                        print(f"\nError getting AI advice: {str(e)}")
                        ai_advice = None
                    
                    workout = {
                        "Title": source.get('Title', ''),
                        "Description": source.get('Description', ''),
                        "Type": source.get('Type', ''),
                        "Equipment": source.get('Equipment', ''),
                        "Level": source.get('Level', ''),
                        "BodyPart": source.get('BodyPart', ''),
                        "AI_Recommendations": ai_advice
                    }
                    day_exercises.append(workout)
                    current_exercise += 1
                
                # Get day-specific advice from Mistral
                day_advice_messages = [
                    {
                        "role": "system",
                        "content": "You are a knowledgeable fitness advisor. Provide a brief overview for this workout day."
                    },
                    {
                        "role": "user",
                        "content": f"Create a brief overview for Day {day + 1} of a {days_per_week}-day workout plan. Focus on: {', '.join([ex['BodyPart'] for ex in day_exercises if ex.get('BodyPart')])}"
                    }
                ]
                
                try:
                    day_advice_response = mistral_advisor.client.chat.complete(
                        model="mistral-tiny",
                        messages=day_advice_messages,
                        temperature=0.7,
                        max_tokens=150
                    )
                    day_advice = day_advice_response.choices[0].message.content.strip()
                except Exception as e:
                    print(f"\nError getting day advice: {str(e)}")
                    day_advice = None
                
                workout_day = {
                    "day_number": day + 1,
                    "overview": day_advice,
                    "exercises": day_exercises
                }
                workout_plan["workout_days"].append(workout_day)
            
            # Get overall plan advice from Mistral
            plan_advice_messages = [
                {
                    "role": "system",
                    "content": "You are a knowledgeable fitness advisor. Provide a brief overview of this workout plan."
                },
                {
                    "role": "user",
                    "content": f"Create a brief overview for a {days_per_week}-day workout plan at {workout_plan['level']} level."
                }
            ]
            
            try:
                plan_advice_response = mistral_advisor.client.chat.complete(
                    model="mistral-tiny",
                    messages=plan_advice_messages,
                    temperature=0.7,
                    max_tokens=200
                )
                workout_plan["plan_overview"] = plan_advice_response.choices[0].message.content.strip()
            except Exception as e:
                print(f"\nError getting plan advice: {str(e)}")
                workout_plan["plan_overview"] = None
            
            print(f"\nWorkout plan generated with {len(workout_plan['workout_days'])} days")

            # After generating the workout plan, save it to history if user is logged in
            if current_user.is_authenticated:
                try:
                    workout_history = WorkoutHistory(
                        user_id=current_user.id,
                        workout_plan=workout_plan
                    )
                    es.index(
                        index='workout_history',
                        body=workout_history.to_dict()
                    )
                except Exception as e:
                    print(f"Error saving workout history: {str(e)}")
            
            return jsonify({"response": workout_plan})
            
        except Exception as e:
            print(f"\nError in query_es: {str(e)}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return jsonify({"error": "Failed to process query"}), 500

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
    
@app.route('/chat',methods=["POST"])
def ask_question():
    if request.method != "POST":
        return jsonify({"error":"Method must be post"}), 400
    data = request.get_json()
    if not data or "query" not in data or "session_id" not in data:
        return jsonify({"error":"Invalid request"}), 400
    try:
        query = data["query"]
        session_id = data["session_id"]
        answer = prompt_llm(query,session_id)  
        return jsonify({"response":answer}), 200
    except Exception as e:
        return jsonify({"error":e}), 505

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

@app.route("/test-mistral")
def test_mistral():
    try:
        test_data = {
            "Type": "Strength",
            "BodyPart": "Chest",
            "Equipment": "Bodyweight",
            "Level": "Beginner"
        }
        response = mistral_advisor.generate_advice(test_data, "Basic push-up workout")
        return jsonify({"status": "success", "response": response})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/debug/es-status")
def es_status():
    """Debug endpoint to check Elasticsearch status"""
    try:
        # Check cluster health
        health = es.cluster.health()
        health_dict = {
            "status": health["status"],
            "number_of_nodes": health["number_of_nodes"],
            "active_shards": health["active_shards"]
        }
        
        # Check if index exists
        index_exists = bool(es.indices.exists(index="workouts"))
        
        # Get document count
        count_response = es.count(index="workouts")
        doc_count = count_response.body.get("count", 0) if isinstance(count_response, dict) else 0
        
        # Get a sample document
        sample = None
        try:
            sample_response = es.search(
                index="workouts",
                body={
                    "size": 1,
                    "query": {"match_all": {}}
                }
            )
            if isinstance(sample_response, dict) and sample_response.get("hits", {}).get("hits"):
                sample = sample_response["hits"]["hits"][0]["_source"]
        except Exception as e:
            sample = str(e)
        
        status = {
            "cluster_health": health_dict,
            "index_exists": index_exists,
            "document_count": doc_count,
            "sample_document": sample
        }
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/simple-search")
def simple_search():
    """Debug endpoint to perform a simple search"""
    try:
        response = es.search(
            index="workouts",
            body={
                "size": 5,
                "query": {"match_all": {}}
            }
        )
        return jsonify(response['hits']['hits'])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/debug/reindex", methods=['POST'])
def reindex():
    """Debug endpoint to force reindex"""
    try:
        make_index()
        make_rag_index()
        return jsonify({"status": "success", "message": "Reindexing completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/test-mistral-key")
def test_mistral_key():
    """Test endpoint to verify Mistral API key is working"""
    try:
        print("\nTesting Mistral API key...")
        response = mistral_advisor.client.chat.complete(
            model="mistral-tiny",
            messages=[
                {
                    "role": "user",
                    "content": "Say 'API key is working' if you can read this message."
                }
            ],
            temperature=0.7,
            max_tokens=20
        )
        result = response.choices[0].message.content.strip()
        print(f"Mistral API response: {result}")
        return jsonify({
            "status": "success",
            "message": "Mistral API key is working",
            "response": result
        })
    except Exception as e:
        print(f"Error testing Mistral API: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/auth/google', methods=['POST'])
def google_auth():
    try:
        # Verify the Google token
        token = request.json.get('token')
        idinfo = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_CLIENT_ID)

        # Check if user exists, if not create new user
        user_id = f"google_{idinfo['sub']}"
        try:
            user_doc = es.get(index='users', id=user_id)
            user = User.from_dict(user_doc['_source'])
        except:
            user = User(
                user_id=user_id,
                email=idinfo['email'],
                name=idinfo['name'],
                profile_pic=idinfo.get('picture')
            )
            es.index(index='users', id=user_id, body=user.to_dict())

        # Log in the user
        login_user(user)
        return jsonify({"status": "success", "user": user.to_dict()})

    except Exception as e:
        return jsonify({"error": str(e)}), 401

@app.route('/auth/logout')
@login_required
def logout():
    logout_user()
    return jsonify({"status": "success"})

@app.route('/user/profile')
@login_required
def get_profile():
    return jsonify(current_user.to_dict())

@app.route('/user/workout-history')
@login_required
def get_workout_history():
    try:
        # Search for user's workout history
        response = es.search(
            index='workout_history',
            body={
                "query": {
                    "term": {
                        "user_id": current_user.id
                    }
                },
                "sort": [
                    {"created_at": {"order": "desc"}}
                ],
                "size": 10  # Limit to last 10 workouts
            }
        )
        
        history = [hit['_source'] for hit in response.body['hits']['hits']]
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/user/workout-history', methods=['DELETE'])
@login_required
def delete_workout_history():
    try:
        # Delete all workout history for the current user
        response = es.delete_by_query(
            index='workout_history',
            body={
                "query": {
                    "term": {
                        "user_id": current_user.id
                    }
                }
            }
        )
        return jsonify({"message": "Workout history cleared successfully", "deleted": response.body['deleted']})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        make_index()
        make_rag_index()
    app.run(host='0.0.0.0', port=5000)