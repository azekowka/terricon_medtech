"use client";

import { useState } from "react";
import { MapPin, Search, X } from "lucide-react";
import type { DoctorRegion } from "@/lib/types";

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
  const [q, setQ] = useState("");
  const filtered = regions.filter((r) => r.name.toLowerCase().includes(q.trim().toLowerCase()));
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-ink/40 p-4 pt-20" onClick={onClose}>
      <div className="card w-full max-w-2xl p-6" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-xl font-bold text-ink">
            <MapPin className="text-brand-600" size={22} /> Выберите город
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-700">
            <X size={22} />
          </button>
        </div>
        <div className="relative mt-4">
          <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
          <input
            autoFocus
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Поиск города…"
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
            <p className="col-span-full py-6 text-center text-sm text-slate-400">Город не найден</p>
          )}
        </div>
      </div>
    </div>
  );
}
