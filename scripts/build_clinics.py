"""
Builds the clinic registry for MedServicePrice.kz seed data.

Real Kazakhstani clinic/lab brands across 6 cities. Each clinic has a `profile`
that controls which dictionary categories it offers, and a `price_factor` that
makes prices vary realistically between clinics/cities (premium vs budget).

Output: data/clinics.json

Run:  python scripts/build_clinics.py
"""
import json
import os

# City centres (lat, lng) used to scatter clinic markers for the map.
CITY_COORDS = {
    "Алматы": (43.2389, 76.8897),
    "Астана": (51.1605, 71.4704),
    "Шымкент": (42.3417, 69.5901),
    "Актобе": (50.2839, 57.1670),
    "Караганда": (49.8047, 73.1094),
    "Павлодар": (52.2873, 76.9674),
}

# profiles -> categories covered + how densely
PROFILES = {
    "lab": ["laboratory", "procedure"],
    "diagnostic": ["diagnostic", "laboratory", "procedure"],
    "multiprofile": ["doctor", "laboratory", "diagnostic", "procedure"],
}

# (name, source, city, address, phone, hours, website, profile, price_factor,
#  rating, online_booking, jitter_idx)
CLINICS = [
    # ---- KDL / Olymp lab network (source: kdl) ----
    ("KDL Olymp — Абая", "kdl", "Алматы", "пр. Абая, 109В", "+7 727 344 0066",
     "Пн–Сб 07:00–19:00, Вс 08:00–14:00", "https://www.kdlolymp.kz", "lab", 1.05, 4.6, True, 1),
    ("KDL Olymp — Достык", "kdl", "Астана", "пр. Достык, 5", "+7 7172 76 5050",
     "Пн–Сб 07:30–18:00, Вс 08:00–13:00", "https://www.kdlolymp.kz", "lab", 1.08, 4.5, True, 2),
    ("KDL Olymp — Тауке хана", "kdl", "Шымкент", "пр. Тауке хана, 80", "+7 7252 99 1010",
     "Пн–Сб 07:30–18:00", "https://www.kdlolymp.kz", "lab", 0.92, 4.4, True, 3),
    ("KDL Olymp — Бокенбай", "kdl", "Актобе", "ул. Братьев Жубановых, 289", "+7 7132 70 2020",
     "Пн–Сб 08:00–17:00", "https://www.kdlolymp.kz", "lab", 0.90, 4.3, True, 4),

    # ---- INVITRO (source: invitro) ----
    ("Invitro — Сатпаева", "invitro", "Алматы", "ул. Сатпаева, 90/22", "+7 727 312 1212",
     "Пн–Пт 07:00–19:00, Сб–Вс 08:00–15:00", "https://invitro.kz", "lab", 1.12, 4.5, True, 5),
    ("Invitro — Кабанбай батыра", "invitro", "Астана", "ул. Кабанбай батыра, 42", "+7 7172 73 1414",
     "Пн–Пт 07:00–19:00, Сб 08:00–14:00", "https://invitro.kz", "lab", 1.15, 4.4, True, 6),
    ("Invitro — Республики", "invitro", "Караганда", "пр. Республики, 32", "+7 7212 41 1616",
     "Пн–Сб 07:30–18:00", "https://invitro.kz", "lab", 0.98, 4.3, True, 7),

    # ---- Helix (source: helix) ----
    ("Helix — Розыбакиева", "helix", "Алматы", "ул. Розыбакиева, 247А", "+7 727 351 8080",
     "Пн–Сб 07:30–18:30, Вс 09:00–14:00", "https://helix.kz", "lab", 1.00, 4.4, True, 8),
    ("Helix — Туран", "helix", "Астана", "пр. Туран, 37", "+7 7172 64 8080",
     "Пн–Сб 07:30–18:00", "https://helix.kz", "lab", 1.03, 4.3, True, 9),
    ("Helix — Назарбаева", "helix", "Павлодар", "ул. Кутузова, 204", "+7 7182 55 8080",
     "Пн–Сб 08:00–17:00", "https://helix.kz", "lab", 0.93, 4.2, False, 10),

    # ---- Olymp medcenter (source: olymp) ----
    ("Медцентр Olymp — Гагарина", "olymp", "Алматы", "пр. Гагарина, 177Б", "+7 727 390 4040",
     "Пн–Сб 08:00–20:00", "https://olymp.kz", "diagnostic", 1.06, 4.5, True, 11),
    ("Медцентр Olymp — Сарыарка", "olymp", "Астана", "пр. Сарыарка, 31", "+7 7172 57 4040",
     "Пн–Сб 08:00–19:00", "https://olymp.kz", "diagnostic", 1.09, 4.4, True, 12),

    # ---- MEDEL multiprofile (source: medel) ----
    ("МЕДЭЛ — Клиника на Жандосова", "medel", "Алматы", "ул. Жандосова, 98", "+7 727 258 2525",
     "Пн–Сб 08:00–20:00, Вс 09:00–15:00", "https://medel.kz", "multiprofile", 1.10, 4.6, True, 13),
    ("МЕДЭЛ — Филиал Тимирязева", "medel", "Алматы", "ул. Тимирязева, 42", "+7 727 258 2526",
     "Пн–Сб 08:00–19:00", "https://medel.kz", "multiprofile", 1.07, 4.5, True, 14),

    # ---- MCK medical center (source: mck) ----
    ("Медицинский центр МЦК", "mck", "Шымкент", "ул. Байтурсынова, 25", "+7 7252 53 3030",
     "Пн–Сб 08:00–18:00", "https://mck.kz", "multiprofile", 0.94, 4.3, True, 15),
    ("МЦК — Филиал Север", "mck", "Шымкент", "мкр. Север, 18", "+7 7252 53 3031",
     "Пн–Сб 08:00–17:00", "https://mck.kz", "multiprofile", 0.91, 4.1, False, 16),

    # ---- Aksai regional clinic (source: aksai) ----
    ("Аксай — Областная клиника", "aksai", "Актобе", "пр. Абилкайыр хана, 40", "+7 7132 56 1717",
     "Пн–Сб 08:00–18:00", "https://aksai-clinic.kz", "multiprofile", 0.88, 4.2, False, 17),
    ("Аксай — Городская поликлиника", "aksai", "Караганда", "ул. Ерубаева, 54", "+7 7212 42 1818",
     "Пн–Пт 08:00–17:00, Сб 09:00–14:00", "https://aksai-clinic.kz", "multiprofile", 0.86, 4.0, False, 18),
    ("Аксай — Медцентр Павлодар", "aksai", "Павлодар", "ул. Лермонтова, 96", "+7 7182 60 1919",
     "Пн–Сб 08:00–17:00", "https://aksai-clinic.kz", "multiprofile", 0.85, 4.1, False, 19),
]


def jitter(base, idx, scale=0.045):
    """Deterministic small offset so markers don't overlap on the map."""
    lat0, lng0 = base
    # simple deterministic spread based on index
    dlat = ((idx * 37) % 100 - 50) / 100.0 * scale
    dlng = ((idx * 53) % 100 - 50) / 100.0 * scale
    return round(lat0 + dlat, 6), round(lng0 + dlng, 6)


def build():
    out = []
    for (name, source, city, address, phone, hours, website,
         profile, factor, rating, booking, jidx) in CLINICS:
        lat, lng = jitter(CITY_COORDS[city], jidx)
        out.append({
            "name": name,
            "source": source,
            "city": city,
            "address": address,
            "phone": phone,
            "working_hours": hours,
            "website": website,
            "profile": profile,
            "categories": PROFILES[profile],
            "price_factor": factor,
            "rating": rating,
            "has_online_booking": booking,
            "lat": lat,
            "lng": lng,
        })
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "data", "clinics.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    cities = sorted({c["city"] for c in out})
    sources = sorted({c["source"] for c in out})
    print(f"Wrote {len(out)} clinics to {path}")
    print(f"Cities ({len(cities)}):", ", ".join(cities))
    print(f"Sources ({len(sources)}):", ", ".join(sources))


if __name__ == "__main__":
    build()
