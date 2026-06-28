"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { X } from "lucide-react";
import { api } from "@/lib/api";
import type { MapCity } from "@/components/CityPriceMap";
import type { ClinicListItem } from "@/lib/types";
import { CitySelect } from "@/components/CitySelect";
import { useI18n } from "@/lib/i18n/I18nProvider";

const CityPriceMap = dynamic(() => import("@/components/CityPriceMap"), {
  ssr: false,
  loading: () => <div className="h-full w-full animate-pulse bg-slate-100" />,
});

export default function MapPage() {
  const { t } = useI18n();
  const [cities, setCities] = useState<MapCity[]>([]);
  const [clinics, setClinics] = useState<ClinicListItem[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api.mapCities().then((d) => setCities(d.cities as MapCity[])).catch(() => setCities([]));
    api.clinics().then(setClinics).catch(() => setClinics([]));
  }, []);

  const cheapest = cities.length ? Math.min(...cities.map((c) => c.min_price)) : 0;
  const cheapestCity = cities.find((c) => c.min_price === cheapest);
  const selCity = cities.find((c) => c.slug === selected);
  const clinicsInSel = useMemo(
    () => (selCity ? clinics.filter((c) => c.city === selCity.name).length : clinics.length),
    [clinics, selCity],
  );
  // clinic counts per city for the selector (matches the clinic dots on the map)
  const cityOptions = useMemo(() => {
    const byCity = new Map<string, number>();
    for (const c of clinics) byCity.set(c.city, (byCity.get(c.city) || 0) + 1);
    return cities.map((c) => ({ value: c.slug, label: c.name, count: byCity.get(c.name) }));
  }, [cities, clinics]);

  return (
    <div className="container-page pt-6">
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-ink">{t("map.title")}</h1>
          <p className="mt-1 text-sm text-slate-500">
            {selCity
              ? `${selCity.name} · ${clinicsInSel} ${t("home.clinicsCount")}`
              : t("map.subtitle")}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {!selCity && cheapestCity && (
            <div className="hidden items-center rounded-full bg-teal-50 px-3.5 py-2 text-sm text-teal-700 sm:flex">
              <span className="text-teal-600/80">{t("map.cheapestIn")}&nbsp;</span>
              <b className="font-semibold">{cheapestCity.name}</b>
              <span className="text-teal-600/80">&nbsp;·&nbsp;{t("common.from")}&nbsp;</span>
              <b className="font-semibold">{new Intl.NumberFormat("ru-RU").format(cheapest)} ₸</b>
            </div>
          )}
          <CitySelect
            className="w-full sm:w-56"
            value={selected || ""}
            onChange={(v) => setSelected(v || null)}
            allLabel={t("search.allCities")}
            options={cityOptions}
          />
          {selCity && (
            <button onClick={() => setSelected(null)} className="btn-outline px-2.5 py-2" title={t("search.allCities")}>
              <X size={16} />
            </button>
          )}
        </div>
      </div>
      <div className="card relative h-[72vh] overflow-hidden p-0">
        <CityPriceMap cities={cities} clinics={clinics} selected={selected} onSelect={(s) => setSelected(s)} />
      </div>
      <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-xs text-slate-500">
        <span className="inline-flex items-center gap-2">
          <span className="inline-flex items-center rounded-md border border-slate-200 bg-white px-1.5 py-0.5 text-[10px] font-semibold text-ink shadow-sm">{t("common.from")} ₸</span>
          {t("map.bubbleHint")}
        </span>
        <span className="inline-flex items-center gap-2">
          <span className="inline-block h-3 w-3 rounded-full border-2 border-white bg-brand-600 shadow-sm" />
          {t("map.clinicHint")}
        </span>
      </div>
    </div>
  );
}
