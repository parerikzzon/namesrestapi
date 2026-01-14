from flask import Blueprint, jsonify
import re
regex_bp = Blueprint('regex_bp', __name__)

"""
Här är en sammanställning där förklaring, Python-kod och resultat är samlade för varje exempel. Detta är  perfekt för att snabbt komma igång med `re`-modulen i Python.

---

### 1. `\d` (Siffra)

Matchar en enstaka siffra mellan 0 och 9.

```python
import re
text = "Agent 007"
# Söker efter tre siffror i rad
match = re.search(r"\d\d\d", text)
print(match.group())  # Resultat: 007

```

### 2. `+` (En eller flera)

Används efter ett tecken för att matcha det en eller flera gånger i rad.

```python

text = "Användare12345 loggade in"
# Söker efter alla siffror som sitter ihop
match = re.search(r"\d+", text)
print(match.group())  # Resultat: 12345

```

### 3. `{}` (Kvantifierare)

Anger exakt hur många gånger föregående tecken ska upprepas.

```python

text = "Felkod: 5542"
# Söker efter exakt 4 siffror
match = re.search(r"\d{4}", text)
print(match.group())  # Resultat: 5542

```

### 4. `[]` (Teckenuppsättning)

Matchar ett (och endast ett) av tecknen inuti klamrarna.
```python

text = "bild.png"
# Matchar antingen 'p' eller 'j' följt av 'ng'
match = re.search(r"[pj]ng", text)
print(match.group())  # Resultat: png

```

### 5. `.` (Punkt / Joker)

Matchar vilket tecken som helst utom radbrytning.

```python

text = "admin, admon, adm1n"
# Punkten matchar 'i', 'o' och '1'
matches = re.findall(r"adm.n", text)
print(matches)  # Resultat: ['admin', 'admon', 'adm1n']

```

### 6. `\b` (Ordbegränsning)

Säkerställer att matchningen börjar och slutar som ett eget ord (förhindrar träffar inuti andra ord).

```python

text = "bil, lastbil, bilat"
# Hittar bara ordet 'bil', inte där det är en del av ett längre ord
matches = re.findall(r"\bbil\b", text)
print(matches)  # Resultat: ['bil']

```

### 7. `^` (Början av sträng)

Tvingar mönstret att matcha endast om det finns i början av strängen eller raden.

```python

text = "START: Systemet körs"
# Matchar bara om 'START' står först
match = re.search(r"^START", text)
if match:
    print(match.group())  # Resultat: START

```

### 8. `()` (Gruppering)

Används för att "fånga in" en specifik del av en matchning så att man kan hämta ut den separat.

```python

text = "IP: 192.168.1.1"
# Vi matchar hela 'IP: ...' men sparar bara siffrorna i en grupp ()
match = re.search(r"IP: (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", text)
if match:
    print(match.group(1))  # Resultat: 192.168.1.1 (endast det i parentesen)

```

---

### Hur man kombinerar dessa

Inom IT-säkerhet kombinerar man ofta dessa. Till exempel:
`^` + `\d{4}` + `-` + `\d{2}` skulle matcha ett datum som står först på en rad i en loggfil.

**Vill du att vi testar att bygga ett "kombinations-uttryck" för att hitta något mer komplext, som t.ex. ett specifikt felmeddelande i en serverlogg?**

"""


# http://127.0.0.1:5000/regex/?api_key=abcd
@regex_bp.route('/')
def get_regex_tutorial():
    # En lista med pedagogiska objekt
    examples = [
        
        {
            "id": "pris",
            "label": "Pris-extraktion",
            "text": "Medlemskap kostar 299 kr och frakt 49 kr.",
            "pattern": r"(\d+)\s?kr",
            "desc": "(\\d+): fångar en eller flera siffror. \\s?: valfritt mellanslag. kr: letar efter exakta tecken."
        },
        {
            "id": "email",
            "label": "E-post",
            "text": "Maila support@test.se",
            "pattern": r"[\w\.-]+@[\w\.-]+\.\w+",
            "desc": "[\\w\\.-]+: bokstäver/siffror/punkt före @. @: matchar symbolen. \\w+: domännamn. \\.\\w+: punkt följt av toppdomän."
        },
        {
            "id": "url_simple",
            "label": "Webbadresser (URL)",
            "text": "Besök https://www.google.com för info.",
            "pattern": r"https?://[\w\.-]+",
            "desc": "http: exakta tecken. s?: gör 's' valfritt (matchar http/https). ://: matchar snedstrecken. [\\w\\.-]+: matchar domänen."
        },
        {
            "id": "named_groups",
            "label": "Namngivna Grupper",
            "text": "Användare: Johan, ID: 4502",
            "pattern": r"Användare: (?P<namn>\w+), ID: (?P<id>\d+)",
            "desc": "(?P<namn>\\w+): fångar ord och sparar det under nyckeln 'namn'. \\d+: fångar siffror till nyckeln 'id'."
        },
        {
            "id": "whitespace_cleanup",
            "label": "Städa mellanslag",
            "text": "Detta    är  smutsigt.",
            "pattern": r"\s{2,}",
            "desc": "\\s: matchar mellanrum (space/tab). {2,}: betyder 'två eller fler gånger i rad'."
        },
        {
            "id": "date_iso",
            "label": "Datum (ISO)",
            "text": "Deadline är 2024-12-24.",
            "pattern": r"(\d{4})-(\d{2})-(\d{2})",
            "desc": "(\\d{4}): fångar 4 siffror (år). -: matchar bindestreck. (\\d{2}): fångar 2 siffror (månad/dag)."
        },
        {
            "id": "word_boundaries",
            "label": "Exakta ord",
            "text": "En bil körde förbi, bilen var blå.",
            "pattern": r"\bbil\b",
            "desc": "\\b: ordgräns. Ser till att mönstret inte matchar om 'bil' är en del av ett längre ord som 'bilen'."
        },
        {
            "id": "ip_address",
            "label": "IP-adresser (IPv4)",
            "text": "IP: 192.168.1.1",
            "pattern": r"(?:\d{1,3}\.){3}\d{1,3}",
            "desc": "(?:\\d{1,3}\\.){3}: repeterar 1-3 siffror + punkt tre gånger. \\d{1,3}: den sista siffergruppen."
        },
        {
            "id": "html_tags",
            "label": "HTML-taggar",
            "text": "Visa <b>fet</b> text.",
            "pattern": r"<[^>]*>",
            "desc": "<: början på tagg. [^>]*: matchar allt som INTE är en slutparentes. >: stänger taggen."
        },
        {
            "id": "swedish_pnr",
            "label": "Personnummer",
            "text": "Nummer: 850512-1234",
            "pattern": r"\d{6}[-+]?\d{4}",
            "desc": "\\d{6}: de första 6 siffrorna. [-+]?: valfritt minus eller plus. \\d{4}: de sista 4 siffrorna."
        }
    
    ]

    lessons = []

    # 1. Vi går igenom varje lektion/exempel i vår lista
    for ex in examples:
        matches = [] # Här sparar vi alla träffar vi hittar i just DENNA text
        
        # 2. re.finditer letar upp ALLA ställen där mönstret matchar texten.
        # Det skapar ett "match-objekt" för varje träff som vi kan ställa frågor till.
        for match in re.finditer(ex["pattern"], ex["text"]):
            
            # 3. Vi skapar en egen "ordlista" (dictionary) för att spara informationen 
            # på ett sätt som är lätt för t.ex. en hemsida eller JSON att förstå.
            match_obj = {
                # .group(0) returnerar hela den textsträng som fastnade i regex-fällan.
                "full_match": match.group(0),
                
                # .start() och .end() ger oss exakta positioner (index) där matching startade resp slutade. 
                # Det behövs för att t.ex. kunna stryka under eller färglägga texten.
                "indices": [match.start(), match.end()],
                
                # .groups() hämtar allt som hamnat inom (parenteser).
                # Om vi har flera parenteser får vi en lista med varje del för sig.
                "groups": match.groups() # en tuple data struktur skpas och returnar av groups
            }
            
            # 4. Lägg till träffen i vår lista för detta exempel
            matches.append(match_obj)

        lessons.append({
            "lesson_title": ex["label"],
            "source_text": ex["text"],
            "regex_used": ex["pattern"],
            "explanation": ex["desc"],
            "results": matches
        })

    return jsonify({
        "course": "Python Regex 101",
        "lessons": lessons
    })