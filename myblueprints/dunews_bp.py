#i öppna cmd skriv: python -m pip install beautifulsoup4
#python -m pip install requests
from flask import Blueprint, jsonify
from bs4 import BeautifulSoup
import requests

dunews_bp = Blueprint('dunews_bp', __name__)
# http://127.0.0.1:5000/dunews/?api_key=abcd
@dunews_bp.route('/')
def get_live_news():
    #skrapa du nyheter
    url = "https://www.du.se"
    
    try:
        # 1. Hämta HTML från du.se
        # Vi lägger till en 'user-agent' för att se ut som en vanlig webbläsare
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Kolla om anropet gick bra

        # 2. Skapa soppan (parse HTML)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        news_items = []

        # 3. Hitta alla article-taggar som är nyhetskort
        articles = soup.find_all('article', class_='news-card')

        for article in articles:
            # Hitta titeln och länken inuti div:en "du-title"
            title_container = article.find('div', class_='du-title')
            
            if title_container:
                link_tag = title_container.find('a')
                if link_tag:
                    text = link_tag.get_text(strip=True)
                    href = link_tag.get('href')
                    
                    # Bygg ihop den fullständiga länken om den är relativ dvs lägg till prefixet
                    if href.startswith('/'):
                        href = f"https://www.du.se{href}"
                    
                    news_items.append({
                        "title": text,
                        "url": href
                    })

        return jsonify({
            "source": "Högskolan Dalarna",
            "count": len(news_items),
            "articles": news_items
        })

    except Exception as e:
        return jsonify({"error": f"Kunde inte hämta nyheter: {str(e)}"}), 500