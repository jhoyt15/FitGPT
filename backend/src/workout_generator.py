from elasticsearch import Elasticsearch
import os
import re
from datetime import datetime
from collections import Counter, defaultdict
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
from fuzzywuzzy import process, fuzz

# Define comprehensive equipment mapping with synonyms and categories
EQUIPMENT_MAPPING = {
    # Standard equipment with synonyms
    'barbell': {'name': 'Barbell', 'synonyms': ['bar', 'olympic bar', 'bars']},
    'dumbbell': {'name': 'Dumbbell', 'synonyms': ['db', 'free weights', 'hand weights']},
    'kettlebell': {'name': 'Kettlebells', 'synonyms': ['kb', 'kettle bell', 'kettle bells']},
    'bands': {'name': 'Bands', 'synonyms': ['resistance bands', 'elastic bands', 'rubber bands', 'tube']},
    'machine': {'name': 'Machine', 'synonyms': ['gym machine', 'weight machine', 'machines']},
    'cable': {'name': 'Cable', 'synonyms': ['pulley', 'cables', 'cable machine']},
    'bodyweight': {'name': 'Body Only', 'synonyms': ['body weight', 'no equipment', 'bodyweight only', 'calisthenics']},
    'exercise ball': {'name': 'Exercise Ball', 'synonyms': ['swiss ball', 'stability ball', 'physio ball', 'yoga ball']},
    'medicine ball': {'name': 'Medicine Ball', 'synonyms': ['med ball', 'weighted ball']},
    'foam roller': {'name': 'Foam Roll', 'synonyms': ['roller', 'foam roll']},
    'ez bar': {'name': 'E-Z Curl Bar', 'synonyms': ['ez curl bar', 'curl bar', 'ez-curl']}
}

# Define equipment categories - for more semantic understanding
EQUIPMENT_CATEGORIES = {
    'weight_training': ['Barbell', 'Dumbbell', 'Kettlebells', 'E-Z Curl Bar', 'Medicine Ball'],
    'bodyweight': ['Body Only'],
    'machine': ['Machine', 'Cable'],
    'stability': ['Exercise Ball', 'Foam Roll'],
    'resistance': ['Bands']
}

# Reverse mapping from standard names to equipment keys
REVERSE_EQUIPMENT_MAPPING = {}
for key, data in EQUIPMENT_MAPPING.items():
    REVERSE_EQUIPMENT_MAPPING[data['name']] = key

def extract_number(text, default=3):
    """Extract a number from text or return default"""
    numbers = re.findall(r'\b(\d+)\b', text)
    if numbers:
        return int(numbers[0])
    return default

def extract_body_parts(text):
    """Extract body parts from text"""
    body_parts = set()
    part_keywords = {
        'leg': 'Legs', 'quad': 'Quadriceps', 'hamstring': 'Hamstrings', 'calf': 'Calves',
        'arm': 'Arms', 'bicep': 'Biceps', 'tricep': 'Triceps', 'shoulder': 'Shoulders',
        'chest': 'Chest', 'pec': 'Chest', 
        'back': 'Back', 'lat': 'Back',
        'core': 'Core', 'ab': 'Abdominals', 'abs': 'Abdominals',
        'glute': 'Glutes', 'butt': 'Glutes',
        'full body': 'Full Body', 'total body': 'Full Body'
    }
    
    for keyword, part in part_keywords.items():
        if keyword in text.lower():
            body_parts.add(part)
    
    return list(body_parts)

def preprocess_text(text):
    """Preprocess text for better matching"""
    # Convert to lowercase
    text = text.lower()
    
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove punctuation
    text = re.sub(r'[^\w\s]', ' ', text)
    
    return text.strip()

def fuzzy_match_equipment(text, threshold=80):
    """Use fuzzy matching to find equipment in text"""
    matched_equipment = []
    
    # Text normalization
    text = preprocess_text(text)
    
    # First check exact matches including synonyms
    for equip_key, equip_data in EQUIPMENT_MAPPING.items():
        # Check the main term
        if equip_key in text:
            matched_equipment.append(equip_data['name'])
            continue
            
        # Check synonyms
        for synonym in equip_data['synonyms']:
            if synonym in text:
                matched_equipment.append(equip_data['name'])
                break
    
    # If no exact matches, try fuzzy matching
    if not matched_equipment:
        # Create a list of all equipment terms and their synonyms
        all_terms = []
        term_to_equipment = {}
        
        for equip_key, equip_data in EQUIPMENT_MAPPING.items():
            all_terms.append(equip_key)
            term_to_equipment[equip_key] = equip_data['name']
            
            for synonym in equip_data['synonyms']:
                all_terms.append(synonym)
                term_to_equipment[synonym] = equip_data['name']
        
        # Extract all words and phrases from the text (1-3 word combinations)
        words = text.split()
        phrases = [' '.join(words[i:i+n]) for n in range(1, 4) for i in range(len(words)-n+1)]
        
        # Try to match each phrase to equipment terms
        for phrase in phrases:
            matches = process.extractBests(phrase, all_terms, scorer=fuzz.token_sort_ratio, 
                                          score_cutoff=threshold, limit=3)
            for match, score in matches:
                matched_equipment.append(term_to_equipment[match])
    
    # Return unique matches
    return list(set(matched_equipment))

def extract_equipment(text):
    """
    Extract equipment preferences from text with advanced matching
    Returns (equipment_list, is_exclusive, no_equipment)
    """
    # Preprocess the text
    text = preprocess_text(text)
    
    # Check for "no equipment" phrases
    no_equipment_phrases = [
        'no equipment', 'body weight', 'bodyweight', 'body only', 
        'without equipment', 'no weights', 'without weights', 
        'calisthenics', 'just my body'
    ]
    
    for phrase in no_equipment_phrases:
        if phrase in text:
            return ['Body Only'], True, True
    
    # Check for "only" phrases that indicate exclusive equipment use
    only_patterns = [
        r'([\w\s]+)\s+only',        # "dumbbells only"
        r'only\s+([\w\s]+)',        # "only dumbbells"
        r'just\s+([\w\s]+)',        # "just dumbbells"
        r'using\s+only\s+([\w\s]+)', # "using only dumbbells"
        r'with\s+only\s+([\w\s]+)',  # "with only dumbbells"
        r'have\s+only\s+([\w\s]+)',  # "have only dumbbells"
        r'access\s+to\s+only\s+([\w\s]+)', # "access to only dumbbells"
    ]
    
    for pattern in only_patterns:
        match = re.search(pattern, text)
        if match:
            equipment_text = match.group(1).strip()
            matched_equip = fuzzy_match_equipment(equipment_text)
            if matched_equip:
                return matched_equip, True, False
    
    # Use fuzzy matching for all equipment
    matched_equipment = fuzzy_match_equipment(text)
    return matched_equipment, len(matched_equipment) > 0, False

def is_equipment_compatible(exercise_equipment, user_equipment, no_equipment_only=False):
    """
    Check if an exercise's equipment is compatible with user's equipment preferences
    With stricter validation and context awareness
    """
    # Handle the case where user specifically wants no equipment
    if no_equipment_only:
        return exercise_equipment == 'Body Only' or exercise_equipment == 'None'
        
    # If no user equipment specified, all equipment is compatible
    if not user_equipment:
        return True
        
    # Exact match
    if exercise_equipment in user_equipment:
        return True
        
    # Handle "None" as equivalent to "Body Only"
    if exercise_equipment == 'None' and 'Body Only' in user_equipment:
        return True
        
    if exercise_equipment == 'Body Only' and 'None' in user_equipment:
        return True
    
    # Handle equipment categories (e.g., if a user has barbell, they probably have weights)
    equip_category = None
    for category, equipments in EQUIPMENT_CATEGORIES.items():
        if exercise_equipment in equipments:
            equip_category = category
            break
    
    if equip_category:
        # Check if the user has any equipment in this category
        for user_equip in user_equipment:
            if any(user_equip == e for e in EQUIPMENT_CATEGORIES.get(equip_category, [])):
                return True
    
    return False

def generate_ai_tip_rule_based(exercise):
    """Generate more specific and helpful AI coach tips based on exercise details - rule-based fallback"""
    body_part = exercise.get('BodyPart', '')
    exercise_type = exercise.get('Type', '')
    equipment = exercise.get('Equipment', '')
    level = exercise.get('Level', 'beginner')
    title = exercise.get('Title', '')
    
    tips = []
    
    # Form tips based on body part
    if 'Chest' in body_part:
        tips.append("Keep your elbows at a 45-degree angle to protect your shoulders.")
        tips.append("Focus on squeezing your chest muscles at the top of the movement.")
    elif 'Back' in body_part:
        tips.append("Maintain a straight back and engage your core throughout the movement.")
        tips.append("Pull with your back muscles, not your arms, by focusing on squeezing your shoulder blades together.")
    elif 'Shoulder' in body_part:
        tips.append("Avoid shrugging your shoulders to prevent neck strain.")
        tips.append("Keep your core engaged to stabilize your upper body during the exercise.")
    elif 'Leg' in body_part or 'Quad' in body_part or 'Hamstring' in body_part:
        tips.append("Push through your heels to engage your posterior chain properly.")
        tips.append("Keep your knees aligned with your toes to protect your joints.")
    elif 'Arm' in body_part or 'Bicep' in body_part or 'Tricep' in body_part:
        tips.append("Control the movement in both directions for maximum muscle activation.")
        tips.append("Keep your elbows close to your body for better isolation.")
    elif 'Core' in body_part or 'Ab' in body_part:
        tips.append("Focus on slow, controlled movements rather than speed.")
        tips.append("Remember to breathe properly - exhale during exertion.")
    
    # Equipment-specific tips
    if 'Barbell' in equipment:
        tips.append(f"Start with a lighter weight to perfect your form before progressing. For {title}, grip width significantly impacts which muscles are engaged most.")
    elif 'Dumbbell' in equipment:
        tips.append(f"Use a weight that allows you to maintain perfect form. For {title}, focus on equal effort from both sides.")
    elif 'Kettlebell' in equipment:
        tips.append("Keep your movements fluid and use the momentum of the kettlebell strategically.")
    elif 'Body' in equipment or 'None' in equipment:
        tips.append("Focus on maximizing the mind-muscle connection since you're working with your body weight.")
    
    # Level-specific tips
    if level.lower() == 'beginner':
        tips.append("Take your time to learn proper form before increasing intensity or weight.")
    elif level.lower() == 'intermediate':
        tips.append("Consider adding tempo variations (slow negatives, pauses) to increase difficulty.")
    elif level.lower() == 'advanced':
        tips.append("Maximize muscle time under tension by slowing down the eccentric (lowering) phase.")
    
    # Select 2-3 most relevant tips
    selected_tips = tips[:2] if tips else ["Focus on proper form and breathing throughout this exercise."]
    
    return " ".join(selected_tips)

def generate_ai_tip(exercise):
    """Generate AI coach tips using Mistral AI if available, fallback to rule-based"""
    try:
        # Try to use Mistral API if credentials are available
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            return generate_ai_tip_rule_based(exercise)
        
        client = MistralClient(api_key=api_key)
        
        # Format exercise details for the prompt
        exercise_details = f"""
        Exercise: {exercise.get('Title', '')}
        Description: {exercise.get('Description', '')}
        Type: {exercise.get('Type', '')}
        Equipment: {exercise.get('Equipment', '')}
        Body Part: {exercise.get('BodyPart', '')}
        Level: {exercise.get('Level', '')}
        """
        
        messages = [
            ChatMessage(role="system", content="You are an expert fitness coach providing concise, specific advice for exercises. Focus on proper form, technique, and common mistakes to avoid. Keep your response under 40 words."),
            ChatMessage(role="user", content=f"Give me 1-2 specific coaching tips for this exercise:\n{exercise_details}")
        ]
        
        response = client.chat(
            model="mistral-tiny",  # Use an appropriate model
            messages=messages
        )
        
        ai_tip = response.choices[0].message.content
        
        # Ensure the tip isn't too long
        if len(ai_tip.split()) > 45:  # If more than 45 words
            sentences = ai_tip.split('.')
            ai_tip = '. '.join(sentences[:2]) + '.'
        
        return ai_tip.strip()
    
    except Exception as e:
        print(f"Error generating AI tip with Mistral: {str(e)}")
        # Fall back to rule-based tips
        return generate_ai_tip_rule_based(exercise)

def alternate_exercises(exercise, preferred_equipment):
    """Generate alternative versions of exercises if equipment doesn't match"""
    alt_exercises = []
    if not preferred_equipment:
        return alt_exercises
        
    equipment = exercise.get('Equipment', '')
    title = exercise.get('Title', '')
    description = exercise.get('Description', '')
    body_part = exercise.get('BodyPart', '')
    
    # Don't suggest alternatives for compatible equipment
    if equipment in preferred_equipment:
        return alt_exercises
        
    # Create alternatives based on equipment preferences
    if 'Body Only' in preferred_equipment:
        if 'Dumbbell' in equipment:
            alt_exercises.append({
                'Title': f"{title} (Bodyweight Alternative)",
                'Description': f"No-equipment alternative for {title}: {description}",
                'Type': exercise.get('Type', ''),
                'Equipment': 'Body Only',
                'BodyPart': body_part,
                'Level': exercise.get('Level', ''),
                'is_alternative': True
            })
    
    if 'Dumbbell' in preferred_equipment:
        if 'Barbell' in equipment:
            alt_exercises.append({
                'Title': f"{title} (Dumbbell Alternative)",
                'Description': f"Dumbbell alternative for {title}: {description}",
                'Type': exercise.get('Type', ''),
                'Equipment': 'Dumbbell',
                'BodyPart': body_part,
                'Level': exercise.get('Level', ''),
                'is_alternative': True
            })
            
    return alt_exercises

def generate_ai_workout_intent(query_text):
    """Use AI to better understand the user's workout goals and constraints"""
    try:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            # Fall back to rule-based extraction if no API key
            return None
            
        client = MistralClient(api_key=api_key)
        
        prompt = f"""
        Analyze this workout request and extract the following information in JSON format:
        - goals: Primary fitness goals (e.g., strength, muscle gain, weight loss, endurance)
        - equipment_constraints: What equipment is available or unavailable
        - fitness_level: beginner, intermediate, or advanced
        - focus_areas: Specific body parts they want to target
        - time_constraints: How much time they have for each workout
        - schedule_constraints: How many days per week they can work out

        Request: {query_text}
        
        Return ONLY the JSON with these fields and no explanation or other text. If information for a field is not present, leave it as null.
        """
        
        messages = [
            ChatMessage(role="system", content="You are a fitness expert that analyzes workout requests to extract structured data."),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = client.chat(
            model="mistral-tiny",
            messages=messages
        )
        
        import json
        try:
            result = json.loads(response.choices[0].message.content)
            return result
        except:
            print("Failed to parse AI workout intent response")
            return None
            
    except Exception as e:
        print(f"Error generating AI workout intent: {str(e)}")
        return None

def ai_enhance_workout_plan(draft_plan, user_query):
    """Use AI to enhance a draft workout plan with more personalized recommendations"""
    try:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            # Return original plan if no API key
            return draft_plan
            
        client = MistralClient(api_key=api_key)
        
        # Prepare a condensed version of the draft plan
        days_overview = []
        for day in draft_plan.get('workout_days', []):
            exercise_names = [ex.get('Title') for ex in day.get('exercises', [])]
            days_overview.append({
                'day_number': day.get('day_number'),
                'focus': day.get('overview'),
                'exercises': exercise_names
            })
        
        prompt = f"""
        Review this drafted workout plan and suggest improvements to make it more effective and personalized for the user's request.
        
        USER REQUEST: {user_query}
        
        DRAFTED WORKOUT PLAN:
        - Level: {draft_plan.get('level')}
        - Days per week: {draft_plan.get('days_per_week')}
        - Minutes per session: {draft_plan.get('minutes_per_session')}
        - Overview: {draft_plan.get('plan_overview')}
        - Workout days: {json.dumps(days_overview)}
        
        Provide the following improvements:
        1. Exercise ordering - how the exercises should be reordered for optimal results
        2. Workout structure - changes to the workout structure (e.g., supersets, circuit training)
        3. Progression plan - how the user should progress over time
        
        Return ONLY a JSON with these fields:
        {
            "exercise_ordering": [list of suggestions],
            "workout_structure": [list of suggestions],
            "progression_plan": [list of suggestions],
            "training_tips": [list of overall tips]
        }
        """
        
        messages = [
            ChatMessage(role="system", content="You are an expert fitness coach that helps improve workout plans."),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = client.chat(
            model="mistral-tiny",
            messages=messages
        )
        
        try:
            enhancements = json.loads(response.choices[0].message.content)
            
            # Add the AI enhancements to the workout plan
            draft_plan['ai_enhancements'] = enhancements
            
            # Apply some of the structural enhancements directly
            if enhancements.get('workout_structure'):
                for day in draft_plan.get('workout_days', []):
                    structure_note = f"Coach's Note: {enhancements['workout_structure'][0]}" if enhancements['workout_structure'] else ""
                    day['structure_note'] = structure_note
            
            # Add progression guidance
            if enhancements.get('progression_plan'):
                draft_plan['progression_guidance'] = enhancements['progression_plan']
                
            # Add overall training tips
            if enhancements.get('training_tips'):
                draft_plan['training_tips'] = enhancements['training_tips']
                
            return draft_plan
            
        except Exception as inner_e:
            print(f"Failed to parse AI enhancements: {str(inner_e)}")
            return draft_plan
            
    except Exception as e:
        print(f"Error enhancing workout plan with AI: {str(e)}")
        return draft_plan

def extract_customization_intent(query_text):
    """Use AI to extract specific customization instructions from the query"""
    try:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            return None
            
        client = MistralClient(api_key=api_key)
        
        prompt = f"""
        Extract any special customization instructions or specific workout modifications from this user query.
        
        For example, in a query like "I want a workout for 3 days per week with dumbbells only. Tailor it for a swimmer with focus on shoulder mobility," 
        the customization part would be "Tailor it for a swimmer with focus on shoulder mobility."
        
        USER QUERY: {query_text}
        
        Return ONLY the customization part or "None" if there aren't any special customization instructions.
        """
        
        messages = [
            ChatMessage(role="system", content="You are a fitness expert assistant that helps analyze workout requests."),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = client.chat(
            model="mistral-tiny",
            messages=messages
        )
        
        customization = response.choices[0].message.content.strip()
        if customization.lower() == "none":
            return None
        return customization
        
    except Exception as e:
        print(f"Error extracting customization intent: {str(e)}")
        return None

def apply_workout_customization(workout_plan, customization_text, user_query):
    """Apply specific customization to a workout plan using AI"""
    if not customization_text:
        return workout_plan
        
    try:
        api_key = os.environ.get("MISTRAL_API_KEY")
        if not api_key:
            return workout_plan
            
        client = MistralClient(api_key=api_key)
        
        # Convert the workout plan to a simple format to reduce token usage
        simplified_plan = {
            "level": workout_plan.get("level", ""),
            "days_per_week": workout_plan.get("days_per_week", ""),
            "plan_overview": workout_plan.get("plan_overview", ""),
            "days": []
        }
        
        for day in workout_plan.get("workout_days", []):
            day_summary = {
                "day_number": day.get("day_number", ""),
                "overview": day.get("overview", ""),
                "exercises": [ex.get("Title", "") for ex in day.get("exercises", [])]
            }
            simplified_plan["days"].append(day_summary)
        
        prompt = f"""
        Modify this workout plan according to the following customization request.
        
        CUSTOMIZATION REQUEST: {customization_text}
        
        ORIGINAL QUERY: {user_query}
        
        CURRENT WORKOUT PLAN:
        {json.dumps(simplified_plan, indent=2)}
        
        Provide specific recommendations to modify the workout plan to address the customization request.
        Focus on:
        1. How specific exercises should be changed or substituted
        2. How the overall structure might be adjusted
        3. Any special considerations for the custom request
        
        Return ONLY a JSON with these fields:
        {{
            "exercise_modifications": [list of specific exercise substitutions],
            "structure_changes": [list of workout structure changes],
            "special_considerations": [list of important notes related to the customization]
        }}
        """
        
        messages = [
            ChatMessage(role="system", content="You are an expert fitness coach specialized in tailoring workout plans to specific needs."),
            ChatMessage(role="user", content=prompt)
        ]
        
        response = client.chat(
            model="mistral-tiny",
            messages=messages
        )
        
        try:
            customizations = json.loads(response.choices[0].message.content)
            
            # Add the customization details to the plan
            workout_plan["customization"] = {
                "request": customization_text,
                "modifications": customizations
            }
            
            # If we have progression guidance from earlier enhancements, combine them
            if workout_plan.get("progression_guidance") and customizations.get("structure_changes"):
                workout_plan["progression_guidance"].extend(customizations.get("structure_changes", []))
            
            # Add special considerations as training tips
            if customizations.get("special_considerations"):
                if not workout_plan.get("training_tips"):
                    workout_plan["training_tips"] = []
                workout_plan["training_tips"].extend(customizations.get("special_considerations", []))
            
            # Update the plan overview to mention customization
            if workout_plan.get("plan_overview"):
                workout_plan["plan_overview"] += f" This plan has been customized: {customization_text}"
                
            return workout_plan
            
        except Exception as inner_e:
            print(f"Failed to parse customization response: {str(inner_e)}")
            return workout_plan
            
    except Exception as e:
        print(f"Error applying customization: {str(e)}")
        return workout_plan

def generate_workout_plan(query_text):
    """
    Generate a workout plan based on the user's query using Elasticsearch and AI enhancements
    """
    try:
        # Extract any specific customization instructions
        customization_text = extract_customization_intent(query_text)
        if customization_text:
            print(f"Detected customization request: {customization_text}")
            
        # Try to use AI to better understand the user's intent
        ai_intent = generate_ai_workout_intent(query_text)
        
        # Initialize Elasticsearch client
        es = Elasticsearch("http://elasticsearch:9200")
        
        # Extract key information from the query (with AI assistance if available)
        fitness_level = "beginner"  # Default
        if ai_intent and ai_intent.get('fitness_level'):
            fitness_level = ai_intent.get('fitness_level')
        elif "intermediate" in query_text.lower():
            fitness_level = "intermediate"
        elif "advanced" in query_text.lower():
            fitness_level = "advanced"
        
        # Extract days per week from query
        days_per_week = 3  # Default
        if ai_intent and ai_intent.get('schedule_constraints'):
            # Try to extract from AI intent
            try:
                days_per_week = int(ai_intent.get('schedule_constraints'))
            except:
                pass
        else:
            # Fallback to regex extraction
            days_per_week_pattern = r'(\d+)\s*days\s*per\s*week'
            days_per_week_match = re.search(days_per_week_pattern, query_text)
            if days_per_week_match:
                days_per_week = int(days_per_week_match.group(1))
        
        days_per_week = min(days_per_week, 6)  # Cap at 6 days
        
        # Extract time available
        time_available = 30  # Default
        if ai_intent and ai_intent.get('time_constraints'):
            # Try to extract from AI intent
            try:
                time_available = int(ai_intent.get('time_constraints'))
            except:
                pass
        else:
            # Fallback to regex extraction
            time_pattern = r'(\d+)\s*minutes'
            time_match = re.search(time_pattern, query_text)
            if time_match:
                time_available = int(time_match.group(1))
        
        # Extract preferred body parts (with AI assistance if available)
        preferred_body_parts = []
        if ai_intent and ai_intent.get('focus_areas'):
            preferred_body_parts = ai_intent.get('focus_areas')
        else:
            preferred_body_parts = extract_body_parts(query_text)
        
        # Extract equipment preferences with advanced matching
        preferred_equipment = []
        is_exclusive = False
        no_equipment_only = False
        
        if ai_intent and ai_intent.get('equipment_constraints'):
            # Parse AI-detected equipment constraints
            equipment_constraints = ai_intent.get('equipment_constraints')
            
            # Handle different return types (string or list)
            if isinstance(equipment_constraints, list):
                # Join the list into a single string for processing
                equipment_constraints_text = ' '.join(equipment_constraints).lower()
            else:
                # It's likely a string, but make sure
                equipment_constraints_text = str(equipment_constraints).lower()
            
            # Check for no equipment scenario
            if any(phrase in equipment_constraints_text for phrase in ["no equipment", "bodyweight only", "calisthenics"]):
                preferred_equipment = ['Body Only']
                is_exclusive = True
                no_equipment_only = True
            else:
                # Extract equipment from AI analysis
                detected_equipment = []
                for equip_key, equip_data in EQUIPMENT_MAPPING.items():
                    if equip_key in equipment_constraints_text or any(syn in equipment_constraints_text for syn in equip_data['synonyms']):
                        detected_equipment.append(equip_data['name'])
                
                if detected_equipment:
                    preferred_equipment = detected_equipment
                    is_exclusive = "only" in equipment_constraints_text or "just" in equipment_constraints_text
                else:
                    # Fallback to normal extraction
                    preferred_equipment, is_exclusive, no_equipment_only = extract_equipment(query_text)
        else:
            # Fallback to normal extraction
            preferred_equipment, is_exclusive, no_equipment_only = extract_equipment(query_text)
        
        # Log equipment detection results for debugging
        print(f"Equipment detection: {preferred_equipment}, exclusive: {is_exclusive}, no_equipment: {no_equipment_only}")
        if ai_intent:
            print(f"AI intent detected: {ai_intent}")
        
        # Prepare search query
        search_query = query_text
        if preferred_body_parts:
            search_query += " " + " ".join(preferred_body_parts)
        
        # CRUCIAL IMPROVEMENT: Use a more sophisticated Elasticsearch query
        # Add specific queries for equipment to ensure we get relevant exercises
        should_clauses = []
        
        # Add title and description match
        should_clauses.extend([
            {"match": {"Title": {"query": search_query, "boost": 2}}},
            {"match": {"Description": {"query": search_query, "boost": 1}}}
        ])
        
        # Add equipment specific boosts
        for equipment in preferred_equipment:
            should_clauses.append({"match": {"Equipment": {"query": equipment, "boost": 3}}})
            
        # For body-only/no equipment, specifically include exercises with no equipment
        if no_equipment_only or 'Body Only' in preferred_equipment:
            should_clauses.extend([
                {"match": {"Equipment": {"query": "Body Only", "boost": 3}}},
                {"match": {"Equipment": {"query": "None", "boost": 3}}}
            ])
        
        # Construct final query
        query = {
            "size": 500,  # Get much more results to ensure we have enough
            "query": {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }
        }
        
        # Execute the enhanced query
        result = es.search(index="workouts", body=query)
        
        # Extract and format the workout plan
        hits = result['hits']['hits']
        
        # IMPROVED: More intelligent filtering
        filtered_hits = []
        for hit in hits:
            workout = hit['_source']
            exercise_equipment = workout.get('Equipment', '')
            
            # We'll score each exercise to decide inclusion
            # Base inclusion on compatibility BUT with intelligent scoring
            inclusion_score = 0
            
            # Direct equipment match is best
            if exercise_equipment in preferred_equipment:
                inclusion_score += 10
                
            # For "no equipment" queries, bodyweight is perfect
            if no_equipment_only and (exercise_equipment == 'Body Only' or exercise_equipment == 'None'):
                inclusion_score += 15
                
            # For bodyweight filter, slightly broader match criteria
            if 'Body Only' in preferred_equipment and exercise_equipment in ['None', 'Body Only', 'Bands', 'Medicine Ball']:
                inclusion_score += 8
            
            # Check body part preferences
            if preferred_body_parts:
                body_part = workout.get('BodyPart', '')
                if any(part.lower() in body_part.lower() for part in preferred_body_parts):
                    inclusion_score += 5
                    
            # If exclusive mode is on, require minimum score with equipment contribution
            if is_exclusive or no_equipment_only:
                if inclusion_score < 5 or (inclusion_score <= 8 and not any(
                    exercise_equipment in equip or equip in exercise_equipment for equip in preferred_equipment
                )):
                    continue
            
            # Always add items with decent score
            if inclusion_score > 0:
                # Add score to workout for sorting
                workout['inclusion_score'] = inclusion_score
                filtered_hits.append((workout, inclusion_score))
        
        # Sort by inclusion score
        filtered_hits.sort(key=lambda x: x[1], reverse=True)
        filtered_hits = [hit[0] for hit in filtered_hits]
        
        # IMPORTANT: Before falling back completely, make sure we have bodyweight alternatives
        if len(filtered_hits) < days_per_week * 2 and ('Body Only' in preferred_equipment or no_equipment_only):
            print(f"Not enough exercises found ({len(filtered_hits)}), using adaptive search...")
            
            # Use a dedicated bodyweight exercise search
            bodyweight_query = {
                "size": 200,
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"Equipment": "Body Only"}}
                        ]
                    }
                }
            }
            
            # Add body parts if specified
            if preferred_body_parts:
                should_body_parts = []
                for part in preferred_body_parts:
                    should_body_parts.append({"match": {"BodyPart": part}})
                
                if should_body_parts:
                    bodyweight_query["query"]["bool"]["should"] = should_body_parts
            
            bodyweight_result = es.search(index="workouts", body=bodyweight_query)
            bodyweight_hits = bodyweight_result['hits']['hits']
            
            # Add bodyweight exercises to results
            for hit in bodyweight_hits:
                if hit['_source'] not in filtered_hits:
                    hit['_source']['inclusion_score'] = 5  # Lower priority than direct matches
                    filtered_hits.append(hit['_source'])
                    
            print(f"Added bodyweight exercises, new count: {len(filtered_hits)}")
        
        # MUST HAVE: Ensure we have enough exercises by intelligently relaxing constraints
        if len(filtered_hits) < days_per_week * 2:
            # Final fallback - search for common bodyweight exercises by name
            basic_exercises = ["push up", "squat", "lunge", "plank", "crunch", "mountain climber", 
                               "jumping jack", "burpee", "sit up", "pull up", "dip"]
            
            additional_hits = []
            
            for exercise_name in basic_exercises:
                basic_query = {
                    "size": 5,
                    "query": {
                        "bool": {
                            "should": [
                                {"match": {"Title": {"query": exercise_name, "boost": 3}}},
                                {"match": {"Description": {"query": exercise_name, "boost": 1}}}
                            ],
                            "minimum_should_match": 1
                        }
                    }
                }
                
                result = es.search(index="workouts", body=basic_query)
                for hit in result['hits']['hits']:
                    if hit['_source'] not in filtered_hits and hit['_source'] not in additional_hits:
                        hit['_source']['inclusion_score'] = 3  # Even lower priority
                        additional_hits.append(hit['_source'])
            
            filtered_hits.extend(additional_hits)
            print(f"Added common exercises by name search, new count: {len(filtered_hits)}")
        
        # Organize workouts by body part with strict equipment validation but ensuring good coverage
        workouts_by_body_part = defaultdict(list)
        
        # Function to determine equipment compatibility with more flexibility
        def is_compatible_for_organization(equipment, user_equipment, is_exclusive, no_equipment_only):
            if not is_exclusive and not no_equipment_only:
                return True
                
            if no_equipment_only:
                return equipment == 'Body Only' or equipment == 'None'
                
            if is_exclusive:
                # Direct match
                if equipment in user_equipment:
                    return True
                    
                # None/Body Only equivalence
                if equipment == 'None' and 'Body Only' in user_equipment:
                    return True
                if equipment == 'Body Only' and 'None' in user_equipment:
                    return True
                    
                # Category match (e.g. Bands and Resistance Tube)
                for category, equipments in EQUIPMENT_CATEGORIES.items():
                    if equipment in equipments:
                        for user_eq in user_equipment:
                            if user_eq in equipments:
                                return True
                                
            return False
        
        # First pass: strict filtering
        for workout in filtered_hits:
            equipment = workout.get('Equipment', '')
            
            if is_compatible_for_organization(equipment, preferred_equipment, is_exclusive, no_equipment_only):
                body_part = workout.get('BodyPart', 'General')
                workouts_by_body_part[body_part].append(workout)
        
        # Check if we have enough exercises after organization
        total_organized = sum(len(workouts) for workouts in workouts_by_body_part.values())
        
        # If we don't have enough for a good split, add additional exercises
        if total_organized < days_per_week * 3:
            print(f"Not enough exercises after organization, adding more flexible matches...")
            for workout in filtered_hits:
                if workout not in [w for workouts in workouts_by_body_part.values() for w in workouts]:
                    body_part = workout.get('BodyPart', 'General')
                    workouts_by_body_part[body_part].append(workout)
        
        # Determine workout split based on days per week
        if days_per_week <= 2:
            # Full body workouts
            split_type = "full body"
            day_splits = ["Full Body"] * days_per_week
        elif days_per_week == 3:
            # Push/Pull/Legs split
            split_type = "push/pull/legs"
            day_splits = ["Push", "Pull", "Legs"]
        elif days_per_week == 4:
            # Upper/Lower split
            split_type = "upper/lower"
            day_splits = ["Upper", "Lower", "Upper", "Lower"]
        else:
            # Body part split
            split_type = "body part"
            day_splits = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"][:days_per_week]
        
        # Create structured workout plan
        workout_days = []
        
        # Final safety check - ensure we have SOMETHING for each day
        all_workouts = [w for workouts in workouts_by_body_part.values() for w in workouts]
        
        # Debugging: Print number of available exercises
        print(f"Total organized workouts: {len(all_workouts)}")
        print(f"Key body parts: {list(workouts_by_body_part.keys())[:5]}")
        
        for day_idx, focus in enumerate(day_splits):
            day_number = day_idx + 1
            exercises = []
            
            # Intelligent exercise selection adjusted for each focus
            # [Similar to existing selection logic but with better fallbacks]
            # For brevity, I'll add a streamlined selection process that ensures we get exercises
            
            selected_exercises = []
            
            # First try exact focus matches
            if focus == "Full Body":
                # Get a mix of exercises for different body parts
                body_parts = ["Chest", "Back", "Legs", "Shoulders", "Arms", "Core"]
                for part in body_parts:
                    part_exercises = []
                    for body_part, workouts in workouts_by_body_part.items():
                        if part.lower() in body_part.lower():
                            part_exercises.extend(workouts)
                    
                    # Take top scored exercises by part
                    part_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                    selected_exercises.extend(part_exercises[:max(1, min(2, time_available // 15))])
            
            elif focus == "Push":
                push_exercises = []
                for body_part, workouts in workouts_by_body_part.items():
                    if any(part in body_part.lower() for part in ["chest", "shoulder", "tricep"]):
                        push_exercises.extend(workouts)
                
                push_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(push_exercises[:time_available // 5])
            
            elif focus == "Pull":
                pull_exercises = []
                for body_part, workouts in workouts_by_body_part.items():
                    if any(part in body_part.lower() for part in ["back", "bicep"]):
                        pull_exercises.extend(workouts)
                
                pull_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(pull_exercises[:time_available // 5])
            
            elif focus == "Legs":
                leg_exercises = []
                for body_part, workouts in workouts_by_body_part.items():
                    if any(part in body_part.lower() for part in ["leg", "quad", "hamstring", "glute", "calf"]):
                        leg_exercises.extend(workouts)
                
                leg_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(leg_exercises[:time_available // 5])
            
            elif focus == "Upper":
                upper_exercises = []
                for body_part, workouts in workouts_by_body_part.items():
                    if any(part in body_part.lower() for part in ["chest", "back", "shoulder", "arm", "bicep", "tricep"]):
                        upper_exercises.extend(workouts)
                
                upper_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(upper_exercises[:time_available // 5])
            
            elif focus == "Lower":
                lower_exercises = []
                for body_part, workouts in workouts_by_body_part.items():
                    if any(part in body_part.lower() for part in ["leg", "quad", "hamstring", "glute", "calf"]):
                        lower_exercises.extend(workouts)
                
                lower_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(lower_exercises[:time_available // 5])
            
            else:
                # Specific body part
                specific_exercises = []
                for body_part, workouts in workouts_by_body_part.items():
                    if focus.lower() in body_part.lower():
                        specific_exercises.extend(workouts)
                
                specific_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(specific_exercises[:time_available // 5])
            
            # CRITICAL: If we still don't have enough exercises for this day, take some from the general pool
            if len(selected_exercises) < 3:
                print(f"Not enough exercises for day {day_number}, using general pool")
                remaining_exercises = [w for w in all_workouts if w not in selected_exercises]
                remaining_exercises.sort(key=lambda x: x.get('inclusion_score', 0), reverse=True)
                selected_exercises.extend(remaining_exercises[:3])
            
            # Format the final exercises for this day
            for workout in selected_exercises[:time_available // 5]:  # Limit to reasonable number
                exercises.append({
                    'Title': workout.get('Title', ''),
                    'Description': workout.get('Description', ''),
                    'Type': workout.get('Type', ''),
                    'Equipment': workout.get('Equipment', ''),
                    'BodyPart': workout.get('BodyPart', ''),
                    'Level': workout.get('Level', ''),
                    'AI_Recommendations': generate_ai_tip(workout)
                })
            
            # Only add day if we have exercises
            if exercises:
                body_parts = set([ex.get('BodyPart', '') for ex in exercises])
                day_overview = f"Day {day_number}: {focus} Day - Focus on {', '.join(list(body_parts)[:3])}"
                
                workout_days.append({
                    'day_number': day_number,
                    'overview': day_overview,
                    'exercises': exercises
                })
        
        # ABSOLUTE LAST RESORT - Create basic workout if everything else failed
        if not workout_days:
            print("WARNING: All intelligent fallbacks failed. Using hardcoded basic workout.")
            
            bodyweight_exercises = [
                {
                    'Title': 'Push-ups',
                    'Description': 'Basic bodyweight exercise for chest, shoulders, and triceps.',
                    'Type': 'Strength',
                    'Equipment': 'Body Only',
                    'BodyPart': 'Chest',
                    'Level': fitness_level,
                    'AI_Recommendations': 'Keep your core tight and body in a straight line. Lower until elbows reach 90 degrees.'
                },
                {
                    'Title': 'Squats',
                    'Description': 'Fundamental lower body exercise targeting quadriceps, hamstrings, and glutes.',
                    'Type': 'Strength',
                    'Equipment': 'Body Only',
                    'BodyPart': 'Quadriceps',
                    'Level': fitness_level,
                    'AI_Recommendations': 'Keep weight in your heels and knees tracking over toes. Descend until thighs are parallel to ground.'
                },
                {
                    'Title': 'Planks',
                    'Description': 'Core stabilization exercise engaging the entire midsection.',
                    'Type': 'Strength',
                    'Equipment': 'Body Only',
                    'BodyPart': 'Abdominals',
                    'Level': fitness_level,
                    'AI_Recommendations': 'Maintain a straight line from head to heels. Engage your core and breathe normally.'
                }
            ]
            
            workout_days.append({
                'day_number': 1,
                'overview': 'Full Body Workout (FALLBACK - No matches found)',
                'exercises': bodyweight_exercises
            })
            
            # Ensure this is clearly marked as a fallback
            days_per_week = 1
            equipment_description = " (basic fallback workout)"
        else:
            # Create equipment description for overview
            if no_equipment_only:
                equipment_description = " using only bodyweight exercises"
            elif is_exclusive and preferred_equipment:
                equipment_description = f" using only {', '.join(preferred_equipment)}"
            elif preferred_equipment:
                equipment_description = f" using {', '.join(preferred_equipment)}"
            else:
                equipment_description = ""
        
        # Create the draft response
        draft_plan = {
            'level': fitness_level,
            'days_per_week': str(len(workout_days)),
            'minutes_per_session': str(time_available),
            'plan_overview': f"This {fitness_level} level workout plan follows a {split_type} split, designed for {len(workout_days)} days per week, with approximately {time_available} minutes per session{equipment_description}.{' Focus on ' + ', '.join(preferred_body_parts) + '.' if preferred_body_parts else ''}",
            'workout_days': workout_days
        }
        
        # Try to enhance the workout plan with AI recommendations
        enhanced_plan = ai_enhance_workout_plan(draft_plan, query_text)
        
        # Apply customization if specified
        if customization_text:
            final_plan = apply_workout_customization(enhanced_plan, customization_text, query_text)
            return final_plan
        else:
            return enhanced_plan
        
    except Exception as e:
        print(f"Error generating workout plan: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return a basic fallback plan
        return {
            'level': 'beginner',
            'days_per_week': '3',
            'minutes_per_session': '30',
            'plan_overview': "Error generating custom plan. Here's a basic fallback plan.",
            'workout_days': [{
                'day_number': 1,
                'overview': "Full Body Workout",
                'exercises': [{
                    'Title': "Basic Workout",
                    'Description': "Simple exercises to get you moving",
                    'Type': "Strength",
                    'Equipment': "Body Only",
                    'BodyPart': "Full Body",
                    'Level': "Beginner",
                    'AI_Recommendations': "Start slow and focus on proper form."
                }]
            }]
        } 