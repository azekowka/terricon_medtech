"use client";

import { MapContainer, Marker, Popup, TileLayer } from "react-leaflet";
import L from "leaflet";
import Link from "next/link";
import type { ClinicListItem } from "@/lib/types";

function pin(color: string) {
  return L.divIcon({
    className: "",
    html: `<div style="background:${color};width:20px;height:20px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,.35)"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 20],
    popupAnchor: [0, -18],
  });
}

const SOURCE_COLORS: Record<string, string> = {
  kdl: "#2563eb",
  invitro: "#0d9488",
  helix: "#db2777",
  olymp: "#f59e0b",
  medel: "#7c3aed",
  mck: "#0891b2",
  aksai: "#65a30d",
  seed: "#2563eb",
};

export default function ClinicsMap({
  clinics,
  center,
}: {
  clinics: ClinicListItem[];
  center: [number, number];
}) {
  const withCoords = clinics.filter((c) => c.lat != null && c.lng != null);
  return (
    <MapContainer center={center} zoom={5} scrollWheelZoom style={{ height: "100%", width: "100%" }}>
      <TileLayer attribution="&copy; OpenStreetMap" url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      {withCoords.map((c) => (
        <Marker key={c.id} position={[c.lat!, c.lng!]} icon={pin(SOURCE_COLORS[c.source] || "#2563eb")}>
          <Popup>
            <div className="space-y-1">
              <Link href={`/clinics/${c.id}`} className="font-bold text-brand-700">
                {c.name}
              </Link>
              <div className="text-xs text-slate-500">
                {c.city}, {c.address}
              </div>
              <div className="text-xs text-slate-500">{c.working_hours}</div>
              <div className="text-xs font-medium text-slate-700">
                {c.services_count} услуг{c.rating ? ` · ★ ${c.rating.toFixed(1)}` : ""}
              </div>
              <Link href={`/clinics/${c.id}`} className="text-xs font-semibold text-brand-600">
                Открыть карточку →
              </Link>
            </div>
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
}
