"use client";

import dynamic from "next/dynamic";
import { useMemo } from "react";

const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const Marker = dynamic(() => import("react-leaflet").then((m) => m.Marker), { ssr: false });

export function ClinicMiniMap({ lat, lng, name }: { lat: number; lng: number; name: string }) {
  const icon = useMemo(() => {
    if (typeof window === "undefined") return undefined;
    const L = require("leaflet");
    return L.divIcon({
      className: "",
      html: `<div style="background:#2563eb;width:18px;height:18px;border-radius:50% 50% 50% 0;transform:rotate(-45deg);border:3px solid white;box-shadow:0 2px 6px rgba(0,0,0,.3)"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 18],
    });
  }, []);

  return (
    <div className="h-56 w-full overflow-hidden rounded-2xl">
      <MapContainer center={[lat, lng]} zoom={14} scrollWheelZoom={false} style={{ height: "100%", width: "100%" }}>
        <TileLayer
          attribution='&copy; OpenStreetMap'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {icon && <Marker position={[lat, lng]} icon={icon} />}
      </MapContainer>
    </div>
  );
}
