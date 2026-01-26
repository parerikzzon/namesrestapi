# myblueprints/friends_refactor_bp.py
from flask import Blueprint, request, jsonify
import json
import os
friends_refactor_bp = Blueprint('friends_refactor_bp', __name__)
JSON_DATA_FILE = 'friends.json'
def load_data():
    if not os.path.exists(JSON_DATA_FILE):
        return []
    with open(JSON_DATA_FILE, 'r') as json_friends:
        return json.load(json_friends)

def save_data(data):
    with open(JSON_DATA_FILE, 'w') as json_friends:
        json.dump(data, json_friends, indent=4)


# --- CRUD Operations ---
#http://127.0.0.1:5000/api/v3/friends/
@friends_refactor_bp.route('/', methods=['GET'])
def get_friends():
    # 200 OK: Standard response for successful GET
    return jsonify(load_data()), 200

#http://127.0.0.1:5000/api/v3/friends/1
@friends_refactor_bp.route('/<int:friend_id>', methods=['GET'])
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


@friends_refactor_bp.route('/', methods=['POST'])
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


@friends_refactor_bp.route('/<int:friend_id>', methods=['PUT'])
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
#api/v1/friends/2
@friends_refactor_bp.route('/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    data = load_data()
    updated_data = [f for f in data if f['id'] != friend_id]

    if len(updated_data) == len(data):
        return jsonify({"error": "Friend not found"}), 404

    save_data(updated_data)
    # 204 No Content: Success, but nothing to return (common for DELETE)
    # Or use 200 OK with a message
    return jsonify({"message": "Deleted successfully"}), 200