import csv
import re
import html
from pathlib import Path

INPUT_PATH = Path("input.txt")
OUTPUT_PATH = Path("output.tsv")

TAG_RE = re.compile(r"<[^>]+>")

def strip_html(s: str) -> str:
    if s is None:
        return ""
    s = html.unescape(s)
    s = s.replace("\u00a0", " ")          # non-breaking space
    s = TAG_RE.sub("", s)                 # remove tags
    s = re.sub(r"\s+", " ", s).strip()    # normalize whitespace
    return s

raw = INPUT_PATH.read_text(encoding="utf-8", errors="replace")

# Läs som tab-separerad "CSV" med citattecken runt fält som kan innehålla \n
rows = []
reader = csv.reader(raw.splitlines(True), delimiter="\t", quotechar='"')
for row in reader:
    if not row:
        continue
    rows.append(row)

# Förväntad struktur (0-baserade index):
# 0 Name
# 1 Q1_answer, 4 Q1_id
# 6 Q2_answer, 9 Q2_id
# 11 Q3_answer, 14 Q3_id
# 16 Q4_answer, 19 Q4_id
# 21 Q5_answer, 24 Q5_id
# 26 Q5_choice_value (Yes/No) när Q5 är "choice"
out = []
header = ["Namn", "Svar_1", "Svar_2", "Svar_3", "Svar_4", "Svar_5", "Choice_YesNo"]
out.append(header)

for r in rows:
    # Hoppa över trasiga/korta rader
    if len(r) < 2:
        continue

    name = r[0].strip()

    # Försök extrahera de fem svaren enligt din exportlayout
    def safe_get(idx: int) -> str:
        return r[idx] if idx < len(r) else ""

    ans1 = strip_html(safe_get(1))
    ans2 = strip_html(safe_get(6))
    ans3 = strip_html(safe_get(11))
    ans4 = strip_html(safe_get(16))
    ans5 = strip_html(safe_get(21))

    choice = strip_html(safe_get(26))

    # Om raden inte verkar vara en "studentrad" (t.ex. tomt namn), hoppa
    if not name:
        continue

    out.append([name, ans1, ans2, ans3, ans4, ans5, choice])

# Skriv TSV för Excel
with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_MINIMAL)
    w.writerows(out)

print(f"Klart: skrev {len(out)-1} rader till {OUTPUT_PATH}")
