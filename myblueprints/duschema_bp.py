from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup

duschema_bp = Blueprint('duschema_bp', __name__)

#http://127.0.0.1:5000/duschema/?api_key=abcd
@duschema_bp.route('/')
def get_schema():
    data_schema = skrapa_schema_data()
    """
    Raden kontrollerar två saker innan svaret skickas till webbläsaren:
    1. isinstance(data_schema, dict): Den kollar om variabeln data_schema är en "dictionary" (ordlista). 
    Din funktion skrapa_schema_data returnerar normalt sett en lista med lektioner, men om ett fel uppstår returnerar den en dict (t.ex. {"error": "Nätverksfel"}).
    2. "error" in data_schema: Om det är en dict, letar den efter en nyckel som heter just "error".
    Utan denna kontroll skulle denn försöka skicka ut ett "lyckat" svar även när skrapningen misslyckats, vilket skapar flera problem:
    """
    if isinstance(data_schema, dict) and "error" in data_schema:
        return jsonify(data_schema), 500
    
    # Annars skicka schema listan med 200 OK
    return jsonify({
        "status": "success",
        "schema": data_schema

    }), 200
    
def skrapa_schema_data():
    # URL till schemat (TimeEdit grafisk vy)
    url = "https://cloud.timeedit.net/hda/web/public/ri1t6fZ7YQb1bnQY53Q9YQtnZ507fX966n5756ny.html"
    
    try:
        # Skapa en 'header' (sidhuvud) som fungerar som en legitimation mot webbservern
        # Vi låtsas vara en vanlig webbläsare (Mozilla) så att servern inte blockerar oss som en robot
        headers = {'User-Agent': 'Mozilla/5.0'}

        # Använd requests-biblioteket för att skicka en förfrågan om att få hämta hemsidan
        # 'url' är adressen, 'headers' är vår legitimation, och 'timeout=10' gör att vi slutar vänta efter 10 sekunder om inget händer
        response = requests.get(url, headers=headers, timeout=10)

        # Skapa ett 'BeautifulSoup-objekt' som fungerar som en översättare av HTML-koden
        # Vi tar innehållet från svaret (response.content) och använder 'html.parser' för att göra koden sökbar och strukturerad
        soup = BeautifulSoup(response.content, 'html.parser')

        #Hitta alla DIV-taggar som har klassen 'bookingDiv' eftersom det identifierar en schemaposition.
        #Där finns i dess title attribut allt data om den schemapositionen tex datum tid, lektiontyp, lärarnan, sal, kurskod etc
        #<div class="bookingDiv fgDiv clickable2 c-1 r669241" title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"></div>
        bokningar_divs = soup.find_all('div', class_='bookingDiv')
        
        #listan kommer att innehålla dicts med alla schema positioner/bokningar
        schema_positioner = []
        
        #loopar all div:ar där schemapostioner/bokningar finns
        for bokning in bokningar_divs:
            # Extrahera strängen från 'title'-attributet i diven
            # Din exempel-div har all info i 'title', t.ex. "2026-01-21 15:00 - 17:00..."
            #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"></div>
            info_strang_title = bokning.get('title', '')
            
            if info_strang_title:
                # Skapar en array/lista baserat på den komma separerade sträng i title
                #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
                detaljer_title_array = info_strang_title .strip().split(',')
                #Anropar hjälp funktioner för att plock rätt delar ur arrayen 
                datumet=get_datum(detaljer_title_array)
                tiden=get_tid(detaljer_title_array)
                kursen=get_kurskod(detaljer_title_array)
                lararen=get_larare(detaljer_title_array)
                lokalen=get_lokal(detaljer_title_array)
                typen=get_typ(detaljer_title_array)
                
                #bygger up dicten för en schema_post
                schema_post = {
                    
                    "datum":  datumet,                    
                    "tid":  tiden,                    
                    "kurs":  kursen,
                    "larare": lararen,                    
                    "lokal":  lokalen,
                    "typ":typen
                }
                #lägger till schema_post dicten på lista av schem_positioner
                schema_positioner.append(schema_post)

        return schema_positioner

    except Exception as e:
        return {"error": str(e)}
    
# --- HJÄLPFUNKTIONER FÖR SCHEMA-DATA ---

def get_datum(title_array):
    """
    Hämtar datumet.
    Strängen ser ut så här: "2026-01-22 10:00 - 12:00"
    Vi vill bara ha den första delen (index 0).
    """
    if len(title_array) > 0:
        #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
        # 1. Ta första delen: "2026-01-22 10:00 - 12:00"
        första_delen = title_array[0].strip()
        # 2. Dela upp den vid mellanslag och plocka ut första ordet
        datum = första_delen.split(" ")[0] # är datumet
        return datum
    
    return "Saknas"

def get_tid(title_array):
    """
    #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
    Hämtar start- och sluttid.
    Vi splittar "2026-01-22 10:00 - 12:00" vid varje mellanslag.
    Då hamnar tiderna på index 1 och 3.
    """
    if len(title_array) > 0:
        tids_delar = title_array[0].strip().split(" ")
        
        # Vi kollar att det finns minst 4 delar så att koden inte kraschar
        if len(tids_delar) >= 4:
            start_tid = tids_delar[1]
            slut_tid = tids_delar[3]
            return f"{start_tid} - {slut_tid}"
            
    return "Saknas"

def get_kurskod(title_array):
    """
    #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
    Kurskoden alltid på index 1 listan.
    """
    if len(title_array) > 1:
        return title_array[1].strip() # kurskoden "GMI35S_V3NJJ"
    
    return "Saknas"

def get_larare(title_array):
    """
    #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
    Lärare är klurigt. i normfallet ligger lärarens namn på index 3, men om det fins grupp nummer så liiger det på index 3 
    och läraren läggs på annan index position och den är rre från sluter dvs -3   
    """
    if len(title_array) < 4:
        return "Saknas"

    # Hämta det lärarens namn på den normal index positionen dvs 3
    larar_namn = title_array[3].strip()

    # Om ordet 'grupp' finns i texten, så är det inte läraren vi hittat.
    # Då hämatr i bakifrån: dvs på index -3 är ofta lärarens plats i dessa fall.
    if "grupp" in  larar_namn .lower():
        return title_array[-3].strip()# läser bakifrån i arrayen och då ligger lärern på  index -3
    
    return  larar_namn 

def get_lokal(title_array):
    """
    #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
    Lokalen står sist i strängen, t.ex: "Samtal298 (zoom) ID 669241"
    Vi vill bara ha det första ordet i den sista delen.
    """
    if len(title_array) > 0:
        sista_delen = title_array[-1].strip()
        # Dela sista delen vid mellanslag och ta första ordet
        lokal = sista_delen.split(" ")[0] # Samtal298
        return lokal
    
    return "Saknas"

def get_typ(title_array):
    """
    #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
    Lektionstyp (t.ex. Föreläsning eller Handledning).
    Erfarenheten visar att den ligger på inndex -4 från slutet i listan.
    """
    if len(title_array) >= 4:
        return title_array[-4].strip() # Handledning
    
    return "Saknas"