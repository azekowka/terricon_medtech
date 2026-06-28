"use client";

import { useState } from "react";
import { MapPin, Search, X } from "lucide-react";
import type { DoctorRegion } from "@/lib/types";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function RegionPopup({
  regions,
  current,
  onSelect,
  onClose,
}: {
  regions: DoctorRegion[];
  current: string | null;
  onSelect: (slug: string) => void;
  onClose: () => void;
}) {
  const { t } = useI18n();
  const [q, setQ] = useState("");
  const filtered = regions.filter((r) => r.name.toLowerCase().includes(q.trim().toLowerCase()));
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-ink/40 p-4 pt-20" onClick={onClose}>
      <div className="card w-full max-w-2xl p-6 shadow-pop" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2.5 text-xl font-bold tracking-tight text-ink">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
              <MapPin size={18} strokeWidth={1.75} />
            </span>
            {t("doctors.selectCity")}
          </h2>
          <button
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-xl text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>
        <div className="relative mt-4">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder={t("doctors.searchCity")}
            className="input pl-10"
          />
        </div>
        <div className="mt-4 grid max-h-[55vh] grid-cols-2 gap-2 overflow-y-auto sm:grid-cols-3">
          {filtered.map((r) => (
            <button
              key={r.slug}
              onClick={() => onSelect(r.slug)}
              className={`flex items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm transition ${
                current === r.slug ? "bg-brand-50 font-semibold text-brand-700" : "hover:bg-slate-100 text-slate-700"
              }`}
            >
              <span>{r.name}</span>
              <span className="text-xs text-slate-400">{r.count}</span>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="col-span-full py-6 text-center text-sm text-slate-400">{t("doctors.cityNotFound")}</p>
          )}
        </div>
      </div>
    </div>
  );
}
