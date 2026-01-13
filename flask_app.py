#i öppna cmd skriv: python -m pip install beautifulsoup4
#python -m pip install flask
from flask import Flask, request, jsonify
import json
import os

from datetime import datetime
# Blueprints används för att dela upp stora appar i mindre moduler/filer
from myblueprints.friends_bp import friends_bp
from myblueprints.dunews_bp import dunews_bp
from myblueprints.duschema_bp import duschema_bp 


# Skapar själva Flask-appen
app = Flask(__name__)

# Inställningar för databas (här en enkel JSON-fil) och säkerhet
JSON_FRIENDS_FILE = 'friends.json'
API_KEY = "abcd"

# --- STRUKTUR ---
# Registrera en Blueprint. Det gör att vi kan gruppera rutter.
# url_prefix='/api/v1/friends' betyder att alla rutter i den filen 
# automatiskt får den här texten framför sig.
#http://127.0.0.1:5000/api/v1/friends/?api_key=abcd
app.register_blueprint(friends_bp, url_prefix='/api/v1/friends')
app.register_blueprint(dunews_bp, url_prefix='/dunews')
app.register_blueprint(duschema_bp, url_prefix='/duschema')

# --- HJÄLPFUNKTIONER (Datahantering) ---
def load_data():
    """Laddar vänner från JSON-filen. Skapar en tom lista om filen inte finns."""
    if not os.path.exists(JSON_FRIENDS_FILE):
        return []
    with open(JSON_FRIENDS_FILE, 'r') as json_friends:
        return json.load(json_friends)

def save_data(data):
    """Sparar ner hela listan med vänner till JSON-filen med snygg formatering (indent)."""
    with open(JSON_FRIENDS_FILE, 'w') as json_friends:
        json.dump(data,json_friends, indent=4)

# --- MIDDLEWARE / SÄKERHET ---
@app.before_request
def check_api_key():
    """
    Körs innan VARJE anrop. Kontrollerar att användaren har skickat med rätt API-nyckel.
    Detta är ett enkelt sätt att skydda sitt API.
    """
    # 1. Letar först i Headern (Standard i professionella API:er)
    key = request.headers.get('x-api-key')

    # 2. Om den inte finns där, kolla i URL-parametrarna (?api_key=abcd)
    if not key:
        key = request.args.get('api_key')

    # Om nyckeln inte matchar vår API_KEY, stoppa anropet direkt
    if key != API_KEY:
        # 401 Unauthorized är rätt HTTP-statuskod för saknad behörighet
        return jsonify({"error": "Unauthorized: Invalid or missing API Key"}), 401

# --- ROUTES (Själva API-ändpunkterna) ---

@app.route('/', methods=['GET'])
def home():
    """Enkel startsida för att se att servern lever."""
    return "Hello from flask"

@app.route("/hello/<name>")
def hello_there(name):
    now = datetime.now()
    """
    Code	Meaning	                                        Example Output
    %A	    The full weekday name.	                        Monday, Tuesday...
    %d	    The day of the month as a zero-padded number.	01, 15, 31
    %B	    The full month name.	                        January, February...
    %Y	    The four-digit year.	                        2026
    %X	    The locale’s appropriate time representation.	08:50:18
    """
    formatted_now = now.strftime("%A, %d %B, %Y at %X")
    content = "Hello there, " + name + "! It's " + formatted_now
    return content


# --- CRUD Operations (Create, Read, Update, Delete) ---
# http://127.0.0.1:5000/friends?api_key=abcd
@app.route('/friends', methods=['GET'])
def get_friends():
    """Hämtar alla vänner. Använder GET för att läsa data."""
    # 200 OK: Standard för lyckad hämtning
    return jsonify(load_data()), 200

#http://127.0.0.1:5000/friends/1?api_key=abcd
@app.route('/friends/<int:friend_id>', methods=['GET'])
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
    
@app.route('/friends', methods=['POST'])
def add_friend():
    """Skapar en ny vän. Använder POST för att skicka data till servern."""
    data = load_data()
    # request.json hämtar den data (JSON) som användaren skickade med i anropet
    new_friend = request.json

    # Enkel validering: Vi kräver att objektet har ett ID
    if not new_friend or 'id' not in new_friend:
        # 400 Bad Request: När klienten skickat felaktig eller ofullständig data
        return jsonify({"error": "Invalid data"}), 400

    data.append(new_friend)
    save_data(data)
    # 201 Created: Används när man har lyckats skapa en ny resurs
    return jsonify(new_friend), 201

@app.route('/friends/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    """Uppdaterar en befintlig vän baserat på ID. Använder PUT."""
    data = load_data()
    # Letar upp rätt vän i listan
    for friend in data:
        if friend['id'] == friend_id:
            # .update() slår ihop den gamla datan med den nya från request.json
            friend.update(request.json)
            save_data(data)
            # 200 OK: Uppdateringen lyckades
            return jsonify(friend), 200

    # Om vi loopat igenom allt utan att hitta ID:t
    # 404 Not Found: Resursen finns inte
    return jsonify({"error": "Friend not found"}), 404

@app.route('/friends/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    """Tar bort en vän baserat på ID. Använder DELETE."""
    data = load_data()
    # Skapar en ny lista där vi hoppar över den vän som ska bort (List Comprehension)
    updated_data = [f for f in data if f['id'] != friend_id]

    # Om listans längd är samma, hittades inget att ta bort
    #404 Not Found: Resursen finns inte
    if len(updated_data) == len(data):
        return jsonify({"error": "Friend not found"}), 404

    save_data(updated_data)
    # 200 OK (eller 204 No Content) bekräftar att borttagningen lyckades
    return jsonify({"message": "Deleted successfully"}), 200

# Startar applikationen
if __name__ == "__main__": 
    # debug=True gör att servern startar om automatiskt när du ändrar i koden
    app.run(debug=True)