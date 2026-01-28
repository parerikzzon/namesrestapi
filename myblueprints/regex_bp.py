from flask import Flask, Blueprint, request, jsonify
import re # för att kunna skriv regex

#Vi skapar en ny Blueprint för regex
regex_bp = Blueprint('reg_bp', __name__)

# --- Några vanliga regex ---
PATTERNS = {
    
    # --- VARDAGLIG VALIDERING ---
    # Exempel: "nisse.svensson@gmail.com", "info@foretag.se"
    # E-POST
    # [a-z0-9._%+-]+ -> Matcha bokstäver/siffror/tecken EN eller FLERA gånger (+)
    # @ -> Letar efter ett bokstavligt @-tecken
    # \.[a-z]{2,} -> Letar efter en punkt (\.) följt av minst 2 bokstäver ({2,})
    # [a-z0-9._%+-]+ -> Matcha bokstäver/siffror/tecken EN eller FLERA gånger (+)
    # @ -> Letar efter ett bokstavligt @-tecken
    # \.[a-z]{2,} -> Letar efter en punkt (\.) följt av minst 2 bokstäver ({2,})
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',

    # Exempel: "123 45" eller "54321"
    # SVENSKT POSTNUMMER
    # \d{3} -> Exakt tre siffror (\d)
    # \s? -> Ett valfritt (?) mellanslag (\s)
    # \d{2} -> Exakt två siffror till
    "swe_postnummer": r'\d{3}\s?\d{2}',

    # Exempel: "070-1234567", "0731234567", "076 1234567"
    # SVENSKT MOBILNUMMER
    # 07[02369] -> Börjar på 07 följt av någon av siffrorna i haken []
    # \s?-? -> Tillåter valfritt mellanslag ELLER bindestreck
    "swe_mobile": r'07[02369]\s?-?\d{7}',

    # Exempel: href="https://google.com" (fångar det inuti citattecknen)
    # HTML-LÄNKAR
    # href=" -> Letar efter den exakta textsträngen
    # ([^"]*) -> Parenteser skapar en GRUPP. ^" betyder "allt utom citattecken". * betyder noll eller flera.
    "html_links": r'href="([^"]*)"',
    
    # --- IT-FORENSIK: NÄTVERK & IDENTIFIERING ---
    # Exempel: "192.168.1.1", "8.8.8.8", "10.0.0.254"
    # IPv4-ADRESS
    # \b -> Word boundary: ser till att IP:n inte är en del av ett längre ord
    # (?:[0-9]{1,3}\.){3} -> Repeterar gruppen (1-3 siffror + punkt) exakt 3 gånger
    "ipv4": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',

    # Exempel: "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    # IPv6-ADRESS
    # [0-9a-fA-F]{1,4} -> Matcha 1 till 4 hexadecimala tecken
    # : -> Letar efter bokstavliga kolon som separerar grupperna
    "ipv6": r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',

    # Exempel: "00:1A:2B:3C:4D:5E" eller "00-1A-2B-3C-4D-5E"
    # MAC-ADRESS
    # [0-9a-fA-F]{2} -> Två hex-tecken (t.ex. 4A)
    # [:-] -> Matcha antingen kolon ELLER bindestreck som separator
    "mac_address": r'(?:[0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}',
    
    # --- IT-FORENSIK: FILANALYS & MALWARE ---
    # Exempel: "C:\Windows\System32\drivers\etc\hosts", "D:\Bilder\foto.jpg"
    # WINDOWS FILVÄG
    # [a-zA-Z]:\\ -> Enhetsbokstav följt av kolon och ett bokstavligt backslash (dubbelt \\ behövs i kod)
    # [^\\\/:*?"<>|\r\n]+ -> Matcha alla tecken som INTE är förbjudna i filnamn
    "windows_path": r'[a-zA-Z]:\\(?:[^\\\/:*?"<>|\r\n]+\\)*[^\\\/:*?"<>|\r\n]*',

    # Exempel: "/var/log/auth.log", "/etc/shadow", "/home/user/.bashrc"
    # LINUX FILVÄG
    # / -> Måste börja med ett framåtlutat snedstreck
    # (?:[\w.-]+/)+ -> Matcha mappar (bokstäver/siffror/punkt/streck + /) EN eller FLERA gånger
    "linux_path": r'/(?:[\w.-]+/)+[\w.-]+',

    # Exempel: "5d41402abc4b2a76b9719d911017c592" (32 tecken långt fingeravtryck)
    # MD5 HASH
    # \b...\b -> Boundary: Säkerställer att vi hittar EXAKT 32 tecken, inte 32 tecken inuti något annat
    "md5_hash": r'\b[0-9a-fA-F]{32}\b',

    # Exempel: "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855" (64 tecken)
    # SHA256 HASH
    # {64} -> Letar efter exakt 64 hexadecimala tecken i följd
    "sha256_hash": r'\b[0-9a-fA-F]{64}\b',
    
    # --- IT-FORENSIK: SÅRBARHETER & KOD ---
    # Exempel: "CVE-2021-44228", "CVE-2023-1234"
    # CVE-ID (Common Vulnerabilities and Exposures)
    # CVE- -> Den fasta texten "CVE-"
    # \d{4} -> Årtalet (4 siffror)
    # -\d{4,7} -> Ett bindestreck följt av mellan 4 och 7 siffror (ID-numret)
    "cve_id": r'CVE-\d{4}-\d{4,7}',

    # Exempel: "SGVsbG8gV29ybGQgdGhpcyBpcyBhIGJhc2U2NCB0ZXN0IHN0cmluZy4=" (Kodad data)
    # BASE64-BLOB
    # [A-Za-z0-9+/]{40,} -> Letar efter Base64-alfabetet som är minst 40 tecken långt ({40,})
    # =* -> Letar efter noll eller flera padding-tecken (=) i slutet
    "base64_blob": r'[A-Za-z0-9+/]{40,}=*',

    # Exempel: "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC..." (En publik krypteringsnyckel)
    # SSH PUBLIC KEY
    # ssh-rsa -> Den fasta strängen som definierar nyckeltypen
    # AAAA -> SSH-nycklar börjar nästan alltid med fyra stycken A
    "ssh_key": r'ssh-rsa AAAA[0-9A-Za-z+/]+[=]{0,3}'

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