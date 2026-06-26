"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import type { ClinicListItem, Meta } from "@/lib/types";

const ClinicsMap = dynamic(() => import("@/components/ClinicsMap"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-slate-100" />,
});

const CITY_CENTERS: Record<string, [number, number]> = {
  Алматы: [43.238, 76.889],
  Астана: [51.16, 71.47],
  Шымкент: [42.34, 69.59],
  Актобе: [50.28, 57.17],
  Караганда: [49.8, 73.11],
  Павлодар: [52.29, 76.97],
};

export default function MapPage() {
  const [clinics, setClinics] = useState<ClinicListItem[]>([]);
  const [meta, setMeta] = useState<Meta | null>(null);
  const [city, setCity] = useState("");

  useEffect(() => {
    api.meta().then(setMeta).catch(() => {});
  }, []);

  useEffect(() => {
    api.clinics(city ? { city } : undefined).then(setClinics).catch(() => setClinics([]));
  }, [city]);

  const center: [number, number] = useMemo(
    () => (city && CITY_CENTERS[city] ? CITY_CENTERS[city] : [48.0, 68.0]),
    [city],
  );

  return (
    <div className="container-page pt-6">
      <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-extrabold text-ink">Клиники на карте</h1>
          <p className="text-sm text-slate-500">{clinics.length} клиник · нажмите на маркер для подробностей</p>
        </div>
        <select className="input sm:w-56" value={city} onChange={(e) => setCity(e.target.value)}>
          <option value="">Весь Казахстан</option>
          {meta?.cities.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>
      <div className="card h-[70vh] overflow-hidden p-0">
        {/* key forces a remount so react-leaflet re-centers on city change */}
        <ClinicsMap key={city || "all"} clinics={clinics} center={center} />
      </div>
    </div>
  );
}
