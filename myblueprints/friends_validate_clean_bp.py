# myblueprints/friends_bp.py
from flask import Blueprint, request, jsonify
import json
import os

friends_validate_bp = Blueprint('friends_validate_bp', __name__)
JSON_DATA_FILE = 'friends.json'

# --- Hjälpfunktioner ---
def load_data():
    if not os.path.exists(JSON_DATA_FILE):
        return []
    with open(JSON_DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(JSON_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- CRUD Operations ---
#http://127.0.0.1:5000/api/v3/friends/
@friends_validate_bp.route('/', methods=['GET'])
def get_friends():
    # 200 OK: Standard response for successful GET
    return jsonify(load_data()), 200

#http://127.0.0.1:5000/api/v3/friends/1
#behöver inte valideras då flask gör det åt oss genom <int:friend_id>
@friends_validate_bp.route('/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    """
    Hämtar en enskild vän baserat på ID.
    <int:friend_id> i URL:en gör att Flask skickar med siffran som ett argument till funktionen.
    """
    data = load_data()
    
    # Vi letar igenom listan efter en vän med matchande ID
    # 'next' hämtar det första objektet som matchar villkoret, eller None om det inte finns
    friend = next((f for f in data if f['id'] == friend_id), None)

    if friend:
        # Om vännen hittas, returnera den med status 200 OK
        return jsonify(friend), 200
    else:
        # Om vännen inte finns, returnera ett felmeddelande med 404 Not Found
        return jsonify({"error": f"Friend with ID {friend_id} not found"}), 404

@friends_validate_bp.route('/', methods=['POST'])
def add_friend():
    data = load_data()
    incoming = request.json

    # 1. VALIDERING: Kontrollera att alla fält finns med
    required_fields = ['id', 'name', 'email', 'status']
    if not incoming or not all(field in incoming for field in required_fields):
        return jsonify({"error": "Bad Request", "message": "id, name, email och status krävs"}), 400

    # 2. VALIDERING: Kontrollera unikt ID
    if any(f['id'] == incoming['id'] for f in data):
        return jsonify({"error": "Bad Request", "message": "ID:t finns redan"}), 400

    # 3. TVÄTTNING: Snygga till datan innan den sparas
    # .strip() tar bort mellanslag, .lower() gör e-posten enhetlig
    clean_name = incoming['name'].strip().title()
    clean_email = incoming['email'].strip().lower()
    clean_status = incoming['status'].strip().capitalize() # "Close friend"

    new_friend = {
        "id": incoming['id'],
        "name": clean_name,
        "email": clean_email,
        "status": clean_status
    }

    data.append(new_friend)
    save_data(data)
    return jsonify(new_friend), 201

@friends_validate_bp.route('/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    data = load_data()
    incoming = request.json
    
    # Hitta vännen
    friend = next((f for f in data if f['id'] == friend_id), None)
    if not friend:
        return jsonify({"error": "Not Found", "message": "Vännen hittades inte"}), 404

    # 4. VALIDERING & TVÄTTNING: Uppdatera fält om de skickats med
    if incoming:
        if 'name' in incoming:
            friend['name'] = incoming['name'].strip().title()
        
        if 'email' in incoming:
            # Enkel validering: kolla om @ finns med i e-posten
            if "@" in incoming['email']:
                friend['email'] = incoming['email'].strip().lower()
            else:
                return jsonify({"error": "Bad Request", "message": "Ogiltig e-postadress"}), 400
        
        if 'status' in incoming:
            friend['status'] = incoming['status'].strip().capitalize()

    save_data(data)
    return jsonify(friend), 200

@friends_validate_bp.route('/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    data = load_data()
    # Kolla om ID finns innan vi raderar
    if not any(f['id'] == friend_id for f in data):
        return jsonify({"error": "Not Found", "message": "ID saknas"}), 404

    updated_data = [f for f in data if f['id'] != friend_id]
    save_data(updated_data)
    return jsonify({"message": f"Vän {friend_id} raderad"}), 200