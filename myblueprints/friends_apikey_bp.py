# myblueprints/friends_bp.py
from flask import Blueprint, request, jsonify, render_template
import json
import os

# Vi skapar en ny Blueprint för säkerhets-etappen
friends_apikey_bp = Blueprint('friends_apikey_bp', __name__)
JSON_DATA_FILE = 'friends.json'
VALID_API_KEY = "abc"  # Vår enkla, fasta nyckel

# --- Säkerhetskontroll ---
#Genom att lägga det i @before_request skyddar vi hela Blueprinten på en gång. Om den inte går igenom, körs aldrig koden i övriga end points/route överhuvudtaget.
@friends_apikey_bp.before_request
def check_api_key():
    """
    Denna funktion körs AUTOMATISKT före varje anrop till denna blueprint.
    Om nyckeln saknas eller är fel, stoppar vi anropet direkt.
    """
    # 1. Kolla om nyckeln finns i Headern (Standard i API:er)
    api_key = request.headers.get('x-api-key')
    
    # 2. Om den inte fanns där, kolla i URL:en (?api_key=abc)
    if not api_key:
        api_key = request.args.get('api_key')
        
    # 3. Validera nyckeln
    if api_key != VALID_API_KEY:
        # 401 Unauthorized: Stopp! Du har inte behörighet.
        return jsonify({
            "error": "Unauthorized", 
            "message": "Du måste ange en giltig API-nyckel för att få tillgång."
        }), 401

# --- Hjälpfunktioner ---
def load_data():
    if not os.path.exists(JSON_DATA_FILE):
        return []
    with open(JSON_DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(JSON_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# --- CRUD Operations dess körs inte om man inte passera @friends_security_bp.before_request ---
#http://127.0.0.1:5000/api/v5/friends/?api_key=abc
@friends_apikey_bp.route('/', methods=['GET'])
def get_friends():
    return jsonify(load_data()), 200

#http://127.0.0.1:5000/api/v5/friends/1?api_key=abc
@friends_apikey_bp.route('/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    data = load_data()
    friend = next((f for f in data if f['id'] == friend_id), None)
    if friend:
        return jsonify(friend), 200
    return jsonify({"error": "Not Found", "message": "Vännen hittades inte"}), 404

@friends_apikey_bp.route('/', methods=['POST'])
def add_friend():
    data = load_data()
    incoming = request.json
    
    # Validering av obligatoriska fält
    required = ['id', 'name', 'email', 'status']
    if not incoming or not all(k in incoming for k in required):
        return jsonify({"error": "Bad Request", "message": "Saknar data"}), 400

    # Tvättning
    new_friend = {
        "id": incoming['id'],
        "name": incoming['name'].strip().title(),
        "email": incoming['email'].strip().lower(),
        "status": incoming['status'].strip().capitalize()
    }

    data.append(new_friend)
    save_data(data)
    return jsonify(new_friend), 201

@friends_apikey_bp.route('/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    data = load_data()
    incoming = request.json
    friend = next((f for f in data if f['id'] == friend_id), None)
    
    if not friend:
        return jsonify({"error": "Not Found"}), 404

    if incoming:
        if 'name' in incoming: friend['name'] = incoming['name'].strip().title()
        if 'email' in incoming: friend['email'] = incoming['email'].strip().lower()
        if 'status' in incoming: friend['status'] = incoming['status'].strip().capitalize()

    save_data(data)
    return jsonify(friend), 200

@friends_apikey_bp.route('/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    data = load_data()
    if not any(f['id'] == friend_id for f in data):
        return jsonify({"error": "Not Found"}), 404

    updated_data = [f for f in data if f['id'] != friend_id]
    save_data(updated_data)
    return jsonify({"message": "Raderad"}), 200

@friends_apikey_bp.route('/ui') #http://127.0.0.1:5000/api/v5/friends/ui?api_key=abc
def friends_page():
    # Renderar templates/friends.html
    return render_template('crudview.html')