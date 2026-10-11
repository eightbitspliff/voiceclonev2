"""Deutsche Textaufbereitung für die Sprachausgabe.

TTS-Modelle sprechen Ziffern, Abkürzungen und Symbole im Deutschen oft falsch aus
(„z. B.“ als „zett be“, „3,5 %“ englisch oder gar nicht, „11.10.2026“ als Ziffernfolge).
Dieses Modul schreibt solche Stellen vorher aus – unabhängig vom Sprachmodell.
"""

from __future__ import annotations

import re

try:
    from num2words import num2words as _n2w
except Exception:  # Paket fehlt -> Zahlen bleiben stehen
    _n2w = None

MONTHS = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August",
          "September", "Oktober", "November", "Dezember"]
_MONTH_RE = "|".join(MONTHS + ["Jan", "Feb", "Mär", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Okt", "Nov", "Dez"])

# Abkürzungen (mit und ohne Leerzeichen nach dem Punkt)
ABBREVIATIONS = [
    (r"z\.\s?B\.", "zum Beispiel"), (r"d\.\s?h\.", "das heißt"), (r"u\.\s?a\.", "unter anderem"),
    (r"o\.\s?Ä\.", "oder Ähnliches"), (r"u\.\s?U\.", "unter Umständen"), (r"i\.\s?d\.\s?R\.", "in der Regel"),
    (r"z\.\s?T\.", "zum Teil"), (r"s\.\s?o\.", "siehe oben"), (r"s\.\s?u\.", "siehe unten"),
    (r"v\.\s?a\.", "vor allem"), (r"m\.\s?E\.", "meines Erachtens"), (r"o\.\s?g\.", "oben genannt"),
    (r"u\.\s?v\.\s?m\.", "und vieles mehr"), (r"usw\.", "und so weiter"), (r"usf\.", "und so fort"),
    (r"bzw\.", "beziehungsweise"), (r"ca\.", "circa"), (r"evtl\.", "eventuell"), (r"ggf\.", "gegebenenfalls"),
    (r"inkl\.", "inklusive"), (r"exkl\.", "exklusive"), (r"zzgl\.", "zuzüglich"), (r"vgl\.", "vergleiche"),
    (r"etc\.", "et cetera"), (r"bspw\.", "beispielsweise"), (r"sog\.", "sogenannte"), (r"insb\.", "insbesondere"),
    (r"allg\.", "allgemein"), (r"Nr\.", "Nummer"), (r"Tel\.", "Telefon"), (r"Str\.", "Straße"),
    (r"St\.(?=\s?[A-ZÄÖÜ])", "Sankt"), (r"Dr\.", "Doktor"), (r"Prof\.", "Professor"), (r"Hr\.", "Herr"), (r"Fr\.", "Frau"),
    (r"Mio\.", "Millionen"), (r"Mrd\.", "Milliarden"), (r"Tsd\.", "Tausend"), (r"Std\.", "Stunden"),
    (r"Min\.", "Minuten"), (r"Sek\.", "Sekunden"), (r"max\.", "maximal"), (r"min\.", "minimal"),
    (r"gem\.", "gemäß"), (r"geb\.", "geboren"), (r"Jh\.", "Jahrhundert"), (r"Jhd\.", "Jahrhundert"),
    (r"Abs\.", "Absatz"), (r"Abb\.", "Abbildung"), (r"Kap\.", "Kapitel"), (r"S\.(?=\s*\d)", "Seite"),
]
_ABBR = [(re.compile(r"(?<![\wÄÖÜäöüß])" + p + r"(?=[\s,;:!?)]|$)"), w) for p, w in ABBREVIATIONS]

# Einheiten nach Zahlen: (Muster, Einzahl, Mehrzahl)
UNITS = [
    ("km/h", "Kilometer pro Stunde", None), ("°C", "Grad Celsius", None), ("°", "Grad", None),
    ("km²", "Quadratkilometer", None), ("m²", "Quadratmeter", None), ("m³", "Kubikmeter", None),
    ("km", "Kilometer", None), ("cm", "Zentimeter", None), ("mm", "Millimeter", None), ("m", "Meter", None),
    ("kg", "Kilogramm", None), ("g", "Gramm", None), ("t", "Tonnen", None),
    ("ml", "Milliliter", None), ("l", "Liter", None), ("h", "Stunden", None),
    ("kWh", "Kilowattstunden", None), ("kW", "Kilowatt", None), ("W", "Watt", None), ("V", "Volt", None),
    ("GB", "Gigabyte", None), ("MB", "Megabyte", None), ("TB", "Terabyte", None), ("GHz", "Gigahertz", None),
    ("MHz", "Megahertz", None), ("Hz", "Hertz", None),
    ("%", "Prozent", None), ("€", "Euro", None), ("EUR", "Euro", None), ("$", "Dollar", None), ("£", "Pfund", None),
]
_UNIT_RE = re.compile(r"(\d[\d.,]*)\s?(" + "|".join(re.escape(u[0]) for u in UNITS) + r")(?![\wÄÖÜäöüß])")
_UNIT_WORDS = {u[0]: u[1] for u in UNITS}
_CURRENCY_FRONT = {"€": "Euro", "$": "Dollar", "£": "Pfund"}

SYMBOLS = [("&", " und "), ("+", " plus "), ("=", " gleich "), ("§§", " Paragraphen "), ("§", " Paragraph "),
           ("@", " ät "), ("#", " Nummer "), ("~", " ungefähr ")]

# Nach diesen Wörtern steht die Ordnungszahl im Dativ ("am dritten Oktober")
_DATIVE = r"(?i:am|vom|zum|im|beim|seit dem|bis zum|ab dem|an dem|von dem|zu dem|dem|den)"


def _w(n: int | float, **kw) -> str:
    if _n2w is None:
        return str(n)
    try:
        return _n2w(n, lang="de", **kw)
    except Exception:
        return str(n)


def _ordinal(n: int, dative: bool) -> str:
    word = _w(n, to="ordinal")  # z. B. "dritte"
    return word + "n" if dative and word.endswith("e") else word


def _parse_number(s: str) -> int | float | None:
    """Deutsche Schreibweise: 1.234.567,89 -> 1234567.89; 3,5 -> 3.5"""
    s = s.strip(".,")
    if re.fullmatch(r"\d{1,3}(\.\d{3})+(,\d+)?", s):
        s = s.replace(".", "")
    elif re.fullmatch(r"\d+\.\d+", s):  # 3.5 (englische Schreibweise)
        return float(s)
    if "," in s:
        try:
            return float(s.replace(",", "."))
        except ValueError:
            return None
    return int(s) if s.isdigit() else None


def _number_words(s: str) -> str:
    n = _parse_number(s)
    if n is None:
        return s
    if isinstance(n, float):
        whole, frac = s.replace(".", "").split(",") if "," in s else s.split(".")
        return f"{_w(int(whole))} Komma {' '.join(_w(int(d)) for d in frac)}"
    return _w(n)


def _money(amount: str, unit: str) -> str:
    """3,50 € -> drei Euro fünfzig"""
    m = re.fullmatch(r"(\d[\d.]*)(?:,(\d{1,2}))?", amount.strip("."))
    if not m or unit not in ("Euro", "Dollar", "Pfund"):
        return f"{_number_words(amount)} {unit}"
    whole = int(m.group(1).replace(".", ""))
    cents = int((m.group(2) or "0").ljust(2, "0"))
    text = f"{_w(whole) if whole != 1 else 'ein'} {unit}"
    if cents:
        text += f" {_w(cents)}"
    return text


def normalize(text: str) -> str:
    """Schreibt Zahlen, Datumsangaben, Uhrzeiten, Einheiten und Abkürzungen aus."""
    t = text.replace(" ", " ").replace(" ", " ")
    t = re.sub(r"[„“”«»]", '"', t)

    for rx, word in _ABBR:
        # Satzende-Punkt erhalten ("… usw." am Satzende)
        t = rx.sub(lambda m, w=word: w + ("." if re.match(r"\s*(?:$|\n|[A-ZÄÖÜ]\w*\s)", t[m.end():]) and
                                            w in ("und so weiter", "und so fort", "et cetera", "und vieles mehr") else ""), t)

    # Datum 11.10.2026 / 11.10.
    def date(m):
        d, mo, y = int(m.group(2)), int(m.group(3)), m.group(4)
        if not (1 <= d <= 31 and 1 <= mo <= 12):
            return m.group(0)
        dative = bool(m.group(1))
        out = f"{m.group(1) or ''}{_ordinal(d, dative)} {MONTHS[mo - 1]}"
        if y:
            out += " " + _w(int(y if len(y) == 4 else "20" + y), to="year")
        return out
    t = re.sub(rf"(\b{_DATIVE}\s)?\b(\d{{1,2}})\.(\d{{1,2}})\.(\d{{4}}|\d{{2}}(?!\d))?", date, t)

    # 3. Oktober / am 3. Okt.
    def day_month(m):
        mon = m.group(3)
        full = next((x for x in MONTHS if x.lower().startswith(mon.lower()[:3])), mon)
        return f"{m.group(1) or ''}{_ordinal(int(m.group(2)), bool(m.group(1)))} {full}"
    t = re.sub(rf"(\b{_DATIVE}\s)?\b(\d{{1,2}})\.\s?({_MONTH_RE})\.?(?![\wäöü])", day_month, t)

    # Uhrzeit 15:30 Uhr / 9.05 Uhr / 15 Uhr
    def clock(m):
        h, mi = int(m.group(1)), int(m.group(2) or 0)
        if h > 24 or mi > 59:
            return m.group(0)
        return f"{_w(h) if h != 1 else 'ein'} Uhr" + (f" {_w(mi)}" if mi else "")
    t = re.sub(r"\b(\d{1,2})(?:[:.](\d{2}))?\s?Uhr\b", clock, t)
    t = re.sub(r"\b(\d{1,2}):(\d{2})\b", clock, t)

    # Jahreszahlen nach "im Jahr" / "Jahr" / allein stehend 1100-1999
    t = re.sub(r"\b(Jahr(?:e|es)?\s)(\d{4})\b", lambda m: m.group(1) + _w(int(m.group(2)), to="year"), t)
    t = re.sub(r"(?<![\d.,])\b(1[1-9]\d\d)\b(?![.,]\d)", lambda m: _w(int(m.group(1)), to="year"), t)

    # Währung vorne: € 5 / $ 20
    t = re.sub(r"([€$£])\s?(\d[\d.,]*)", lambda m: _money(m.group(2), _CURRENCY_FRONT[m.group(1)]), t)

    # Zahl + ausgeschriebene Währung: "3,50 Euro" -> "drei Euro fünfzig"
    t = re.sub(r"(\d[\d.]*,\d{1,2})\s(Euro|Dollar|Pfund)\b", lambda m: _money(m.group(1), m.group(2)), t)

    # Zahl + Einheit
    def unit(m):
        word = _UNIT_WORDS[m.group(2)]
        if word in ("Euro", "Dollar", "Pfund"):
            return _money(m.group(1), word)
        return f"{_number_words(m.group(1))} {word}"
    t = _UNIT_RE.sub(unit, t)

    # Ordnungszahlen vor Großbuchstaben-Wort: "der 2. Platz", "zum 5. Mal"
    t = re.sub(rf"(\b{_DATIVE}\s)?\b(\d{{1,3}})\.\s(?=[A-ZÄÖÜ][a-zäöüß])",
               lambda m: f"{m.group(1) or ''}{_ordinal(int(m.group(2)), bool(m.group(1)))} ", t)

    # Bereiche 10-20 / 10–20 -> zehn bis zwanzig
    t = re.sub(r"\b(\d+)\s?[–-]\s?(\d+)\b", lambda m: f"{_w(int(m.group(1)))} bis {_w(int(m.group(2)))}", t)

    # "1 Hund" -> "ein Hund" (vor einem Substantiv)
    t = re.sub(r"(?<![\w.,])1\s(?=[A-ZÄÖÜ][a-zäöüß])", "ein ", t)

    # Restliche Zahlen (mit Tausenderpunkten / Dezimalkomma)
    t = re.sub(r"(?<![\w])(\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+|\d+)(?![\w])", lambda m: _number_words(m.group(1)), t)

    for sym, word in SYMBOLS:
        t = t.replace(sym, word)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r" ([,.!?;:])", r"\1", t)
    return t.strip()


# Wörter, nach deren Punkt kein Satz endet (falls nicht normalisiert wird)
_NO_SPLIT = re.compile(
    r"(?:\b(?:z\.\s?B|d\.\s?h|u\.\s?a|bzw|ca|evtl|ggf|inkl|usw|vgl|etc|bspw|sog|Nr|Dr|Prof|Hr|Fr|St|Str|"
    r"Mio|Mrd|Tsd|Jh|Abs|Abb|Kap|S|[A-ZÄÖÜa-zäöü])|\b\d{1,3})\.$")


def split_sentences(text: str) -> list[str]:
    """Satzgrenzen erkennen, ohne an Abkürzungen oder Ordnungszahlen zu trennen."""
    parts = [p for p in re.split(r"(?<=[.!?;:…])\s+|\n+", text.strip()) if p.strip()]
    out: list[str] = []
    for p in parts:
        if out and _NO_SPLIT.search(out[-1]):
            out[-1] = f"{out[-1]} {p}"
        else:
            out.append(p.strip())
    return out
