# myblueprints/friends_validate_clean_bp.py
from flask import Blueprint, request, jsonify
import json
import os
import re

friends_validate_bp = Blueprint('friends_validate_bp', __name__)
JSON_DATA_FILE = 'friends.json'

# Global konstants för validering
EMAIL_REGEX = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

# --- Utility Functions (Hjälpfunktioner) ---

def load_data():
    if not os.path.exists(JSON_DATA_FILE):
        return []
    with open(JSON_DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(JSON_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- SANITIZATION FUNCTION (Tvättning) ---

def sanitize_value(value):
    """
    Rensar data från farliga HTML-taggar och onödiga mellanslag.
    Studenter: Detta kallas 'Sanitization' och skyddar mot XSS-attacker.
    """
    if value is None:
        return ""
    # re.sub raderar allt som matchar mönstret <...>
    clean_text = re.sub(r'<.*?>', '', str(value))
    return clean_text.strip()

# --- VALIDATION FUNCTION (Validering) ---

def validate_friend(friend_data, is_new=True, existing_data=None):
    """
    Kontrollerar att datan följer affärsreglerna.
    Returnerar (True, None) om OK, annars (False, "Felmeddelande").
    """
    # 1. Validera ID (endast vid POST/ny vän)
    if is_new:
        if not isinstance(friend_data.get('id'), int):
            return False, "ID must be an integer."
        if existing_data and any(f['id'] == friend_data['id'] for f in existing_data):
            return False, "ID already exists."

    # 2. Validera Namn (om det finns med i datan)
    if 'name' in friend_data:
        if not (2 <= len(friend_data['name']) <= 50):
            return False, "Name must be between 2 and 50 characters."

    # 3. Validera E-post (om det finns med i datan)
    if 'email' in friend_data:
        if not re.match(EMAIL_REGEX, friend_data['email']):
            return False, "Invalid email format."

    return True, None

# --- CRUD Operations ---

@friends_validate_bp.route('/', methods=['GET'])
def get_friends():
    return jsonify(load_data()), 200

@friends_validate_bp.route('/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    data = load_data()
    friend = next((f for f in data if f['id'] == friend_id), None)
    if friend:
        return jsonify(friend), 200
    return jsonify({"error": "Friend not found"}), 404

@friends_validate_bp.route('/', methods=['POST'])
def add_friend():
    all_friends = load_data()
    incoming = request.get_json()

    # Kontrollera att alla fält finns
    required = ['id', 'name', 'email', 'status']
    if not incoming or not all(field in incoming for field in required):
        return jsonify({"error": "Bad Request", "message": "Missing fields"}), 400

    # STEG 1: SANITIZE (Tvätta inkommande text)
    clean_data = {
        "id": incoming.get('id'),
        "name": sanitize_value(incoming.get('name')),
        "email": sanitize_value(incoming.get('email')).lower(),
        "status": sanitize_value(incoming.get('status'))
    }

    # STEG 2: VALIDATE (Kontrollera regler)
    is_valid, error_msg = validate_friend(clean_data, is_new=True, existing_data=all_friends)
    if not is_valid:
        return jsonify({"error": "Validation Error", "message": error_msg}), 400

    # STEG 3: FORMAT & SAVE
    new_friend = {
        "id": clean_data["id"],
        "name": clean_data["name"].title(),
        "email": clean_data["email"],
        "status": clean_data["status"].capitalize()
    }

    all_friends.append(new_friend)
    save_data(all_friends)
    return jsonify(new_friend), 201

@friends_validate_bp.route('/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    all_friends = load_data()
    incoming = request.get_json()
    
    # Hitta vännen i listan
    friend = next((f for f in all_friends if f['id'] == friend_id), None)
    if not friend:
        return jsonify({"error": "Not Found"}), 404

    # STEG 1: SANITIZE & UPDATE (Tvätta endast de fält som skickats)
    updates = {}
    if 'name' in incoming:
        updates['name'] = sanitize_value(incoming['name'])
    if 'email' in incoming:
        updates['email'] = sanitize_value(incoming['email']).lower()
    if 'status' in incoming:
        updates['status'] = sanitize_value(incoming['status'])

    # STEG 2: VALIDATE (Kolla om de uppdaterade värdena är okej)
    is_valid, error_msg = validate_friend(updates, is_new=False)
    if not is_valid:
        return jsonify({"error": "Validation Error", "message": error_msg}), 400

    # STEG 3: APPLY UPDATES
    if 'name' in updates: friend['name'] = updates['name'].title()
    if 'email' in updates: friend['email'] = updates['email']
    if 'status' in updates: friend['status'] = updates['status'].capitalize()

    save_data(all_friends)
    return jsonify(friend), 200

@friends_validate_bp.route('/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    all_friends = load_data()
    original_length = len(all_friends)
    
    # Filtrera bort vännen
    all_friends = [f for f in all_friends if f['id'] != friend_id]
    
    if len(all_friends) == original_length:
        return jsonify({"error": "Not Found"}), 404

    save_data(all_friends)
    return jsonify({"message": f"Friend {friend_id} deleted"}), 200