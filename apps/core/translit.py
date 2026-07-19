"""O‘zbek lotin -> kirill transliteratsiyasi.

Butun HTML sahifa matnini (faqat matn tugunlarini) o‘giradi: teglar,
atributlar, <script>/<style> bloklari va HTML-entitylar tegilmaydi.
"""
import re

# Apostrof (tutuq belgisi) va o‘/g‘ dagi belgi variantlari — bittaga keltiramiz
_APOS = "ʻʼ‘’`´'"

# Ko‘p harfli (digraf) mosliklar — birinchi qo‘llanadi. Registr saqlanadi.
_DIGRAPHS = [
    ('oʻ', 'ў'), ('gʻ', 'ғ'),
    ('sh', 'ш'), ('ch', 'ч'),
    ('yo', 'ё'), ('yu', 'ю'), ('ya', 'я'), ('ye', 'е'),
    ('ts', 'ц'),
]

# Bir harfli mosliklar
_SINGLE = {
    'a': 'а', 'b': 'б', 'd': 'д', 'e': 'е', 'f': 'ф', 'g': 'г',
    'h': 'ҳ', 'i': 'и', 'j': 'ж', 'k': 'к', 'l': 'л', 'm': 'м',
    'n': 'н', 'o': 'о', 'p': 'п', 'q': 'қ', 'r': 'р', 's': 'с',
    't': 'т', 'u': 'у', 'v': 'в', 'x': 'х', 'y': 'й', 'z': 'з',
    'c': 'ц',
}


def _cap(cyr):
    """Kirill harfini bosh harfga aylantiradi (digraf uchun faqat 1-harf)."""
    return cyr[0].upper() + cyr[1:]


def _apply_cased(text, lat, cyr):
    """`lat` (lotin) ni uchta registr ko‘rinishida `cyr` ga almashtiradi."""
    text = text.replace(lat.upper(), cyr.upper())          # HAMMASI KATTA
    text = text.replace(lat.capitalize(), _cap(cyr))       # Bosh harf
    text = text.replace(lat, cyr)                          # kichik
    return text


def to_cyrillic(text):
    if not text:
        return text

    # apostrof variantlarini bittaga keltiramiz
    for ch in _APOS:
        text = text.replace(ch, "'")

    # o' / g' -> ў / ғ  (digrafdan oldin apostrofli shakl)
    text = _apply_cased(text, "o'", 'ў')
    text = _apply_cased(text, "g'", 'ғ')

    # qolgan digraflar
    for lat, cyr in _DIGRAPHS:
        text = _apply_cased(text, lat, cyr)

    # so‘z boshidagi e -> э (aks holda quyida е bo‘ladi)
    text = re.sub(r'\bE', 'Э', text)
    text = re.sub(r'\be', 'э', text)

    # qolgan tutuq belgisi -> ъ
    text = text.replace("'", 'ъ')

    # bir harflilar
    out = []
    for ch in text:
        low = ch.lower()
        if low in _SINGLE:
            cyr = _SINGLE[low]
            out.append(cyr.upper() if ch.isupper() else cyr)
        else:
            out.append(ch)
    return ''.join(out)


# Teg / script / style / entity — bularga tegmaymiz, oralaridagi matngina o‘giriladi
_SKIP = re.compile(
    r'(<script[^>]*>.*?</script>'
    r'|<style[^>]*>.*?</style>'
    r'|<[^>]+>'
    r'|&[#a-zA-Z0-9]+;)',
    re.S | re.I,
)


def html_to_cyrillic(html):
    parts = _SKIP.split(html)
    # re.split (guruh bilan) natijasi: matn, ajratuvchi, matn, ajratuvchi, ...
    for i in range(0, len(parts), 2):
        parts[i] = to_cyrillic(parts[i])
    return ''.join(parts)
