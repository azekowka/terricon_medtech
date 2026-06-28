"""Concrete live sources for real KZ clinic/lab sites listed in the TZ (§2.1).

All are JS-heavy, so render=True (Playwright with httpx fallback). Catalogue paths
are best-effort; the generic scraper tries each until one yields prices.
"""
from __future__ import annotations

from ._generic import GenericLiveParser


class KdlParser(GenericLiveParser):
    source = "kdl"
    base_url = "https://www.kdlolymp.kz"
    catalog_paths = ["/analizy-i-tseny", "/analizy", "/catalog", "/price", "/"]
    clinic_name = "KDL Olymp (онлайн-прайс)"
    city = "Алматы"
    render = True


class InvitroParser(GenericLiveParser):
    source = "invitro"
    base_url = "https://invitro.kz"
    catalog_paths = ["/analizes/for-doctors/", "/analizes/", "/price/", "/"]
    clinic_name = "INVITRO (онлайн-прайс)"
    city = "Алматы"
    render = True


class HelixParser(GenericLiveParser):
    source = "helix"
    base_url = "https://helix.kz"
    catalog_paths = ["/catalog/", "/price/", "/analizy/", "/"]
    clinic_name = "Helix (онлайн-прайс)"
    city = "Алматы"
    render = True


class OlympParser(GenericLiveParser):
    source = "olymp"
    base_url = "https://www.olymp.kz"
    catalog_paths = ["/analizy-i-tseny", "/uslugi", "/price", "/catalog", "/"]
    clinic_name = "Медцентр Олимп (онлайн-прайс)"
    city = "Алматы"
    render = True


class MedelParser(GenericLiveParser):
    source = "medel"
    base_url = "https://medel.kz"
    catalog_paths = ["/price", "/uslugi", "/ceny", "/services", "/"]
    clinic_name = "МЕДЭЛ (онлайн-прайс)"
    city = "Алматы"
    render = True


class MckParser(GenericLiveParser):
    source = "mck"
    base_url = "https://mck.kz"
    catalog_paths = ["/price", "/uslugi-i-ceny", "/uslugi", "/services", "/"]
    clinic_name = "Медицинский центр МЦК (онлайн)"
    city = "Шымкент"
    render = True


class AksaiParser(GenericLiveParser):
    source = "aksai"
    base_url = "https://aksai-clinic.kz"
    catalog_paths = ["/price", "/uslugi", "/ceny", "/prajs", "/"]
    clinic_name = "Аксай (онлайн-прайс)"
    city = "Алматы"
    render = True


class DoqParser(GenericLiveParser):
    source = "doq"
    base_url = "https://doq.kz"
    catalog_paths = ["/almaty/services", "/services", "/uslugi", "/price", "/"]
    clinic_name = "doq.kz (агрегатор клиник)"
    city = "Алматы"
    render = True


LIVE_PARSERS = [
    KdlParser, InvitroParser, HelixParser, OlympParser,
    MedelParser, MckParser, AksaiParser, DoqParser,
]
