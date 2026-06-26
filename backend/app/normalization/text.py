"""Text normalization helpers for matching raw service names to the dictionary."""
import re

# Common noise tokens that clinics append to service names and that do not help
# identify the canonical service.
_NOISE = [
    "стоимость", "цена", "услуга", "анализ крови на", "исследование",
    "лабораторное", "взятие биоматериала", "без стоимости взятия",
    "1 показатель", "колич.", "кол-во", "качественный", "количественный",
    "сыворотка", "венозная кровь", "(сыворотка)", "руб", "тенге", "тг",
]

_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_SPACE_RE = re.compile(r"\s+", re.UNICODE)


def normalize_text(value: str) -> str:
    """Lower-case, de-noise and collapse a raw service string.

    Used both to build the synonym index and to canonicalize incoming raw names,
    so the two are compared on equal footing.
    """
    if not value:
        return ""
    text = value.strip().lower()
    text = text.replace("ё", "е")
    # unify latin look-alikes occasionally used in Russian medical names
    text = text.replace(" ", " ")
    text = _PUNCT_RE.sub(" ", text)
    for noise in _NOISE:
        text = text.replace(noise, " ")
    text = _SPACE_RE.sub(" ", text).strip()
    return text
