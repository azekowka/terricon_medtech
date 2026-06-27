"use client";

import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";

const MAPBOX_TOKEN = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
const STYLE_URL = MAPBOX_TOKEN
  ? `https://api.mapbox.com/styles/v1/mapbox/light-v11?access_token=${MAPBOX_TOKEN}`
  : "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json";

export function ClinicMiniMap({ lat, lng, name }: { lat: number; lng: number; name: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!ref.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: ref.current,
      style: STYLE_URL as any,
      center: [lng, lat],
      zoom: 13,
      attributionControl: false,
    });
    mapRef.current = map;
    const el = document.createElement("div");
    el.style.cssText =
      "width:18px;height:18px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);" +
      "background:#2563eb;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.3)";
    new maplibregl.Marker({ element: el, anchor: "bottom" }).setLngLat([lng, lat]).addTo(map);
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, [lat, lng]);

  return <div ref={ref} className="h-56 w-full overflow-hidden rounded-2xl" title={name} />;
}
