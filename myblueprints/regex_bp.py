from flask import Flask, Blueprint, request, jsonify
import re # för att kunna skriv regex

#Vi skapar en ny Blueprint för regex
regex_bp = Blueprint('reg_bp', __name__)

# --- Några vanliga regex ---
PATTERNS = {
    # --- VARDAGLIG VALIDERING / IDENTITETER ---

    # E-POST
    # Exempel: "nisse.svensson@gmail.com", "info@foretag.se"
    # [a-zA-Z0-9._%+-]+  -> lokaldel: bokstäver, siffror och vissa symboler, en eller flera gånger
    # @                  -> bokstavligt snabel-a
    # [a-zA-Z0-9.-]+     -> domännamn (ex: gmail, foretag.se)
    # \.[a-zA-Z]{2,}     -> punkt + toppdomän med minst 2 bokstäver (.se, .com, .org...)
    #
    # Forensik/hot: Kan användas för att hitta kontakter, offer/förövare, phishing-avsändare
    # i loggar, e-postdump och chatt-export.
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',

    # SVENSKT POSTNUMMER
    # Exempel: "123 45" eller "54321"
    # \d{3}  -> exakt tre siffror
    # \s?    -> valfritt mellanslag
    # \d{2}  -> exakt två siffror
    #
    # Forensik/hot: Kan peka på svensk adress, t.ex. i beställningsunderlag, leveransdata,
    # eller läckta kundregister.
    "swe_postnummer": r'\d{3}\s?\d{2}',

    # SVENSKT MOBILNUMMER
    # Exempel: "070-1234567", "0731234567", "076 1234567"
    # 07[02369] -> börjar på 07 följt av ett giltigt mobilprefix
    # \s?-?     -> valfritt mellanslag ELLER bindestreck
    # \d{7}     -> exakt sju siffror
    #
    # Forensik/hot: Hjälper till att identifiera telefonnummer i phishing-SMS, WhatsApp-loggar
    # eller läckta kontaktlistor som angripare använt.
    "swe_mobile": r'07[02369]\s?-?\d{7}',

    # HTML-LÄNKAR
    # Exempel: href="https://google.com" (fångar det inuti citattecknen)
    # href="      -> letar efter den exakta textsträngen
    # ([^"]*)     -> grupp: alla tecken som INTE är " (noll eller fler)
    #
    # Forensik/hot: Kan plocka ut alla länkar i HTML-mail eller webbsidor,
    # t.ex. skadliga URL:er i phishingkampanjer eller exploit-sidor.
    "html_links": r'href="([^"]*)"',

    # --- IT-FORENSIK: NÄTVERK & IDENTIFIERING ---

    # IPv4-ADRESS (förenklad, validerar inte 0–255)
    # Exempel: "192.168.1.1", "8.8.8.8", "10.0.0.254"
    # \b                 -> word boundary, så vi inte fångar "123.4.5.6abc"
    # (?:[0-9]{1,3}\.){3} -> tre grupper med 1–3 siffror + punkt
    # [0-9]{1,3}         -> sista oktetten
    #
    # Forensik/hot: Används för att extrahera käll- och destinations-IP från loggar
    # (t.ex. C2-servrar, skadliga IP:n, intern laterala rörelser).
    "ipv4": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',

    # IPv6-ADRESS (förenklad utan alla komprimeringsvarianter)
    # Exempel: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    # (?:[0-9a-fA-F]{1,4}:){7} -> sju grupper av 1–4 hextecken + kolon
    # [0-9a-fA-F]{1,4}         -> sista gruppen
    #
    # Forensik/hot: Hjälper till att hitta IPv6-källor i moderna loggar,
    # t.ex. angripare som gömmer sig bakom IPv6-adresser.
    "ipv6": r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',

    # MAC-ADRESS
    # Exempel: "00:1A:2B:3C:4D:5E" eller "00-1A-2B-3C-4D-5E"
    # (?:[0-9a-fA-F]{2}[:-]){5} -> fem grupper av två hextecken + kolon/bindestreck
    # [0-9a-fA-F]{2}            -> sista paret
    #
    # Forensik/hot: Kan användas för att binda aktivitet till specifik nätverksadapter/enhet
    # (t.ex. en angripares laptop eller IoT-enhet).
    "mac_address": r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}',

    # --- IT-FORENSIK: FILANALYS & MALWARE ---

    # WINDOWS FILVÄG
    # Exempel: "C:\Windows\System32\drivers\etc\hosts", "D:\Bilder\foto.jpg"
    # [a-zA-Z]:\\          -> enhetsbokstav + kolon + backslash
    # (?:[^\\\/:*?"<>|\r\n]+\\)* -> mappar: alla tillåtna tecken + \, upprepat
    # [^\\\/:*?"<>|\r\n]*  -> sista fil- eller katalognamnet (kan vara tomt)
    #
    # Forensik/hot: Hitta var skadlig kod lagras/körs, t.ex. "C:\Users\...\payload.exe".
    "windows_path": r'[a-zA-Z]:\\(?:[^\\\/:*?"<>|\r\n]+\\)*[^\\\/:*?"<>|\r\n]*',

    # LINUX FILVÄG
    # Exempel: "/var/log/auth.log", "/etc/shadow", "/home/user/.bashrc"
    # /                    -> börjar med root
    # (?:[\w.-]+/)+        -> en eller flera mappar (bokstäver/siffror/._- + /)
    # [\w.-]+              -> filnamn
    #
    # Forensik/hot: Hitta intressanta filer i loggar/rapporter, som /etc/shadow,
    # loggar angripare rört eller nya binärer i /usr/local/bin.
    "linux_path": r'/(?:[\w.-]+/)+[\w.-]+',

    # MD5 HASH
    # Exempel: "5d41402abc4b2a76b9719d911017c592" (32 hextecken)
    # \b[0-9a-fA-F]{32}\b -> exakt 32 hextecken, avgränsat av word boundaries
    #
    # Forensik/hot: används för att identifiera filer via hash (malware-signaturer,
    # IOC-listor(Indicators of Compromise (på svenska: indikatorer på intrång)), jämförelse mot threat intel).
    "md5_hash": r'\b[0-9a-fA-F]{32}\b',

    # SHA256 HASH
    # Exempel: "e3b0c4...b855" (64 hextecken)
    # \b[0-9a-fA-F]{64}\b -> exakt 64 hextecken
    #
    # Forensik/hot: samma användning som MD5 men modernare, används i många
    # malware- och IOC-databaser.
    "sha256_hash": r'\b[0-9a-fA-F]{64}\b',

    # --- IT-FORENSIK: SÅRBARHETER & KOD ---

    # CVE-ID (Common Vulnerabilities and Exposures)
    # Exempel: "CVE-2021-44228", "CVE-2023-1234"
    # CVE-         -> fast prefix
    # \d{4}        -> årtal
    # -\d{4,7}     -> ett bindestreck + 4–7 siffror (ID)
    #
    # Forensik/hot: hitta vilka sårbarheter som nämns i loggar, rapporter och exp


}

@regex_bp.route('/', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'content' not in data:
        return jsonify({"error": "Skicka JSON med fältet 'content'"}), 400
    
    text = data['content']
    results = {}

    for name, pattern in PATTERNS.items():
        matches = re.findall(pattern, text)
        
        # Hantera om regexet har grupper (t.ex. html_links)
        if matches and isinstance(matches[0], tuple):
            matches = [m[0] for m in matches]
            
        # Ta bort dubbletter och spara
        results[name] = list(set(matches))

    return jsonify({
        "status": "success",
        "analysis": results
    })

"""
test json i thunder client via POST och i body
{
  "content": "ANALYSRAPPORT 2024-05-20\n--------------------------\nAnvändare: nisse.it-forensik@bolaget.se (Mobil: 070-1234567, Postnr: 123 45)\nSystem: Windows 11 på enhet C:\\\\Users\\\\Admin\\\\Downloads\\\\payload.exe\nNätverk: IPv4: 192.168.1.50, IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334, MAC: 00:1A:2B:3C:4D:5E\nLinux-spår: Hittade filer i /var/log/syslog och /etc/shadow\nHasher: MD5: 85202888629f635f3d3d6396f9a65d78, SHA256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855\nSårbarhet: Detekterade försök mot CVE-2021-44228 via <a href=\"https://skadlig-sida.ru/exploit\">Klicka här</a>\nKod: Base64-sträng funnen: SGVsbG8gV29ybGQgdGhpcyBpcyBhIGJhc2U2NCB0ZXN0IHN0cmluZy4=\nSSH: ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC0testkey"
}
"""