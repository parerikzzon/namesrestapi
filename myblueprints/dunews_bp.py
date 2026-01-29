#i öppna cmd skriv: python -m pip install beautifulsoup4
#python -m pip install requests
from flask import Blueprint, jsonify
from bs4 import BeautifulSoup
import requests
from datetime import datetime #för dagensdatum och tid

dunews_bp = Blueprint('dunews_bp', __name__)

BASE_URL = "https://www.du.se"
HEADERS = {'User-Agent': 'Mozilla/5.0'}
# http://127.0.0.1:5000/dunews/?api_key=abcd
@dunews_bp.route('/')
def get_live_news():
    try:
        #anroper egen hjälp funktion
        news = scrape_du_news()
        
        return jsonify({
            "source": "Högskolan Dalarna",
            "count": len(news),
            "articles": news,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M") # Formatera enligt format: ÅÅÅÅ-MM-DD TT:MM
        }),200
    ## Om hemsidan tar för lång tid på sig att svara
    except requests.exceptions.Timeout:
        return jsonify({"error": "Timeout: du.se svarade för långsamt"}), 504 # Gateway Timeout
    # Om något annat oväntat fel uppstår (fångar alla andra fel)
    except Exception as e:
        return jsonify({"error": f"Internt serverfel: {e}"}), 500 # Internal Server Error

#--------Helper functions-------
def scrape_du_news():
    # requests.get skickar en förfrågan till hemsidan och sparar hela svaret i 'response'
    response = requests.get(BASE_URL, headers=HEADERS)
    # raise_for_status() kollar om vi fick ett felmeddelande från hemsidan (t.ex. 404)
    # Om något gick fel hoppar koden direkt ner till 'except'-blocket.
    response.raise_for_status() # Kolla om anropet gick bra
    # 2. Skapa soppan (parse HTML)
    # Vi matar in texten från hemsidan och talar om att det är HTML.
    # Nu kan Python "förstå" strukturen på sidan.
    soup = BeautifulSoup(response.text, 'html.parser')
    # Skapa en tom lista där vi ska spara våra hittade nyheter som små paket (dictionaries)
    news_items = []

    # 3. Hitta alla article-taggar som är nyhetskort
    # find_all letar efter alla <article>-taggar som har CSS-klassen 'news-card'
    articles = soup.find_all('article', class_='news-card')
    ## Vi loopar igenom varje artikel vi hittade
    for article in articles:
        # Hitta titeln och länken inuti div:en vars calss är "du-title"
        title_container = article.find('div', class_='du-title')
        # Kontrollera att behållaren faktiskt finns innan vi går vidare (viktigt!)
        if title_container:
            link_tag = title_container.find('a')
            if link_tag:
                # .get_text(strip=True) hämtar texten i länken och tar bort fula mellanslag
                text = link_tag.get_text(strip=True)
                # .get('href') hämtar själva webbadressen som länken pekar på
                href = link_tag.get('href')
                
                # Bygg ihop den fullständiga länken om den är relativ dvs lägg till prefixet
                # Webbplatser använder ofta "relativa länkar" (t.ex. /sv/om-oss/nytt-och-aktuellt/)
                # Här kollar vi om länken börjar med '/' och lägger till domänen i så fall.(https://www.du.se)
                #så att de blir(https://www.du.se/sv/om-oss/nytt-och-aktuellt/......)
                if href.startswith('/'):
                    href = f"https://www.du.se{href}"
                # Spara nyheten i vår lista som ett dictionary objekt
                news_items.append({
                    "title": text,
                    "url": href
                })
    return news_items


