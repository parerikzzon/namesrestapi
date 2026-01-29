from flask import Blueprint, jsonify, render_template
import requests
from bs4 import BeautifulSoup

duschema_bp = Blueprint('duschema_bp', __name__, template_folder='templates')

# URL till schemat (TimeEdit grafisk vy)
BASE_URL = "https://cloud.timeedit.net/hda/web/public/ri1t6fZ7YQb1bnQY53Q9YQtnZ507fX966n5756ny.html"

def skrapa_schema_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # 1. Hämta HTML-koden från TimeEdit
        response = requests.get(BASE_URL, headers=headers, timeout=10)
        response.raise_for_status() 
        
        # 2. Skapa soppan (översättaren)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 3. Hitta alla DIV-taggar med klassen 'bookingDiv'
        # Varje sådan DIV representerar en lektion i schemat
        bokningar_divs = soup.find_all('div', class_='bookingDiv')
        
        schema_positioner = []
        
        for bokning in bokningar_divs:
            # Extrahera strängen från 'title'-attributet (där all info finns)
            info_strang = bokning.get('title', '')
            
            if info_strang:
                #
                #title=" 2026-01-27 08:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Lektion, Ulrika Artursson Wissa, Borlänge, B302 Lärosal/etage ID 669214" 
                # Här gör vi "Clean Code": 
                # .split(',') delar upp texten vid varje kommatecken till en lista (array)
                # [p.strip() for p in ...] går igenom varje del och tar bort onödiga mellanslag direkt
                parts = [p.strip() for p in info_strang.split(',')]
                
                # Tiden ligger alltid i första delen: "2026-01-22 10:00 - 12:00"
                # Vi delar den vid mellanslag för att få ut datum och klockslag separat
                time_parts = parts[0].split(' ')# till array
                
                # --- LOGIK FÖR LÄRARE ---
                # Ibland finns "Grupp X" på lärarens plats (index 3). 
                # Om ordet 'grupp' finns, hoppar vi till index -3 (tredje sista elementet)
                larare = parts[3] if "grupp" not in parts[3].lower() else parts[-3]

                # --- BYGG DICTIONARY ---
                # Vi skapar ett paket för varje lektion
                schema_post = {
                    "datum": time_parts[0] if len(time_parts) > 0 else "Saknas",
                    "tid": f"{time_parts[1]} - {time_parts[3]}" if len(time_parts) >= 4 else "Saknas",
                    "kurs": parts[1] if len(parts) > 1 else "Saknas",
                    "larare": larare,
                    # Lokalen står sist. Vi tar sista delen (index -1) och plockar första ordet
                    "lokal": parts[-1].split(' ')[0] if len(parts) > 0 else "Saknas",
                    # Typen (Föreläsning/Handledning) ligger oftast 4 steg från slutet
                    "typ": parts[-4] if len(parts) >= 4 else "Saknas"
                }
                
                schema_positioner.append(schema_post)

        return schema_positioner

    except Exception as e:
        # Om något går fel returnerar vi None så att vi kan hantera felet i routerna
        print(f"Ett fel uppstod: {e}")
        return None

@duschema_bp.route('/')
def get_schema():
    data = skrapa_schema_data()
    
    # Om skrapningen misslyckades (returnerade None)
    if data is None:
        return jsonify({"error": "Kunde inte hämta schemat från TimeEdit"}), 500
    
    return jsonify({
        "status": "success",
        "schema": data
    }), 200

@duschema_bp.route('/view')
def show_schema():
    data = skrapa_schema_data()
    # Om data är None skickar vi en tom lista [] så att HTML-sidan inte kraschar
    return render_template('schema.html', schema=data or [])