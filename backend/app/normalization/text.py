"""Text normalization helpers for matching raw service names to the dictionary."""
import re

# Common noise tokens that clinics append to service names and that do not help
# identify the canonical service. Note "ё" is folded to "е" before this runs.
_NOISE = [
    "стоимость", "цена", "услуга", "анализ крови на", "исследование",
    "лабораторное", "взятие биоматериала", "без стоимости взятия",
    "1 показатель", "колич.", "кол-во", "качественный", "количественный",
    "сыворотка", "венозная кровь", "(сыворотка)", "руб", "тенге", "тг",
    # "doctor visit" wrappers — strip so visits cluster by SPECIALTY, not by the
    # shared "приём врача" prefix (the specialty is the identifying token).
    "первичныи прием", "повторныи прием", "прием врача", "консультация врача",
    "прием", "консультация", "консультации", "осмотр врача", "врача",
]

# Leading tariff / catalogue codes real price lists put before the name,
# e.g. "A01.1 ", "B03.304.002 ", "123. ", "1.2.3 ".
_LEADING_CODE_RE = re.compile(r"^\s*[a-zа-я]?\d[\d.\-/]*\.?\s+", re.UNICODE)
_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+", re.UNICODE)


def normalize_text(value: str) -> str:
    """Lower-case, de-noise and collapse a raw service string.

    Used both to build the dictionary (clustering) and to canonicalize incoming
    raw names for matching, so the two are compared on equal footing.
    """
    if not value:
        return ""
    text = value.strip().lower()
    text = text.replace("ё", "е")  # ё -> е
    text = text.replace("\xa0", " ")
    text = _LEADING_CODE_RE.sub("", text)
    text = _PUNCT_RE.sub(" ", text)
    for noise in _NOISE:
        text = text.replace(noise, " ")
    text = _SPACE_RE.sub(" ", text).strip()
    return text
