"use client";

import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { useI18n } from "@/lib/i18n/I18nProvider";
import type { ClinicListItem } from "@/lib/types";

export interface MapCity {
  slug: string;
  name: string;
  lat: number;
  lng: number;
  min_price: number;
  doctors: number;
}

// Open-source Mapbox GL engine (MapLibre) with a free, token-free vector style.
// To use real Mapbox tiles, set NEXT_PUBLIC_MAPBOX_TOKEN and swap the style URL.
const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const STYLE_URL = MAPBOX_TOKEN
  ? `https://api.mapbox.com/styles/v1/mapbox/light-v11?access_token=${MAPBOX_TOKEN}`
  : "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

function fmt(n: number) {
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(n);
}
function esc(s: string) {
  return (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]!));
}

export default function CityPriceMap({
  cities,
  clinics,
  selected,
  onSelect,
}: {
  cities: MapCity[];
  clinics: ClinicListItem[];
  selected: string | null;
  onSelect: (slug: string) => void;
}) {
  const { t } = useI18n();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const cityMarkers = useRef<maplibregl.Marker[]>([]);
  const clinicMarkers = useRef<maplibregl.Marker[]>([]);
  const [ready, setReady] = useState(false);

  // init the map once
  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL as any,
      center: [68.0, 48.2],
      zoom: 4.2,
      attributionControl: false,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    map.addControl(new maplibregl.AttributionControl({ compact: true }));
    map.on("error", (e: any) => {
      // basemap tile/style hiccups shouldn't break the marker overlay
      console.warn("map error", e?.error?.message || e);
    });
    const onLoad = () => {
      setReady(true);
      map.resize();
    };
    if (map.isStyleLoaded()) onLoad();
    else map.on("load", onLoad);
    // robustness: markers are HTML overlays and don't need tiles — ensure they
    // render even if the basemap style 'load' event is flaky/blocked.
    const fallback = setTimeout(() => setReady(true), 1500);
    return () => {
      clearTimeout(fallback);
      setReady(false);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // city price bubbles
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    cityMarkers.current.forEach((m) => m.remove());
    cityMarkers.current = [];
    if (cities.length === 0) return;
    const cheapest = Math.min(...cities.map((c) => c.min_price));
    const from = t("common.from");
    for (const c of cities) {
      const el = document.createElement("div");
      el.className =
        "price-bubble" + (c.min_price === cheapest ? " pb-best" : "") + (selected === c.slug ? " pb-active" : "");
      el.innerHTML = `<div class="pb-name">${esc(c.name)}</div><div class="pb-price">${from} ${fmt(c.min_price)} ₸</div>`;
      el.addEventListener("click", (e) => {
        e.stopPropagation();
        onSelect(c.slug);
      });
      cityMarkers.current.push(new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat([c.lng, c.lat]).addTo(map));
    }
  }, [ready, cities, selected, onSelect, t]);

  // clinic markers (filtered to the selected city, else all)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready) return;
    clinicMarkers.current.forEach((m) => m.remove());
    clinicMarkers.current = [];
    const selName = selected ? cities.find((c) => c.slug === selected)?.name : null;
    const shown = clinics.filter((c) => c.lat != null && c.lng != null && (!selName || c.city === selName));
    for (const c of shown) {
      const el = document.createElement("div");
      el.className = "clinic-dot";
      const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(
        `<div class="clinic-pop"><a href="/clinics/${c.id}" class="cp-name">${esc(c.name)}</a>` +
          `<div class="cp-meta">${esc(c.city)}, ${esc(c.address || "")}</div>` +
          (c.working_hours ? `<div class="cp-meta">${esc(c.working_hours)}</div>` : "") +
          `<div class="cp-meta">${c.services_count} ${t("home.services")}${c.rating ? ` · ★ ${c.rating.toFixed(1)}` : ""}</div>` +
          `<a href="/clinics/${c.id}" class="cp-link">${t("common.toSite")} →</a></div>`,
      );
      clinicMarkers.current.push(
        new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([c.lng!, c.lat!]).setPopup(popup).addTo(map),
      );
    }
  }, [ready, clinics, selected, cities, t]);

  // camera: zoom to selected city, else fit all cities
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !ready || cities.length === 0) return;
    if (selected) {
      const c = cities.find((x) => x.slug === selected);
      if (c) map.flyTo({ center: [c.lng, c.lat], zoom: 10.5, duration: 800 });
    } else {
      const b = new maplibregl.LngLatBounds();
      cities.forEach((c) => b.extend([c.lng, c.lat]));
      if (!b.isEmpty()) map.fitBounds(b, { padding: 70, maxZoom: 6.5, duration: 600 });
    }
  }, [ready, selected, cities]);

  return <div ref={containerRef} className="h-full w-full" />;
}
