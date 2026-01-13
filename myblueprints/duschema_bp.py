from flask import Blueprint, jsonify
import requests
from bs4 import BeautifulSoup

duschema_bp = Blueprint('duschema_bp', __name__)

#http://127.0.0.1:5000/duschema/?api_key=abcd
@duschema_bp.route('/')
def get_schema():
    data_schema = skrapa_schema_data()
    #return data
    # Om data är en ordlista med nyckeln "error", skicka 500-kod
    if isinstance(data_schema, dict) and "error" in data_schema:
        return jsonify(data_schema), 500
    
    # Annars skicka schemalistan med 200 OK
    return jsonify({
        "status": "success",
        "schema": data_schema

    }), 200
    
def skrapa_schema_data():
    # URL till schemat (TimeEdit grafisk vy)
    url = "https://cloud.timeedit.net/hda/web/public/ri1t6fZ7YQb1bnQY53Q9YQtnZ507fX966n5756ny.html"
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Hitta alla DIV-taggar som har klassen 'bookingDiv'
        # Vi letar efter 'bookingDiv' eftersom det identifierar en schemapost
        bokningar = soup.find_all('div', class_='bookingDiv')
        
        parsed_results = []
        #loopar all div:ar där schema bokningar finns
        for bokning in bokningar:
            # 2. Extrahera information från 'title'-attributet i diven
            # Din exempel-div har all info i 'title', t.ex. "2026-01-21 15:00 - 17:00..."
            #<div class="bookingDiv fgDiv clickable2 c-1 r669241" title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"></div>
            info_strang = bokning.get('title', '')
            
            if info_strang:
                # Delar upp info_strang "title" strängen separerad med kommatecken
                #title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika Artursson Wissa, Internet, Samtal298 (zoom) ID 669241"
                detaljer_title = info_strang.strip().split(',')
                # 1. Hämta värden från index positionen 3 där lärarens namn är i normal fall ligger
                val3 = detaljer_title[3].strip() if len(detaljer_title) > 3 else "" #lärare ligger på index 3 i normal fall      
                

                # 2. Men ibland ligger tex gruppnummer där lärararens namn normalt ligger på index 3 och 
                # då måste vi läsa bakifrån:
                # Om index 3 innehåller "Grupp/grupp" dvsinte läaren namn, 
                if "grupp" in val3.lower():
                    #då ligger inte lärararens namn på index 3 så börja läsbakifrån och finner att läraren då ligger på index -3
                    larare = detaljer_title[-3].strip() # kolla att den ligger på -3 indexposition bakifrån räknat i arrayen
                else:
                    #det fanns inte orddet Grupp så lärarens namn ligger på sin normal index position 3 i arrayen(framifrån)
                    larare = val3

                post = {
                    #plockar ut datum från "2026-01-19 15:00 - 17:00 H3LLJ_DITMG" ligger på index 0
                    "datum":  detaljer_title[0].strip().split(" ")[0] if len( detaljer_title) > 0 else "Saknas",
                    #plockar ut tid från "2026-01-19 15:00 - 17:00 H3LLJ_DITMG" ligger på index 1 resp 3
                    "tid":  detaljer_title[0].strip().split(" ")[1] + " - " +  detaljer_title[0].strip().split(" ")[3]  if len( detaljer_title) > 0 else "Saknas",
                    #plockar ut kurskod från title=" 2026-01-22 10:00 - 12:00 H3LLJ_DITMG, GMI35S_V3NJJ, Handledning, Ulrika A...... ligger på index 1
                    "kurs":  detaljer_title[1].strip() if len( detaljer_title) > 1 else "Saknas",
                    "larare": larare,
                    #plockar ut lokal från title börjar bakifrån B214 Lärosal/ALC ID 676220
                    "lokal":  detaljer_title[-1].strip().split(" ")[0] if len( detaljer_title) > 0 else "Saknas" ,
                    "typ":detaljer_title[-4].strip() if len( detaljer_title) > 0 else "Saknas" # läs bakifrån då ligger den på index -4
                }
                parsed_results.append(post)

        return parsed_results

    except Exception as e:
        return {"error": str(e)}