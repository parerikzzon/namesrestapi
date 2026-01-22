from flask import Blueprint, request, jsonify, render_template
import json
import os
"""
# --- REPOSITORY KLASS ---
# Denna klass sköter all kontakt med JSON-filen
class FriendRepository:
    def __init__(self, file_path):
        self.file_path = file_path

    def _load(self):
        if not os.path.exists(self.file_path):
            return []
        with open(self.file_path, 'r') as f:
            return json.load(f)

    def _save(self, data):
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=4)

    def get_all(self):
        return self._load()

    def get_by_id(self, friend_id):
        data = self._load()
        return next((f for f in data if f['id'] == friend_id), None)

    def add(self, friend_dict):
        data = self._load()
        data.append(friend_dict)
        self._save(data)
        return friend_dict

    def update(self, friend_id, updates):
        data = self._load()
        for friend in data:
            if friend['id'] == friend_id:
                friend.update(updates)
                self._save(data)
                return friend
        return None

    def delete(self, friend_id):
        data = self._load()
        if not any(f['id'] == friend_id for f in data):
            return False
        updated_data = [f for f in data if f['id'] != friend_id]
        self._save(updated_data)
        return True
"""
# --- BLUEPRINT KONFIGURATION ---
# Från mappen repositories (punkt betyder 'inuti denna mapp') 
# importera filen friendrepository.py och klassen FriendRepository
from .repositories.friendrepository import FriendRepository

# Skapa instansen av repot precis som vanligt
repo = FriendRepository('friends.json')
friends_repository_bp = Blueprint('friends_repository_bp', __name__, template_folder='templates')
VALID_API_KEY = "abc"
repo = FriendRepository('friends.json')# anvädn i endposnte/routes för att gör crdu opertion mot json filen

# --- SÄKERHET (DÖRRVAKT) ---

@friends_repository_bp.before_request
def check_api_key():
    # Kollar både Headers och URL-parametrar
    api_key = request.headers.get('x-api-key') or request.args.get('api_key')
    if api_key != VALID_API_KEY:
        return jsonify({
            "error": "Unauthorized", 
            "message": "Giltig API-nyckel krävs"
        }), 401

# --- ROUTES (CRUD) ---

@friends_repository_bp.route('/', methods=['GET'])
def get_friends():
    return jsonify(repo.get_all()), 200

@friends_repository_bp.route('/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    friend = repo.get_by_id(friend_id)
    if friend:
        return jsonify(friend), 200
    return jsonify({"error": "Not Found", "message": "Vännen hittades inte"}), 404

@friends_repository_bp.route('/', methods=['POST'])
def add_friend():
    incoming = request.json
    required = ['id', 'name', 'email', 'status']
    
    # Validering: Saknas fält?
    if not incoming or not all(k in incoming for k in required):
        return jsonify({"error": "Bad Request", "message": "id, name, email och status krävs"}), 400

    # Validering: Finns ID redan?
    if repo.get_by_id(incoming['id']):
        return jsonify({"error": "Conflict", "message": "ID:t är redan upptaget"}), 409

    # Tvättning (Sanitization)
    clean_friend = {
        "id": incoming['id'],
        "name": incoming['name'].strip().title(),
        "email": incoming['email'].strip().lower(),
        "status": incoming['status'].strip().capitalize()
    }

    result = repo.add(clean_friend)
    return jsonify(result), 201

@friends_repository_bp.route('/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    incoming = request.json
    if not repo.get_by_id(friend_id):
        return jsonify({"error": "Not Found", "message": "Vännen finns inte"}), 404

    # Tvättning av fält som ska uppdateras
    updates = {}
    if 'name' in incoming: updates['name'] = incoming['name'].strip().title()
    if 'email' in incoming: updates['email'] = incoming['email'].strip().lower()
    if 'status' in incoming: updates['status'] = incoming['status'].strip().capitalize()

    updated_friend = repo.update(friend_id, updates)
    return jsonify(updated_friend), 200

@friends_repository_bp.route('/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    if repo.delete(friend_id):
        return jsonify({"message": f"Vän med ID {friend_id} raderad"}), 200
    return jsonify({"error": "Not Found", "message": "Kunde inte hitta vännen"}), 404

@friends_repository_bp.route('/ui')
def friends_page():
    # Laddar HTML-filen från /myblueprints/templates/crudview.html
    return render_template('crudview.html')