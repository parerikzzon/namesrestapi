from flask import Blueprint, request, render_template
from flask_restful import Api, Resource, reqparse, abort #kom ihåg att installera flask-restful jag behövde stå i cmd prompten för att kunna göra detta: python -m pip install flask-restful  
import re
# Vi hämtar klassen från mappen 'myblueprints/repositories' och filen 'friend_repository'
from .repositories.friendrepository import FriendRepository

# --- Skapa blueprinten ---
friends_restful_bp = Blueprint('friends_restful_bp', __name__)
#Vi kopplar Flask-RESTful Api till vår blueprint.
# Detta gör att vi kan använda klasser (Resources) istället för vanliga funktioner.
api = Api(friends_restful_bp) # kopplar Flask-RESTful to the Blueprint

repo = FriendRepository('friends.json')

VALID_API_KEY = "abc"
EMAIL_REGEX = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'

# ---  Kollar av api ---
@friends_restful_bp.before_request
def check_api_key():
    #Körs före varje anrop. I REST-sammanhang är detta vår 'dörrvakt'.
    #Flask-RESTful Resource-klasser respekterar Blueprintens before_request.
    api_key = request.headers.get('x-api-key') or request.args.get('api_key')
    if api_key != VALID_API_KEY:
        # Vi returnerar en dict + statuskod. Flask-RESTful gör om det till JSON automatiskt.
        return {"error": "Unauthorized", "message": "Valid API-key required."}, 401
    
@friends_restful_bp.route('/ui') #http://127.0.0.1:5000/api/v7/friends/ui?api_key=abc
def friends_page():
    # Renderar templates/friends.html
    return render_template('crudview.html')

# --- 2. Request Parsing & Sanitization ---
# Denna funktion skickas in i vår Parser nedan. 
#Den tvättar datan INNAN den ens når våra GET/POST-metoder.
def sanitize_type(value):    
    # Om värdet är None, en tom sträng eller bara mellanslag
    if value is None or str(value).strip() == "":
        # Genom att kasta ValueError här, stoppar Flask-RESTful anropet
        # och skickar automatiskt tillbaka ett felmeddelande till användaren.
        raise ValueError("Field cannot be empty or null")
    
    # Ta bort HTML-taggar och mellanslag i början/slutet
    clean = re.sub(r'<.*?>', '', str(value)).strip()
    return clean

# Parsar POST/PUT
# Istället för att använda request.get_json() och kolla manuellt, 
# skapar vi en mall för hur inkommande data SKA se ut.
friend_parser = reqparse.RequestParser()
friend_parser = reqparse.RequestParser()

# För ID: Krävs, får inte vara null, och måste vara ett heltal
friend_parser.add_argument('id', 
    type=int, 
    required=True, 
    nullable=False, 
    help='ID is required and must be a valid integer.')

# För övriga fält: Använd vår nya strikta egen gjorda funktion sanitize_type
friend_parser.add_argument('name', type=sanitize_type, required=True, help='Name is required')
friend_parser.add_argument('email', type=sanitize_type, required=True, help="Email is required")
friend_parser.add_argument('status', type=sanitize_type, required=True, help="Status is required")

# ---  Resources ---
#I Flask-RESTful grupperar vi logiken i klasser baserat på URL-end pointen.
class FriendList(Resource):
    #Hanterar anrop till roten, t.ex. /api/v7/friends/
    #för att få alla friends
    def get(self):
        return repo.get_all(), 200

    def post(self):
        #Skapa en ny vän
        # parse_args() hämtar datan, tvättar den (via sanitize_type) 
        # och skickar felmeddelande direkt om något saknas (pga av required=True).
        args = friend_parser.parse_args()
        
        # Kontrollera affärsregler (t.ex. om ID redan finns)
        if repo.get_by_id(args['id']):
            abort(400, message="ID already exists.")
        
        if not (2 <= len(args['name']) <= 50):
            abort(400, message="Name must be between 2 and 50 characters.")
            
        if not re.match(EMAIL_REGEX, args['email']):
            abort(400, message="Invalid email format.")

        # Formattering
        args['name'] = args['name'].title()
        args['email'] = args['email'].lower()
        args['status'] = args['status'].capitalize()

        new_friend = repo.add(args)
        return new_friend, 201

class FriendItem(Resource):
    #Hanterar anrop till specifika ID:n, t.ex. /api/v7/friends/1
    def get(self, friend_id):
        friend = repo.get_by_id(friend_id)
        if not friend:
            abort(404, message=f"Friend {friend_id} not found")
        return friend, 200

    def put(self, friend_id):
        #Uppdatera en befintlig vän /api/v7/friends/2
        if not repo.get_by_id(friend_id):
            abort(404, message="Friend not found")
            
        # Use partial parsing (don't require all fields for PUT)
        args = friend_parser.parse_args()
        
        # Re-apply formatting
        if args['name']: args['name'] = args['name'].title()
        if args['email']: args['email'] = args['email'].lower()
        if args['status']: args['status'] = args['status'].capitalize()

        updated_friend = repo.update(friend_id, args)
        return updated_friend, 200

    def delete(self, friend_id):
        #Radera en vän /api/v7/friends/1
        if repo.delete(friend_id):
            return {"message": f"Friend {friend_id} deleted"}, 200
        abort(404, message="Friend not found")

# --- 4. Registera routes ---
# Since url_prefix is '/api/v7/friends' in flask_app.py, these paths are relative to that.
api.add_resource(FriendList, '/')                 # Becomes: /api/v7/friends/ för at thater GET för att hämat all vänner och POST för att lägg till en vän
api.add_resource(FriendItem, '/<int:friend_id>')  # Becomes: /api/v7/friends/1 för att hantera enskild vän vid PUT och DELETE

