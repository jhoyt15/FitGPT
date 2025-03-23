from elasticsearch import Elasticsearch
import os
from datetime import datetime

def get_workout_history(uid):
    """
    Get workout history for a specific user
    """
    try:
        # Initialize Elasticsearch client
        es = Elasticsearch("http://elasticsearch:9200")
        
        # Search for user's workout history
        result = es.search(
            index='workout_history',
            query={
                'match': {
                    'user_id': uid
                }
            },
            sort=[
                {'timestamp': {'order': 'desc'}}
            ]
        )
        
        # Extract and format the history
        history = []
        for hit in result['hits']['hits']:
            workout = hit['_source']
            history.append({
                'id': hit['_id'],
                'workout_plan': workout.get('workout_plan', []),
                'timestamp': workout.get('timestamp', ''),
                'query': workout.get('query', '')
            })
        
        return history
    except Exception as e:
        print(f"Error fetching workout history: {str(e)}")
        raise

def save_workout_history(uid, workout_plan, query=None):
    """
    Save a workout plan to the user's history
    """
    try:
        # Initialize Elasticsearch client
        es = Elasticsearch("http://elasticsearch:9200")
        
        # Prepare the document
        doc = {
            'user_id': uid,
            'workout_plan': workout_plan,
            'timestamp': datetime.utcnow().isoformat(),
            'query': query
        }
        
        # Save to Elasticsearch
        result = es.index(
            index='workout_history',
            document=doc
        )
        
        return result['_id']
    except Exception as e:
        print(f"Error saving workout history: {str(e)}")
        raise

def clear_workout_history(uid):
    """
    Delete all workout history for a user
    """
    try:
        # Initialize Elasticsearch client
        es = Elasticsearch("http://elasticsearch:9200")
        
        # Delete by query - remove all documents for this user
        result = es.delete_by_query(
            index='workout_history',
            query={
                'match': {
                    'user_id': uid
                }
            },
            refresh=True  # Refresh the index immediately
        )
        
        print(f"Deleted {result.get('deleted', 0)} workout history records for user {uid}")
        return result.get('deleted', 0)
    except Exception as e:
        print(f"Error clearing workout history: {str(e)}")
        raise 