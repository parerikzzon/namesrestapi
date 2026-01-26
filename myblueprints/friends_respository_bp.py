# myblueprints/friends_repository_bp.py
from flask import Blueprint, request, jsonify
import re
# Vi hämtar klassen från mappen 'myblueprints/repositories' och filen 'friend_repository'
from .repositories.friendrepository import FriendRepository

# Skapar Blueprint
friends_repository_bp = Blueprint('friends_repository_bp', __name__)

# Initiera repository-instansen med sökvägen till JSON-filen
repo = FriendRepository('friends.json')

# Global konstant för e-postmönster
EMAIL_REGEX = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

VALID_API_KEY = "abc"  # Vår enkla, fasta nyckel

# --- 1. SANITIZATION FUNCTION (Tvättning) ---

def sanitize_value(value):
    """
    Rensar bort HTML-taggar och tar bort mellanslag i början/slutet.
    Studenter: Detta steg gör att datan blir säker att hantera.
    """
    if value is None:
        return ""
    # Tar bort allt som ser ut som en HTML-tagg: <...>
    clean_text = re.sub(r'<.*?>', '', str(value))
    return clean_text.strip()

# --- 2. VALIDATION FUNCTION (Validering) ---

def validate_friend(friend_data, is_new=True):
    """
    Kontrollerar affärsregler på den tvättade datan.
    Returnerar (True, None) om allt är okej.
    """
    # Kolla ID om det är en ny vän (POST)
    if is_new:
        if not isinstance(friend_data.get('id'), int):
            return False, "ID must be an integer."
        # Använder repositoryt för att kolla om ID redan finns
        if repo.get_by_id(friend_data.get('id')):
            return False, "ID already exists."

    # Kolla Namn (Längd)
    if 'name' in friend_data:
        if not (2 <= len(friend_data['name']) <= 50):
            return False, "Name must be between 2 and 50 characters."

    # Kolla E-post (Format via Regex)
    if 'email' in friend_data:
        if not re.match(EMAIL_REGEX, friend_data['email']):
            return False, "Invalid email format."

    return True, None
# --- Säkerhetskontroll ---
#Genom att lägga det i @before_request skyddar vi hela Blueprinten på en gång. Om den inte går igenom, körs aldrig koden i övriga end points/route överhuvudtaget.
#http://127.0.0.1:5000/api/v6/friends/?api_key=abc
@friends_repository_bp.before_request
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
# --- API ROUTES ---
#http://127.0.0.1:5000/api/v6/friends/?api_key=abc
@friends_repository_bp.route('/', methods=['GET'])
def get_friends():
    """
    Hämtar alla vänner.
    Anropar repo.get_all() som sköter filkontakten.
    """
    all_friends = repo.get_all()
    
    # Vi skickar tillbaka listan som JSON med statuskod 200 (OK)
    return jsonify(all_friends), 200

#http://127.0.0.1:5000/api/v6/friends/1?api_key=abc
@friends_repository_bp.route('/<int:friend_id>', methods=['GET'])
def get_friend_by_id(friend_id):
    """
    Hämtar en enskild vän med hjälp av repositoryt.
    """
    # Vi ber repositoryt att hitta vännen åt oss
    friend = repo.get_by_id(friend_id)

    if friend:
        # Om vännen finns (inte är None), returnera den
        return jsonify(friend), 200
    
    # Om vännen inte hittades (None), returnera 404
    return jsonify({"error": f"Friend with ID {friend_id} not found"}), 404

@friends_repository_bp.route('/', methods=['POST'])
def add_friend():
    incoming = request.get_json()

    # Kontrollera att alla fält finns med i anropet
    required = ['id', 'name', 'email', 'status']
    if not incoming or not all(field in incoming for field in required):
        return jsonify({"error": "Bad Request", "message": "Missing required fields"}), 400

    # STEG 1: SANITIZE (Tvätta inkommande data först)
    clean_data = {
        "id": incoming.get('id'),
        "name": sanitize_value(incoming.get('name')),
        "email": sanitize_value(incoming.get('email')).lower(),
        "status": sanitize_value(incoming.get('status'))
    }

    # STEG 2: VALIDATE (Kontrollera regler på den rena datan)
    is_valid, error_msg = validate_friend(clean_data, is_new=True)
    if not is_valid:
        return jsonify({"error": "Validation Error", "message": error_msg}), 400

    # STEG 3: FORMAT & REPOSITORY (Spara via klassen)
    # Vi snyggar till texten precis innan den sparas
    clean_data["name"] = clean_data["name"].title()
    clean_data["status"] = clean_data["status"].capitalize()

    new_friend = repo.add(clean_data)
    return jsonify(new_friend), 201

@friends_repository_bp.route('/<int:friend_id>', methods=['PUT'])
def pdate_friend(friend_id):
    incoming = request.get_json()
    
    # Kontrollera om vännen finns i vårt repository
    if not repo.get_by_id(friend_id):
        return jsonify({"error": "Not Found"}), 404

    # STEG 1: SANITIZE (Tvätta bara de fält som skickats)
    updates = {}
    if 'name' in incoming: updates['name'] = sanitize_value(incoming['name'])
    if 'email' in incoming: updates['email'] = sanitize_value(incoming['email']).lower()
    if 'status' in incoming: updates['status'] = sanitize_value(incoming['status'])

    # STEG 2: VALIDATE (Kolla reglerna på den tvättade datan)
    is_valid, error_msg = validate_friend(updates, is_new=False)
    if not is_valid:
        return jsonify({"error": "Validation Error", "message": error_msg}), 400

    # STEG 3: FORMAT & UPDATE
    if 'name' in updates: updates['name'] = updates['name'].title()
    if 'status' in updates: updates['status'] = updates['status'].capitalize()

    updated_friend = repo.update(friend_id, updates)
    return jsonify(updated_friend), 200



@friends_repository_bp.route('/<int:friend_id>', methods=['DELETE'])
def delete_friend(friend_id):
    # Repository-klassen sköter logiken för borttagning
    if repo.delete(friend_id):
        return jsonify({"message": f"Friend {friend_id} deleted"}), 200
    return jsonify({"error": "Not Found"}), 404