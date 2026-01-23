#i öppna cmd skriv: python -m pip install beautifulsoup4
#python -m pip install flask
from flask import Flask, request, jsonify
import json
import os

from datetime import datetime
# Blueprints används för att dela upp stora appar i mindre moduler/filer
from myblueprints.friends_messy_bp import friends_messy_bp
from myblueprints.friends_refactor_bp import friends_refactor_bp
from myblueprints.friends_validate_clean_bp import friends_validate_bp
from myblueprints.friends_apikey_bp import friends_apikey_bp
from myblueprints.friends_respository_bp import friends_repository_bp

from myblueprints.dunews_bp import dunews_bp
from myblueprints.duschema_bp import duschema_bp 
from myblueprints.regex_bp import regex_bp


# Skapar själva Flask-appen
app = Flask(__name__)

# Inställningar för databas (här en enkel JSON-fil) och säkerhet
JSON_FRIENDS_FILE = 'friends.json'
API_KEY = "abcd"

# --- STRUKTUR ---
# Registrera en Blueprint. Det gör att vi kan gruppera rutter.
# url_prefix='/api/v1/friends' betyder att alla rutter i den filen 
# automatiskt får den här texten framför sig.
app.register_blueprint(friends_messy_bp, url_prefix='/api/v2/friends')#http://127.0.0.1:5000/api/v2/friends
app.register_blueprint(friends_refactor_bp, url_prefix='/api/v3/friends')#http://127.0.0.1:5000/api/v3/friends
app.register_blueprint(friends_validate_bp, url_prefix='/api/v4/friends')#http://127.0.0.1:5000/api/v4/friends
app.register_blueprint(friends_apikey_bp, url_prefix='/api/v5/friends') #http://127.0.0.1:5000/api/v5/friends/?api_key=abc
app.register_blueprint(friends_repository_bp, url_prefix='/api/v6/friends') #http://127.0.0.1:5000/api/v6/friends/?api_key=abc


app.register_blueprint(dunews_bp, url_prefix='/dunews')
app.register_blueprint(duschema_bp, url_prefix='/duschema')
app.register_blueprint(regex_bp, url_prefix='/regex')


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
# http://127.0.0.1:5000/api/v1/friends
@app.route('/api/v1/friends', methods=['GET'])
def get_friends():
    # 'with open' öppnar filen friends.json så vi kan läsa den ('r' står för read)
    with open('friends.json', 'r') as f:
        # json.load förvandlar innehållet i filen till en vanlig Python-lista
        data = json.load(f)
    
    # jsonify förvandlar Python-listan tillbaka till JSON-format så webbläsaren förstår den.
    # 200 är statuskoden för 'OK'.
    return jsonify(data), 200

#http://127.0.0.1:5000/api/v1/friends/1
@app.route('/api/v1/friends/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    with open('friends.json', 'r') as f:
        data = json.load(f)
    
    # Vi går igenom listan 'data', en person i taget (vi kallar varje person för 'friend')
    for friend in data:
        # Om personens id är samma som det id som står i URL:en...
        if friend['id'] == friend_id:
            # HTTP stus kod 200 för ett lyckat anrop. Används oftast vid GET (hämta), PUT (uppdatera) och DELETE (ta bort). 
            # Det betyder: "Här är det du bad om" tex en vän med detta id eller alla vänner eller "Jag har utfört ändringen".
            return jsonify(friend), 200
            
    # Om vi har gått igenom hela listan utan att hitta id:t, skickar vi ett felmeddelande.
    # 404 betyder 'Hittades inte'. Du försöker letar efter en vän med ett ID som inte existerar i JSON-filen.
    return jsonify({"error": "Hittades inte"}), 404

##http://127.0.0.1:5000/api/v1/friends   
@app.route('/api/v1/friends', methods=['POST'])
def add_friend():
    with open('friends.json', 'r') as f:
        data = json.load(f)
    
    # request.json hämtar den data som användaren skickade (t.ex. från Postman)
    new_friend = request.json
    
    # Vi lägger till den nya vännen i vår lista
    data.append(new_friend)
    
    # Nu öppnar vi filen igen, men med 'w' (write) för att skriva över den med den nya listan
    with open('friends.json', 'w') as f:
        # indent=4 gör att JSON-filen ser snygg och läsbar ut för människor
        json.dump(data, f, indent=4)
        
    # 201 betyder 'Created' (Skapad). Vi skickar tillbaka den nya vännen som bekräftelse.
    #Används specifikt vid POST. Det betyder: "Jag har tagit emot din data och skapat en ny resurs (t.ex. en ny vän i listan)".
    return jsonify(new_friend), 201
#http://127.0.0.1:5000/api/v1/friends/1
@app.route('/api/v1/friends/<int:friend_id>', methods=['PUT'])
def update_friend(friend_id):
    with open('friends.json', 'r') as f:
        data = json.load(f)
    
    for friend in data:
        if friend['id'] == friend_id:
            # .update tar informationen från användaren och ändrar fälten i vårt objekt
            friend.update(request.json)
            
            # Spara ner hela den uppdaterade listan till filen igen
            with open('friends.json', 'w') as f:
                json.dump(data, f, indent=4)
            return jsonify(friend), 200

    return jsonify({"error": "Hittades inte"}), 404

#http://127.0.0.1:5000/api/v1/friends/1
@app.route('/api/v1/friends/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    with open('friends.json', 'r') as f:
        data = json.load(f)
    
    # Vi skapar en tom lista där vi ska lägga alla vänner vi vill ha kvar
    new_data = []
    for friend in data:
        # Om personens id INTE är det id vi vill ta bort...
        if friend['id'] != friend_id:
            # ...så lägger vi till dem i den nya listan.
            new_data.append(friend)
            
    # Spara den nya listan (där den borttagna personen nu saknas)
    with open('friends.json', 'w') as f:
        json.dump(new_data, f, indent=4)
        
    return jsonify({"message": "Borttagen"}), 200

# Startar applikationen
if __name__ == "__main__": 
    # debug=True gör att servern startar om automatiskt när du ändrar i koden
    app.run(debug=True)