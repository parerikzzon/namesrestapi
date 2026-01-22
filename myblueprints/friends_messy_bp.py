# myblueprints/friends__messy_bp.py
from flask import Blueprint, request, jsonify
import json

# Vi skapar en 'Blueprint'. Tänk på det som en egen liten under-avdelning 
# i vår applikation som bara hanterar allt som har med 'vänner' att göra.
friends_messy_bp = Blueprint('friends_messy_bp', __name__)

# --- CRUD Operations (Skapa, Läsa, Uppdatera, Ta bort) ---

# Denna route körs när någon går till adressen med en GET-förfrågan (för att hämta data)
#http://127.0.0.1:5000/api/v2/friends/
@friends_messy_bp.route('/', methods=['GET'])
def get_friends():
    # 'with open' öppnar filen friends.json så vi kan läsa den ('r' står för read)
    with open('friends.json', 'r') as f:
        # json.load förvandlar innehållet i filen till en vanlig Python-lista
        data = json.load(f)
    
    # jsonify förvandlar Python-listan tillbaka till JSON-format så webbläsaren förstår den.
    # 200 är statuskoden för 'OK'.
    return jsonify(data), 200


# Denna route tar emot ett ID i adressen, t.ex. /friends/1
@friends_messy_bp.route('/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    with open('friends.json', 'r') as f:
        data = json.load(f)
    
    # Vi går igenom listan 'data', en person i taget (vi kallar varje person för 'friend')
    for friend in data:
        # Om personens id är samma som det id som står i URL:en...
        if friend['id'] == friend_id:
            # HTTP stus kod 200 för ett lyckat anrop. Används oftast vid GET (hämta), PUT (uppdatera) och DELETE (ta bort). Det betyder: "Här är det du bad om" eller "Jag har utfört ändringen".
            return jsonify(friend), 200
            
    # Om vi har gått igenom hela listan utan att hitta id:t, skickar vi ett felmeddelande.
    # 404 betyder 'Hittades inte'. Du försöker letar efter en vän med ett ID som inte existerar i JSON-filen.
    return jsonify({"error": "Hittades inte"}), 404


# Denna route används för att skapa en ny vän med POST
@friends_messy_bp.route('/', methods=['POST'])
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


# Denna route ändrar en befintlig vän
@friends_messy_bp.route('/<int:friend_id>', methods=['PUT'])
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


# Denna route tar bort en vän
@friends_messy_bp.route('/<int:friend_id>', methods=['DELETE'])
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