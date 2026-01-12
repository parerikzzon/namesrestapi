from flask import Flask, request, jsonify
import json
import os
from myblueprints.friends_bp import friends_bp #importerar från myblueprints mappen

app = Flask(__name__)
DATA_FILE = 'friends.json'
API_KEY = "abcd"

# Registrera Blueprinten
# url_prefix gör att alla rutter i friends_bp börjar med api/v1/friends
app.register_blueprint(friends_bp, url_prefix='/api/v1/friends')

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

# Security Check
@app.before_request
def check_api_key():
    # 1. Try to get the key from the Header
    key = request.headers.get('x-api-key')

    # 2. If it's not in the header, look in the URL parameters (friends?api_key=...)
    if not key:
        key = request.args.get('api_key')

    if key != API_KEY:
        return jsonify({"error": "Unauthorized: Invalid or missing API Key"}), 401

@app.route('/', methods=['GET'])
def home():
    return "Hello from flask"
# --- CRUD Operations ---

@app.route('/friends', methods=['GET'])
def get_friends():
    # 200 OK: Standard response for successful GET
    return jsonify(load_data()), 200

@app.route('/friends', methods=['POST'])
def add_friend():
    data = load_data()
    new_friend = request.json

    if not new_friend or 'id' not in new_friend:
        # 400 Bad Request: Client sent invalid data
        return jsonify({"error": "Invalid data"}), 400

    data.append(new_friend)
    save_data(data)
    # 201 Created: Successful post resulting in a new resource
    return jsonify(new_friend), 201

@app.route('/friends/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    data = load_data()
    for friend in data:
        if friend['id'] == friend_id:
            friend.update(request.json)
            save_data(data)
            # 200 OK: Resource updated successfully
            return jsonify(friend), 200

    # 404 Not Found: Resource with that ID doesn't exist
    return jsonify({"error": "Friend not found"}), 404

@app.route('/friends/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    data = load_data()
    updated_data = [f for f in data if f['id'] != friend_id]

    if len(updated_data) == len(data):
        return jsonify({"error": "Friend not found"}), 404

    save_data(updated_data)
    # 204 No Content: Success, but nothing to return (common for DELETE)
    # Or use 200 OK with a message
    return jsonify({"message": "Deleted successfully"}), 200

if __name__ == "__main__": 
    app.run(debug=True)